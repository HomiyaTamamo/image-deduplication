import os
import threading
import tkinter as tk  # 这样下面代码里的 tk.Frame 才能生效
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import imagehash


class DuplicateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("涩图去重助手")
        self.root.geometry("900x700")

        self.folder_path = ""
        self.hashes = {}
        self.duplicates = []  # 存储 (path1, path2, similarity)
        self.current_index = 0

        self.setup_ui()

    def setup_ui(self):
        # 顶部控制栏
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X)

        tk.Button(top_frame, text="选择文件夹", command=self.select_folder).pack(side=tk.LEFT, padx=10)
        self.status_label = tk.Label(top_frame, text="请选择文件夹开始扫描")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 中间图片对比区
        self.compare_frame = tk.Frame(self.root)
        self.compare_frame.pack(expand=True, fill=tk.BOTH)

        self.img_label_l = tk.Label(self.compare_frame, text="图片 A")
        self.img_label_l.grid(row=0, column=0, padx=20)
        self.img_label_r = tk.Label(self.compare_frame, text="图片 B")
        self.img_label_r.grid(row=0, column=1, padx=20)

        self.path_label_l = tk.Label(self.compare_frame, text="", wraplength=400)
        self.path_label_l.grid(row=1, column=0)
        self.path_label_r = tk.Label(self.compare_frame, text="", wraplength=400)
        self.path_label_r.grid(row=1, column=1)

        # 底部操作栏
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="保留 A 删除 B", bg="#ffcccb", command=lambda: self.delete_file('B')).pack(
            side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="保留 B 删除 A", bg="#ffcccb", command=lambda: self.delete_file('A')).pack(
            side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="跳过 / 下一组", command=self.next_pair).pack(side=tk.LEFT, padx=10)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            threading.Thread(target=self.scan_images, daemon=True).start()

    def scan_images(self):
        self.status_label.config(text="正在计算哈希值，请稍候...")
        files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path)
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

        # 1. 计算所有图片的哈希
        hashes = []
        for p in files:
            try:
                h = imagehash.phash(Image.open(p))
                hashes.append((p, h))
            except:
                continue

        # 2. 匹配相似图 (阈值可调，10以内通常非常相似)
        self.duplicates = []
        for i in range(len(hashes)):
            for j in range(i + 1, len(hashes)):
                diff = hashes[i][1] - hashes[j][1]
                if diff < 8:  # 差异值越小越像
                    self.duplicates.append((hashes[i][0], hashes[j][0], diff))

        self.duplicates.sort(key=lambda x: x[2])  # 按相似度排序
        self.root.after(0, self.show_pair)

    def show_pair(self):
        if self.current_index >= len(self.duplicates):
            messagebox.showinfo("结束", "没有更多重复项了！")
            return

        p1, p2, diff = self.duplicates[self.current_index]
        self.status_label.config(
            text=f"发现第 {self.current_index + 1}/{len(self.duplicates)} 组相似图 (差异度: {diff})")

        self.display_img(p1, self.img_label_l)
        self.display_img(p2, self.img_label_r)
        self.path_label_l.config(text=f"A: {os.path.basename(p1)}")
        self.path_label_r.config(text=f"B: {os.path.basename(p2)}")

    def display_img(self, path, label):
        img = Image.open(path)
        img.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo

    def delete_file(self, target):
        p1, p2, _ = self.duplicates[self.current_index]
        file_to_del = p2 if target == 'B' else p1
        try:
            os.remove(file_to_del)
            print(f"已删除: {file_to_del}")
            self.next_pair()
        except Exception as e:
            messagebox.showerror("错误", f"无法删除文件: {e}")

    def next_pair(self):
        self.current_index += 1
        self.show_pair()


if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFinder(root)
    root.mainloop()