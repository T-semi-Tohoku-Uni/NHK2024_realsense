import tkinter as tk
from tkinter import messagebox
import pyrealsense2 as rs

from PIL import Image, ImageTk
import numpy as np
from multiprocessing import Queue, Process, RawArray, Lock, Value
from multiprocessing.synchronize import Lock as LockBase
import ctypes
import sys

class CameraCapture:
    def __init__(self, shared_np_image_buf: np.ndarray, lock: LockBase):
        # Init camera capture
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        self.shared_np_image_buf = shared_np_image_buf
        self.lock = lock
            
        # TODO: get default device parameters   
        
        self.gain = Value('d', 0)
        self.gain_is_changed = Value('b', False)
        
        self.process = Process(target=self.capture)
        self.process.start()

    # Run Other Process
    def capture(self):
        # capture setup
        try:
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.pipeline.start(self.config)
        except Exception as e:
            print(f"Fail to initialize realsense pipeline {e}", file=sys.stderr)
            return
        
        # get device settings
        try:
            device = self.pipeline.get_active_profile().get_device()
            self.device = [s for s in device.sensors if s.get_info(rs.camera_info.name) == 'RGB Camera'][0]
            self.device.set_option(rs.option.enable_auto_white_balance, True)
        except Exception as e:
            print(f"Fail to get realsense device {e}", file=sys.stderr)
        
        try:
            # loop
            while True:
                # check shared variable
                if self.gain_is_changed.value:
                    self.device.set_option(rs.option.gain, self.gain.value)
                        
                    with self.gain_is_changed.get_lock():
                        self.gain_is_changed.value = False
                
                # get frame
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if not color_frame:
                    continue
                color_image = np.asanyarray(color_frame.get_data())
                
                with self.lock: # ?
                    self.shared_np_image_buf = color_image
                color_image = self.shared_np_image_buf
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        finally:
            self.pipeline.stop()
    
    def update_white_balance(self, wbl: float):
        pass
    
    def update_gain(self, gain: float):
        print("update_gain")
        self.gain.value = gain
        self.gain_is_changed.value = True
    
    def __del__(self):
        self.process.terminate()

class RealsenseApp:
    def __init__(self, root: tk.Tk):
        print("init settings")
        self.root = root
        self.root.title("RealSense カメラキャプチャ")
        
        # メインフレーム
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.main_frame, width=640, height=480, bg='white')
        self.canvas.pack()
        
        self.side_frame = tk.Frame(self.root)
        self.side_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.serial_label = tk.Label(self.side_frame, text="シリアルナンバー")
        self.serial_label.pack(pady=10)
        
        self.info_label = tk.Label(self.side_frame, text="本体情報")
        self.info_label.pack(pady=10)
        
        # ゲイン入力ボックス
        self.gain_label = tk.Label(self.side_frame, text="Gain")
        self.gain_label.pack(pady=5)
        self.gain_entry = tk.Entry(self.side_frame)
        self.gain_entry.pack(pady=5)
        self.gain_entry.insert(0, "16")  # 初期値を設定
        self.gain_button = tk.Button(self.side_frame, text="設定", command=self.set_gain)
        self.gain_button.pack(pady=10)

        original_image = np.zeros((480, 640, 3), dtype=np.uint8)
        shard_array = RawArray(ctypes.c_uint8, original_image.size)
        self.shared_np_image_buf = np.frombuffer(shard_array, dtype=np.uint8).reshape(original_image.shape)
        self.lock = Lock()
        self.camera = CameraCapture(self.shared_np_image_buf, self.lock)
        self.update_frame()      
    
    def update_frame(self):
        # フレームを取得してキャンバスに表示
        try:
            color_image = self.shared_np_image_buf
            # self.photo = ImageTk.PhotoImage(image=Image.fromarray(color_image))
            # self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.root.after(30, self.update_frame)
        except Exception as e:
            messagebox.showerror("エラー", "フレームの取得中にエラーが発生しました")
            print(e)
    
    def set_gain(self):
        try:
            print("set gain")
            gain_value = float(self.gain_entry.get())
            if 0 <= gain_value <= 128:
                self.camera.update_gain(gain_value)
                messagebox.showinfo("設定完了")
            else:
                messagebox.showerror("エラー", "ゲインは0から128の範囲で入力してください")
        except ValueError:
            messagebox.showerror("エラー", "有効な数値を入力してください")
        except Exception as e:
            messagebox.showerror("エラー", f"ゲインの設定中にエラーが発生しました: {e}")
            print(e)

if __name__ == "__main__":        
    root = tk.Tk()
    app = RealsenseApp(root)
    root.mainloop()