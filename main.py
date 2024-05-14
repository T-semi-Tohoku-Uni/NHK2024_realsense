import tkinter as tk
from tkinter import messagebox
import pyrealsense2 as rs

from PIL import Image, ImageTk
import numpy as np

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
        self.gain_label.pack(pady=10)
        self.gain_entry = tk.Entry(self.side_frame)
        self.gain_entry.pack(pady=10)
        self.gain_entry.insert(0, "16")  # 初期値を設定
        self.gain_button = tk.Button(self.side_frame, text="設定", command=self.set_gain)
        self.gain_button.pack(pady=10)

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        print("end settings")

        try:
            # RealSense カメラのストリームを構成
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.pipeline.start(self.config)
            
            device = self.pipeline.get_active_profile().get_device()
            self.device = [s for s in device.sensors if s.get_info(rs.camera_info.name) == 'RGB Camera'][0]
            self.device.set_option(rs.option.enable_auto_white_balance, True)
            
            self.update_frame()
        except Exception as e:
            messagebox.showerror("エラー", "RealSense カメラが接続されていません")
            print(e)
    
    def update_frame(self):
        # フレームを取得してキャンバスに表示
        try:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                return

            color_image = np.asanyarray(color_frame.get_data())
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(color_image))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.root.after(30, self.update_frame)
        except Exception as e:
            messagebox.showerror("エラー", "フレームの取得中にエラーが発生しました")
            print(e)
    
    def set_gain(self):
        try:
            print("set gain")
            gain_value = float(self.gain_entry.get())
            if 0 <= gain_value <= 128:
                self.device.set_option(rs.option.gain, gain_value)
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