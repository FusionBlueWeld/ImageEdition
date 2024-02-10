from tkinter import Tk, Label, Button, Entry, Frame, filedialog, messagebox
from PIL import Image, ImageTk
import os
import csv

class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")
        self.root.geometry("800x600")

        # 上段フレームの追加
        self.top_frame = Frame(root)
        self.top_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(20, 10))

        # 画像読み込みボタン
        self.load_button = Button(self.top_frame, text="画像読み込み", command=self.load_image)
        self.load_button.pack(side="left")

        # 画像プレビュー用ラベル
        self.original_image_preview = Label(self.top_frame, text="オリジナル画像プレビュー")
        self.original_image_preview.pack(side="left", padx=10)

        self.edited_image_preview = Label(self.top_frame, text="編集画像プレビュー")
        self.edited_image_preview.pack(side="left", padx=10)

        # 中段フレームの追加
        self.middle_frame = Frame(root)
        self.middle_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.middle_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

        # threshold入力ボックス
        self.threshold_label = Label(self.middle_frame, text="Threshold:")
        self.threshold_label.grid(row=0, column=0)
        self.threshold_entry = Entry(self.middle_frame)
        self.threshold_entry.grid(row=0, column=1)
        self.threshold_entry.insert(0, "30")  # デフォルトで30を設定

        # factor入力ボックス
        self.factor_label = Label(self.middle_frame, text="Factor:")
        self.factor_label.grid(row=1, column=0)
        self.factor_entry = Entry(self.middle_frame)
        self.factor_entry.grid(row=1, column=1)
        self.factor_entry.insert(0, "5")  # デフォルトで5を設定

        # 「再処理」ボタンと行数表示ラベルの追加
        self.reprocess_button = Button(self.middle_frame, text="再処理", command=self.reprocess_image)
        self.reprocess_button.grid(row=2, column=0, pady=5)

        self.num_transitions_label = Label(self.middle_frame, text="行数：")
        self.num_transitions_label.grid(row=2, column=1, sticky="w")

        # 下段フレームの追加
        self.bottom_frame = Frame(root)
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 20))

        # 実行ボタン
        self.run_button = Button(self.bottom_frame, text="CSV出力", command=self.csv_run)
        self.run_button.pack(side="left", fill="x", expand=True)

        # EXITボタン
        self.exit_button = Button(self.bottom_frame, text="EXIT", command=root.quit)
        self.exit_button.pack(side="left", fill="x", expand=True)

        # 画像処理用変数
        self.image = None
        self.processed_image = None

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = Image.open(file_path)
            self.preview_image(self.image, self.original_image_preview)
            self.edited_image = self.binarize_image((self.crop_image(self.image)))
            self.marking_image = self.make_pixels_coarser(self.edited_image)
            self.preview_image(self.marking_image, self.edited_image_preview)
            self.file_path = file_path

    def crop_image(self, image):
        new_width, new_height = image.size

        new_long_side = max(new_width, new_height)
        new_short_side = min(new_width, new_height)
        if new_short_side * 2 > new_long_side:
            new_new_height = new_long_side // 2 if new_height == new_short_side else new_height
            new_new_width = new_long_side // 2 if new_width == new_short_side else new_width
        else:
            new_new_height = new_short_side if new_height == new_short_side else new_short_side * 2
            new_new_width = new_short_side if new_width == new_short_side else new_short_side * 2
        new_left = (new_width - new_new_width) / 2
        new_top = (new_height - new_new_height) / 2
        new_right = (new_width + new_new_width) / 2
        new_bottom = (new_height + new_new_height) / 2
        return image.crop((new_left, new_top, new_right, new_bottom))

    def binarize_image(self, image):
        threshold = int(self.threshold_entry.get() or 30)
        grayscale_image = image.convert('L')
        return grayscale_image.point(lambda x: 255 if x > threshold else 0, '1')

    def make_pixels_coarser(self, image):
        factor = int(self.factor_entry.get() or 10)
        original_width, original_height = image.size
        resized_width = original_width // factor
        resized_height = original_height // factor
        coarser_image = image.resize((resized_width, resized_height), Image.NEAREST)
        return coarser_image.resize((original_width, original_height), Image.NEAREST)

    def preview_image(self, image, label):
        img_copy = image.copy()
        base_width = 250  # 画像の幅を適切に設定
        w_percent = (base_width / float(img_copy.size[0]))
        h_size = int((float(img_copy.size[1]) * float(w_percent)))
        img_resized = img_copy.resize((base_width, h_size), Image.LANCZOS)
        img = ImageTk.PhotoImage(img_resized)
        label.configure(image=img)
        label.image = img

    def reprocess_image(self):
        if self.image is None:
            messagebox.showwarning("警告", "画像が読み込まれていません。")
            return
        self.edited_image = self.binarize_image((self.crop_image(self.image)))
        self.marking_image = self.make_pixels_coarser(self.edited_image)
        self.transitions = self.extract_transitions(self.marking_image)
        self.num_transitions_label.configure(text=f"行数：{len(self.transitions)}")
        self.preview_image(self.marking_image, self.edited_image_preview)

    def extract_transitions(self, image):
        transitions = {}
        width, height = image.size
        
        pixels = image.load()
        index = 0
        for y in range(height):
            start = None
            for x in range(width):
                current_pixel = pixels[x, y]
                if start is None and current_pixel == 0:
                    start = (x, y)
                elif start is not None and current_pixel == 255:
                    end = (x, y)
                    transitions[index] = (start[0], start[1], end[0], end[1])
                    index += 1
                    start = None
        self.num_transitions_label.configure(text=f"行数：{len(transitions)}")  # 行数を更新
        return transitions

    def csv_run(self):
        if self.image is None:  # edited_imageがNoneの場合、警告を表示
            messagebox.showwarning("警告", "画像が読み込まれていません。")
        else:
            self.save_transitions_to_csv(self.transitions)

    def save_transitions_to_csv(self, transitions):
        image_directory = os.path.dirname(self.file_path)
        csv_file_path = os.path.join(image_directory, 'zahyou.csv')

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Index', 'X1', 'Y1', 'X2', 'Y2'])
            
            for index, (x1, y1, x2, y2) in transitions.items():
                writer.writerow([index, x1, y1, x2, y2])

        messagebox.showinfo("完了", "csvファイル出力完了")  # ポップアップの表示

if __name__ == "__main__":
    root = Tk()
    app = ImageProcessorGUI(root)
    root.mainloop()
