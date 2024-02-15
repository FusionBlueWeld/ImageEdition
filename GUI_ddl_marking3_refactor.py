import csv
import os
import math
from tkinter import Tk, Label, Button, Entry, Frame, filedialog, messagebox
from PIL import Image, ImageTk
from cv2 import (
    findContours, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE, cvtColor,
    contourArea, drawContours, bitwise_not, COLOR_GRAY2BGR, COLOR_BGR2RGB
)
from numpy import array

class GUIComponents:
    def __init__(self, root):
        self.root = root
        self.image_processor = ImageProcessor()  # GUI内で画像処理クラスのインスタンスを生成
        self.setup_ui()

        # ロードする画像情報の保存変数
        self.file_path = None
        self.image = None

    def setup_ui(self):
        self.initialize_gui()
        self.setup_top_frame()
        self.setup_middle_frame()
        self.setup_bottom_frame()

    def initialize_gui(self):
        self.root.title("Image Processor")
        self.root.geometry("800x400")

    def setup_top_frame(self):
        # 上段フレームの追加
        self.top_frame = Frame(self.root)
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

    def setup_middle_frame(self):
        # 中段フレームの追加
        self.middle_frame = Frame(self.root)
        self.middle_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.middle_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

        # threshold入力ボックス
        self.threshold_label = Label(self.middle_frame, text="Threshold:")
        self.threshold_label.grid(row=0, column=0)
        self.threshold_entry = Entry(self.middle_frame)
        self.threshold_entry.grid(row=0, column=1)
        self.threshold_entry.insert(0, str(self.image_processor.threshold))

        # factor入力ボックス
        self.factor_label = Label(self.middle_frame, text="Factor:")
        self.factor_label.grid(row=1, column=0)
        self.factor_entry = Entry(self.middle_frame)
        self.factor_entry.grid(row=1, column=1)
        self.factor_entry.insert(0, str(self.image_processor.factor))

        # cutoff入力ボックス
        self.cutoff_label = Label(self.middle_frame, text="Cutoff:")
        self.cutoff_label.grid(row=2, column=0)
        self.cutoff_entry = Entry(self.middle_frame)
        self.cutoff_entry.grid(row=2, column=1)
        self.cutoff_entry.insert(0, str(self.image_processor.cutoff_area))

        # 「再処理」ボタンと行数表示ラベルの追加
        self.reprocess_button = Button(self.middle_frame, text="再処理", command=self.reprocess_image)
        self.reprocess_button.grid(row=3, column=0, pady=5)

        self.num_transitions_label = Label(self.middle_frame, text="行数：")
        self.num_transitions_label.grid(row=3, column=1, sticky="w")

    def setup_bottom_frame(self):
        # 下段フレームの追加
        self.bottom_frame = Frame(self.root)
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 20))

        # CSV出力ボタン
        self.run_button = Button(self.bottom_frame, text="CSV出力", command=self.trigger_csv_creation, width=20)
        self.run_button.pack(side="left", padx=(0, 10))  # 左側のボタンには右側にのみパディングを追加

        # EXITボタン
        self.exit_button = Button(self.bottom_frame, text="EXIT", command=root.quit, width=20)
        self.exit_button.pack(side="left")

    # 画像の読み込みを実行する関数
    def load_image(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            # オリジナル画像のプレビュー
            self.image = Image.open(self.file_path)
            self.preview_image(self.image, self.original_image_preview)

            # 編集画像のプレビュー
            self.load_parameter()
            edited_image, transitions = self.image_processor.process_image(self.image)
            self.preview_image(edited_image, self.edited_image_preview)
            self.num_transitions_label.configure(text=f"行数：{len(transitions)}")

    # 画像処理パラメータを更新
    def load_parameter(self):
        threshold = int(self.threshold_entry.get() or 30)
        factor = int(self.factor_entry.get() or 10)
        cutoff_area = int(self.cutoff_entry.get() or 100)
        self.image_processor.set_parameters(threshold, factor, cutoff_area)

    # 画像のプレビューを表示する関数
    def preview_image(self, image, label):
        img_copy = image.copy()
        base_width = 320
        w_percent = (base_width / float(img_copy.size[0]))
        h_size = int((float(img_copy.size[1]) * float(w_percent)))
        img_resized = img_copy.resize((base_width, h_size), Image.LANCZOS)
        img = ImageTk.PhotoImage(img_resized)
        label.configure(image=img)
        label.image = img

    # 画像を再処理する関数
    def reprocess_image(self):
        if self.image is None:
            messagebox.showwarning("警告", "画像が読み込まれていません。")
            return

        # 編集画像のプレビュー
        self.load_parameter()
        edited_image, transitions = self.image_processor.process_image(self.image)
        self.preview_image(edited_image, self.edited_image_preview)
        self.num_transitions_label.configure(text=f"行数：{len(transitions)}")

    # csvファイルを作成実行する関数
    def trigger_csv_creation(self):
        pass

class ImageProcessor:
    def __init__(self):
        # デフォルトパラメータの初期化
        self.threshold = 30
        self.factor = 10
        self.cutoff_area = 100

    # パラメータの更新
    def set_parameters(self, threshold, factor, cutoff_area):
        self.threshold = threshold
        self.factor = factor
        self.cutoff_area = cutoff_area

    # 画像処理を実行する関数
    def process_image(self, image):
        cropped_image = self.crop_image(image)
        flipped_image = self.flip_image_horizontally(cropped_image)
        binarized_image = self.binarize_image(flipped_image)
        pixeled_image = self.make_pixels_coarser(binarized_image)

        transitions = self.extract_transitions(pixeled_image)

        return pixeled_image, transitions

    # 画像を2:1にトリミングする関数
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

    # 画像を左右反転させる関数
    def flip_image_horizontally(self, image):
        return image.transpose(Image.FLIP_LEFT_RIGHT)

    # 画像を2値化処理する関数
    def binarize_image(self, image):
        grayscale_image = image.convert('L')
        return grayscale_image.point(lambda x: 255 if x > self.threshold else 0, '1')

    # 画像のピクセルを粗くする関数
    def make_pixels_coarser(self, image):
        original_width, original_height = image.size
        resized_width = original_width // self.factor
        resized_height = original_height // self.factor
        coarser_image = image.resize((resized_width, resized_height), Image.NEAREST)
        return coarser_image

    # 塗りつぶしの座標を抽出する関数
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
        return transitions

    def extract_contours(self):
        pass

    def flatten_contours(self):
        pass

    def merge_dictionaries(self):
        pass

    def rotate_90(self):
        pass

    def scale_and_offset(self):
        pass

    def save_dict_to_csv(self):
        pass

if __name__ == "__main__":
    root = Tk()
    app = GUIComponents(root)
    root.mainloop()
