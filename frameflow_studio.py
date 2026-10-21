import os, sys, json, shutil, subprocess, threading, time, urllib.request, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "FrameFlow Studio"
VERSION = "0.4.0"

def app_dir():
    # PyInstaller --onefile extracts __file__ into a temporary folder;
    # bundled tools live beside the executable instead.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def find_ffmpeg():
    p = shutil.which("ffmpeg")
    if p: return p
    candidates = [
        app_dir() / "tools" / "ffmpeg.exe",
        Path(__file__).parent / "tools" / "ffmpeg.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
    ]
    return next((str(x) for x in candidates if x.exists()), None)

def find_ffprobe(ffmpeg):
    candidates = [
        app_dir() / "tools" / "ffprobe.exe",
        Path(ffmpeg).with_name("ffprobe.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ffmpeg" / "bin" / "ffprobe.exe",
        Path("C:/ffmpeg/bin/ffprobe.exe"),
    ]
    found = next((str(x) for x in candidates if x.exists()), None)
    return found or shutil.which("ffprobe") or "ffprobe"

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")

def probe(ffmpeg, path):
    p = run([find_ffprobe(ffmpeg),
             "-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)])
    if p.returncode != 0:
        # use ffmpeg stderr fallback only to provide a clear error
        raise RuntimeError("تعذر قراءة مدة الملف: " + Path(path).name)
    try: return float(p.stdout.strip())
    except: raise RuntimeError("مدة الفيديو غير معروفة: " + Path(path).name)

def detect_scenes(path, duration, cap_scenes=250):
    try:
        import cv2
        import numpy as np
    except Exception:
        # Fallback: regular segments, clearly noted in the UI log
        count = max(1, min(cap_scenes, int(duration // 5)))
        return [(i*duration/count, (i+1)*duration/count, 0.0) for i in range(count)], False
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened(): return [(0, duration, 0.0)], True
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or duration*fps
    # sample about twice per second; compare grayscale thumbnails
    step = max(1, int(fps * 0.5))
    points, prev = [], None
    idx = 0
    while idx < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok: break
        small = cv2.resize(frame, (160, 90))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        score = 0.0 if prev is None else float(np.mean(cv2.absdiff(gray, prev)))
        points.append((idx/fps, score, sharp))
        prev = gray
        idx += step
    cap.release()
    cuts = [0.0]
    for t, score, sharp in points[1:]:
        if score >= 22 and t - cuts[-1] >= 1.5:
            cuts.append(t)
    cuts.append(duration)
    cuts = sorted(set(max(0.0, min(duration, x)) for x in cuts))
    scenes = []
    for a,b in zip(cuts, cuts[1:]):
        if b-a >= 0.8:
            # average sharpness of samples within this interval
            vals = [q[2] for q in points if a <= q[0] < b]
            sharp = sum(vals)/len(vals) if vals else 0.0
            scenes.append((a,b,sharp))
    return scenes or [(0.0,duration,0.0)], True

class App:
    def __init__(self, root):
        self.root=root; root.title("FrameFlow Studio"); root.geometry("900x680"); root.minsize(760,580)
        root.configure(bg="#f3f8fc")
        self.media=[]; self.music=""; self.busy=False
        style=ttk.Style(); style.theme_use("clam")
        style.configure("TFrame", background="#f3f8fc")
        style.configure("TLabel", background="#f3f8fc", foreground="#16324f", font=("Segoe UI",10))
        style.configure("Title.TLabel", font=("Segoe UI",20,"bold"), foreground="#087eae")
        style.configure("TButton", font=("Segoe UI",10), padding=7)
        style.configure("Accent.TButton", background="#087eae", foreground="white")
        top=ttk.Frame(root,padding=16); top.pack(fill="x")
        ttk.Label(top,text="FrameFlow Studio",style="Title.TLabel").pack(anchor="w")
        ttk.Label(top,text=f"مونتاج محلي لويندوز 11 • الإصدار {VERSION}").pack(anchor="w",pady=(3,0))
        body=ttk.Frame(root,padding=(16,0,16,16)); body.pack(fill="both",expand=True)
        bar=ttk.Frame(body); bar.pack(fill="x",pady=8)
        ttk.Button(bar,text="إضافة فيديوهات",command=self.add_media).pack(side="left")
        ttk.Button(bar,text="إزالة المحدد",command=self.remove_selected).pack(side="left",padx=6)
        ttk.Button(bar,text="اختيار موسيقى",command=self.pick_music).pack(side="left")
        ttk.Button(bar,text="حفظ مشروع",command=self.save_project).pack(side="left",padx=6)
        ttk.Button(bar,text="فتح مشروع",command=self.load_project).pack(side="left")
        ttk.Button(bar,text="فحص التحديثات",command=self.check_updates).pack(side="right")
        self.list=tk.Listbox(body,height=8,selectmode=tk.EXTENDED,bg="white",fg="#16324f",relief="flat")
        self.list.pack(fill="x",pady=(0,12))
        opts=ttk.Frame(body); opts.pack(fill="x")
        ttk.Label(opts,text="مدة الفيديو النهائي (دقيقة)").grid(row=0,column=0,sticky="w",pady=5)
        self.minutes=tk.StringVar(value="5")
        ttk.Entry(opts,textvariable=self.minutes,width=10).grid(row=0,column=1,sticky="w",padx=8)
        ttk.Label(opts,text="نسبة العرض").grid(row=0,column=2,sticky="w",padx=(18,0))
        self.ratio=tk.StringVar(value="الأصلية")
        ttk.Combobox(opts,textvariable=self.ratio,values=["الأصلية","16:9","9:16","1:1"],state="readonly",width=12).grid(row=0,column=3,sticky="w",padx=8)
        ttk.Label(opts,text="الصوت الأصلي").grid(row=1,column=0,sticky="w",pady=5)
        self.audio=tk.StringVar(value="خفض مع الموسيقى")
        ttk.Combobox(opts,textvariable=self.audio,values=["الإبقاء على الصوت الأصلي","كتم الصوت الأصلي","خفض مع الموسيقى"],state="readonly",width=25).grid(row=1,column=1,columnspan=2,sticky="w",padx=8)
        ttk.Label(opts,text="المعالجة").grid(row=2,column=0,sticky="w",pady=5)
        self.look=tk.StringVar(value="طبيعي")
        ttk.Combobox(opts,textvariable=self.look,values=["طبيعي","سينمائي","حيوي"],state="readonly",width=14).grid(row=2,column=1,sticky="w",padx=8)
        ttk.Label(opts,text="الدقة").grid(row=3,column=0,sticky="w",pady=5)
        self.resolution=tk.StringVar(value="1080p")
        ttk.Combobox(opts,textvariable=self.resolution,values=["1080p","4K"],state="readonly",width=14).grid(row=3,column=1,sticky="w",padx=8)
        ttk.Label(opts,text="جودة التصدير").grid(row=4,column=0,sticky="w",pady=5)
        self.quality=tk.StringVar(value="عالية")
        ttk.Combobox(opts,textvariable=self.quality,values=["أعلى جودة","عالية","متوازنة","حجم أصغر"],state="readonly",width=14).grid(row=4,column=1,sticky="w",padx=8)
        self.log=tk.Text(body,height=8,wrap="word",bg="white",fg="#16324f",relief="flat")
        self.log.pack(fill="both",expand=True,pady=10)
        bottom=ttk.Frame(body); bottom.pack(fill="x")
        self.progress=ttk.Progressbar(bottom,mode="determinate",maximum=100); self.progress.pack(fill="x",pady=(0,8))
        self.status=ttk.Label(bottom,text="جاهز")
        self.status.pack(side="left")
        self.startbtn=ttk.Button(bottom,text="إنشاء الفيديو",command=self.start,style="Accent.TButton"); self.startbtn.pack(side="right")
        self.say("المعالجة محلية. هذه نسخة أولية عملية: تحليل تغيّر المشاهد واختيار مقاطع ثم تصديرها عبر FFmpeg. لا تدّعي فهم أحداث الزفاف دلاليًا.")
        if not find_ffmpeg(): self.say("تنبيه: FFmpeg غير موجود. ثبّته وأضف مجلد bin إلى PATH ثم أعد تشغيل البرنامج.")

    def say(self,msg):
        self.log.insert("end",msg+"\n"); self.log.see("end")

    def save_project(self):
        path=filedialog.asksaveasfilename(title="حفظ إعدادات المشروع",defaultextension=".json",
                                          filetypes=[("FrameFlow Project","*.json")],initialfile="FrameFlow_Project.json")
        if not path: return
        data={"app":"FrameFlow Studio","version":VERSION,"media":self.media,"music":self.music,
              "minutes":self.minutes.get(),"ratio":self.ratio.get(),"audio":self.audio.get(),"look":self.look.get(),"quality":self.quality.get(),"resolution":self.resolution.get()}
        try:
            Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            self.say("تم حفظ المشروع: "+path)
        except Exception as e: messagebox.showerror("حفظ المشروع",str(e))

    def load_project(self):
        path=filedialog.askopenfilename(title="فتح مشروع",filetypes=[("FrameFlow Project","*.json")])
        if not path: return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8"))
            self.media=[p for p in data.get("media",[]) if Path(p).exists()]
            self.list.delete(0,"end")
            for p in self.media: self.list.insert("end",Path(p).name)
            self.music=data.get("music","") if Path(data.get("music","")).exists() else ""
            self.minutes.set(str(data.get("minutes","5")))
            self.ratio.set(data.get("ratio","الأصلية"))
            self.audio.set(data.get("audio","خفض مع الموسيقى"))
            self.look.set(data.get("look","طبيعي"))
            self.quality.set(data.get("quality","عالية"))
            self.resolution.set(data.get("resolution","1080p"))
            self.say("تم فتح المشروع. الملفات المفقودة تم تجاهلها.")
        except Exception as e: messagebox.showerror("فتح المشروع",str(e))

    def check_updates(self):
        self.status.configure(text="جارٍ فحص التحديثات...")
        def worker():
            try:
                req=urllib.request.Request("https://api.github.com/repos/LAWWANsa/FrameFlow-Studio/releases/latest",
                                           headers={"User-Agent":"FrameFlow-Studio","Accept":"application/vnd.github+json"})
                with urllib.request.urlopen(req,timeout=8) as resp: data=json.loads(resp.read().decode("utf-8"))
                tag=data.get("tag_name","")
                url=data.get("html_url","https://github.com/LAWWANsa/FrameFlow-Studio/releases")
                if not tag:
                    self.ui(self.status.configure,text="لا توجد إصدارات منشورة بعد")
                    self.ui(lambda:messagebox.showinfo("التحديثات","لا توجد إصدارات رسمية منشورة حتى الآن."))
                elif tag.lstrip("v") != VERSION.lstrip("v"):
                    self.ui(self.status.configure,text="يتوفر إصدار منشور")
                    self.ui(lambda:self.open_update_page(url,tag))
                else:
                    self.ui(self.status.configure,text="أنت تستخدم أحدث إصدار منشور")
                    self.ui(lambda:messagebox.showinfo("التحديثات","لا يوجد إصدار أحدث منشور."))
            except Exception as e:
                self.ui(self.status.configure,text="تعذر فحص التحديثات")
                self.ui(lambda:messagebox.showwarning("التحديثات","تعذر الاتصال بمستودع الإصدارات. تحقق من الإنترنت."))
        threading.Thread(target=worker,daemon=True).start()

    def open_update_page(self,url,tag):
        if messagebox.askyesno("تحديث متاح",f"يتوفر الإصدار {tag}. هل تريد فتح صفحة الإصدار؟"):
            webbrowser.open(url)

    def add_media(self):
        files=filedialog.askopenfilenames(title="اختر الفيديوهات والصور",filetypes=[("Video and photos","*.mp4 *.mov *.mkv *.avi *.m4v *.webm *.jpg *.jpeg *.png *.bmp *.webp"),("Video","*.mp4 *.mov *.mkv *.avi *.m4v *.webm"),("Photos","*.jpg *.jpeg *.png *.bmp *.webp"),("All files","*.*")])
        for f in files:
            if f not in self.media:
                self.media.append(f); self.list.insert("end",Path(f).name)
        if files: self.say(f"تمت إضافة {len(files)} ملف/ملفات.")

    def remove_selected(self):
        sel=list(self.list.curselection())
        for i in reversed(sel): self.list.delete(i); self.media.pop(i)

    def pick_music(self):
        f=filedialog.askopenfilename(title="اختر ملف موسيقى",filetypes=[("Audio","*.mp3 *.wav *.m4a *.aac *.flac"),("All files","*.*")])
        if f: self.music=f; self.say("الموسيقى: "+Path(f).name)

    def start(self):
        if self.busy: return
        if not self.media: messagebox.showwarning("FrameFlow","أضف فيديو واحدًا على الأقل."); return
        ff=find_ffmpeg()
        if not ff: messagebox.showerror("FFmpeg مطلوب","ثبّت FFmpeg وأضف مجلد bin إلى PATH. راجع README."); return
        try: target=float(self.minutes.get())*60
        except: messagebox.showerror("المدة","أدخل مدة صحيحة بالدقائق."); return
        if target<=0: messagebox.showerror("المدة","المدة يجب أن تكون أكبر من صفر."); return
        out=filedialog.asksaveasfilename(title="حفظ الفيديو النهائي",defaultextension=".mp4",filetypes=[("MP4","*.mp4")],initialfile="FrameFlow_Edit.mp4")
        if not out: return
        self.busy=True; self.startbtn.configure(state="disabled"); self.progress["value"]=0
        threading.Thread(target=self.process,args=(ff,target,Path(out)),daemon=True).start()

    def ui(self,fn,*args): self.root.after(0,lambda:fn(*args))

    def process(self,ff,target,out):
        work=out.parent/("_frameflow_temp_"+str(int(time.time())))
        try:
            work.mkdir(parents=True,exist_ok=True)
            self.ui(self.say,"بدء تحليل المقاطع محليًا...")
            assets=[]; total_duration=0
            image_exts={".jpg",".jpeg",".png",".bmp",".webp"}
            for i,path in enumerate(self.media):
                is_photo=Path(path).suffix.lower() in image_exts
                if is_photo:
                    d=5.0
                    scenes=[(0.0,d,1.0)]
                else:
                    d=probe(ff,path)
                    scenes,cvok=detect_scenes(path,d)
                total_duration+=d
                self.ui(self.say,f"{Path(path).name}: {'صورة ثابتة (5 ثوانٍ)' if is_photo else str(len(scenes))+' مقطع/مشهد مرشح'}")
                for a,b,sharp in scenes:
                    if b-a>=1.0: assets.append({"path":path,"start":a,"end":b,"dur":b-a,"sharp":sharp,"is_photo":is_photo})
                self.ui(self.progress.configure, value=5+int(15*(i+1)/len(self.media)))
            if not assets: raise RuntimeError("لم أجد مقاطع قابلة للاستخدام.")
            # Prefer sharper scenes, while keeping source chronology as a tie-breaker.
            assets.sort(key=lambda x:(x["sharp"],-x["dur"]),reverse=True)
            selected=[]; remaining=target
            for item in assets:
                if remaining<=0: break
                take=min(item["dur"],remaining)
                if take<0.8: continue
                selected.append({**item,"take":take})
                remaining-=take
            if remaining>0.5:
                self.ui(self.say,f"تنبيه: المادة المتاحة أقصر من المطلوب بنحو {remaining:.0f} ثانية؛ سيتم تصدير أقصى مدة ممكنة.")
            if not selected: raise RuntimeError("لم تتوفر مدة كافية للتصدير.")
            # Reorder selected clips by original source order for stable first release.
            selected.sort(key=lambda x:(self.media.index(x["path"]),x["start"]))
            self.ui(self.say,f"سيتم تصدير {len(selected)} مقطعًا...")
            segment_files=[]
            for i,item in enumerate(selected):
                seg=work/f"seg_{i:04d}.mp4"
                vf=[]
                ratio=self.ratio.get()
                w,h=(3840,2160) if self.resolution.get()=="4K" else (1920,1080)
                if ratio=="16:9": vf=[f"scale={w}:{h}:force_original_aspect_ratio=decrease",f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"]
                elif ratio=="9:16": vf=[f"scale={h}:{w}:force_original_aspect_ratio=decrease",f"pad={h}:{w}:(ow-iw)/2:(oh-ih)/2"]
                elif ratio=="1:1":
                    side=2160 if self.resolution.get()=="4K" else 1080
                    vf=[f"scale={side}:{side}:force_original_aspect_ratio=decrease",f"pad={side}:{side}:(ow-iw)/2:(oh-ih)/2"]
                else: vf=[f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease","pad=ceil(iw/2)*2:ceil(ih/2)*2"]
                if self.look.get()=="سينمائي": vf += ["eq=contrast=1.08:saturation=0.88"]
                elif self.look.get()=="حيوي": vf += ["eq=contrast=1.04:saturation=1.15"]
                mode=self.audio.get()
                # Normalize every segment to a consistent stereo audio stream so concat works
                # even when some source clips have no audio.
                if item.get("is_photo"):
                    cmd=[ff,"-y","-loop","1","-framerate","30","-i",item["path"],
                         "-f","lavfi","-t",str(item["take"]),"-i","anullsrc=channel_layout=stereo:sample_rate=48000"]
                    audio_map=["-map","1:a:0"]
                else:
                    pr=run([find_ffprobe(ff),
                            "-v","error","-select_streams","a:0","-show_entries","stream=codec_type",
                            "-of","csv=p=0",item["path"]])
                    has_audio=(pr.returncode==0 and bool(pr.stdout.strip()))
                    cmd=[ff,"-y","-ss",str(item["start"]),"-i",item["path"]]
                    if mode=="كتم الصوت الأصلي" or not has_audio:
                        cmd += ["-f","lavfi","-t",str(item["take"]),"-i","anullsrc=channel_layout=stereo:sample_rate=48000"]
                        audio_map=["-map","1:a:0"]
                    else:
                        audio_map=["-map","0:a:0"]
                crf={"أعلى جودة":"17","عالية":"20","متوازنة":"23","حجم أصغر":"27"}.get(self.quality.get(),"20")
                cmd += ["-t",str(item["take"]),"-vf",",".join(vf),"-r","30",
                        "-map","0:v:0",*audio_map,"-c:v","libx264","-preset","veryfast",
                        "-crf",crf,"-pix_fmt","yuv420p","-c:a","aac","-ar","48000",
                        "-ac","2","-b:a","160k","-shortest",str(seg)]
                p=run(cmd)
                if p.returncode: raise RuntimeError("فشل تجهيز مقطع: "+Path(item["path"]).name+"\n"+p.stderr[-1200:])
                segment_files.append(seg)
                self.ui(self.progress.configure,value=20+int(55*(i+1)/len(selected)))
            concat=work/"concat.txt"
            concat.write_text("".join("file '"+str(x.resolve()).replace("'","'\\''")+"'\n" for x in segment_files),encoding="utf-8")
            silent=work/"joined.mp4"
            p=run([ff,"-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
            if p.returncode: raise RuntimeError("فشل دمج المقاطع. "+p.stderr[-1200:])
            mode=self.audio.get()
            if self.music and self.music.lower().endswith((".mp3",".wav",".m4a",".aac",".flac")):
                if mode=="كتم الصوت الأصلي":
                    cmd=[ff,"-y","-i",str(silent),"-stream_loop","-1","-i",self.music,
                         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac",
                         "-b:a","192k","-t",str(target),"-shortest",str(out)]
                else:
                    # Keep source audio at normal level or duck it under the music.
                    original_volume="1.0" if mode=="الإبقاء على الصوت الأصلي" else "0.22"
                    duration=max(1.0,target)
                    fade_start=max(0.0,duration-3.0)
                    cmd=[ff,"-y","-i",str(silent),"-stream_loop","-1","-i",self.music,
                         "-filter_complex",
                         f"[0:a]volume={original_volume}[orig];[1:a]volume=0.22,afade=t=out:st={fade_start}:d=3[music];[orig][music]amix=inputs=2:duration=first:dropout_transition=2[a]",
                         "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac",
                         "-b:a","192k","-t",str(target),"-shortest",str(out)]
                p=run(cmd)
            else:
                # Without music, preserve source audio unless the user explicitly muted it.
                if mode=="كتم الصوت الأصلي":
                    p=run([ff,"-y","-i",str(silent),"-map","0:v:0","-an","-c:v","copy",str(out)])
                else:
                    p=run([ff,"-y","-i",str(silent),"-c","copy",str(out)])
            if p.returncode: raise RuntimeError("فشل التصدير النهائي. "+p.stderr[-1600:])
            self.ui(self.progress.configure,value=100)
            self.ui(self.status.configure,text="اكتمل التصدير")
            self.ui(self.say,"اكتمل: "+str(out))
            self.ui(lambda:messagebox.showinfo("FrameFlow","اكتمل تصدير الفيديو:\n"+str(out)))
        except Exception as e:
            self.ui(self.status.configure,text="حدث خطأ")
            self.ui(self.say,"خطأ: "+str(e))
            self.ui(lambda:messagebox.showerror("تعذر التصدير",str(e)))
        finally:
            try: shutil.rmtree(work,ignore_errors=True)
            except: pass
            self.busy=False
            self.ui(self.startbtn.configure,state="normal")

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
