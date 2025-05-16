import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import cv2
import numpy as np
import pyautogui
import os
import time
# ----------------------------------
# 主录屏软件类
# ----------------------------------

class ScreenRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("简易录屏软件(多线程)")
        
        # 录制状态变量
        self.is_recording = False      # 是否正在录制
        self.is_paused = False         # 是否暂停录制
        self.recording_thread = None   # 录屏线程句柄
        self.out = None                # 视频写入对象

        # 获取屏幕分辨率
        screen_size = pyautogui.size()
        self.screen_size = (screen_size.width, screen_size.height)
        
        # 默认帧率
        self.fps = 15.0

        # 文件保存相关变量
        self.output_dir = tk.StringVar()
        self.base_filename = tk.StringVar(value="recording")
        
        # --------- 创建界面组件 ---------
        self.create_widgets()

    # ----------------------------------
    # 创建Tkinter界面组件
    # ----------------------------------
    def create_widgets(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(frame_top, text="文件保存文件夹:").pack(side=tk.LEFT)
        self.entry_dir = tk.Entry(frame_top, textvariable=self.output_dir, width=40)
        self.entry_dir.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="浏览", command=self.browse_dir).pack(side=tk.LEFT)

        frame_mid = tk.Frame(self.root)
        frame_mid.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(frame_mid, text="基础文件名:").pack(side=tk.LEFT)
        self.entry_name = tk.Entry(frame_mid, textvariable=self.base_filename, width=30)
        self.entry_name.pack(side=tk.LEFT, padx=5)

        frame_control = tk.Frame(self.root)
        frame_control.pack(pady=15)

        self.btn_start = tk.Button(frame_control, text="开始录制", width=12, command=self.start_record)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_pause = tk.Button(frame_control, text="暂停", width=12, command=self.pause_record, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(frame_control, text="停止录制", width=12, command=self.stop_record, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.root, text="状态：空闲")
        self.status_label.pack(pady=5)

    # ----------------------------------
    # 选择保存目录回调
    # ----------------------------------
    def browse_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)

    # ----------------------------------
    # 自动生成文件名，避免重名覆盖
    # ----------------------------------
    def generate_filename(self):
        base = self.base_filename.get().strip()
        if not base:
            base = "recording"
        directory = self.output_dir.get().strip()
        if not directory:
            directory = os.getcwd()

        # 自动加序号 001-999 找可用文件名
        for i in range(1, 1000):
            filename = f"{base}_{i:03d}.avi"
            full_path = os.path.join(directory, filename)
            if not os.path.exists(full_path):
                return full_path
        # 如果都存在，返回基本名覆盖（极少情况）
        return os.path.join(directory, f"{base}.avi")

    # ----------------------------------
    # 录制屏幕函数，运行于独立线程
    # ----------------------------------
    def record_screen(self):
        filename = self.generate_filename()
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter(filename, fourcc, self.fps, self.screen_size)

        # 更新状态提示
        self.update_status("状态：录制中")

        while self.is_recording:
            if self.is_paused:
                time.sleep(0.1)
                continue

            # 截图并写入视频
            img = pyautogui.screenshot()
            frame = np.array(img)
            # pyautogui截图格式是RGB，需要转成BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.out.write(frame)

            # 控制帧率，waitKey以毫秒为单位
            cv2.waitKey(int(1000 / self.fps))

        # 结束录制，释放资源
        self.out.release()
        self.update_status(f"状态：录制完成，已保存：{filename}")
        # 录制完成弹窗
        messagebox.showinfo("录制完成", f"录屏已保存到:\n{filename}")

    # ----------------------------------
    # 更新界面状态文字（线程安全）
    # ----------------------------------
    def update_status(self, text):
        def setter():
            self.status_label.config(text=text)
        self.root.after(0, setter)

    # ----------------------------------
    # 开始录制按钮回调
    # ----------------------------------
    def start_record(self):
        if self.is_recording:
            messagebox.showwarning("警告", "录制已进行中")
            return
        if not self.output_dir.get().strip():
            messagebox.showwarning("提示", "请选择文件保存目录！")
            return

        self.is_recording = True
        self.is_paused = False

        # 创建并启动录屏线程，避免阻塞主线程
        self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
        self.recording_thread.start()

        # 更新按钮和状态
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="暂停")
        self.btn_stop.config(state=tk.NORMAL)
        self.update_status("状态：准备录制...")

    # ----------------------------------
    # 暂停/继续录制按钮回调
    # ----------------------------------
    def pause_record(self):
        if not self.is_recording:
            return
        if self.is_paused:
            self.is_paused = False
            self.btn_pause.config(text="暂停")
            self.update_status("状态：录制中")
        else:
            self.is_paused = True
            self.btn_pause.config(text="继续")
            self.update_status("状态：暂停中")

    # ----------------------------------
    # 停止录制按钮回调
    # ----------------------------------
    def stop_record(self):
        if not self.is_recording:
            return
        self.is_recording = False
        # 等待线程结束，避免资源冲突
        if self.recording_thread is not None:
            self.recording_thread.join()

        # 重置按钮状态
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="暂停")
        self.btn_stop.config(state=tk.DISABLED)

    # ----------------------------------
    # 窗口关闭时回调，防止录制中强制关闭
    # ----------------------------------
    def on_closing(self):
        if self.is_recording:
            if messagebox.askokcancel("退出", "录制尚未结束，确定退出吗？"):
                self.is_recording = False
                if self.recording_thread is not None:
                    self.recording_thread.join()
                self.root.destroy()
        else:
            self.root.destroy()

# ----------------------------------
# 程序入口
# ----------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
