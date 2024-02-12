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


class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")
        self.root.geometry("800x400")

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
        self.threshold_entry.insert(0, "30")

        # factor入力ボックス
        self.factor_label = Label(self.middle_frame, text="Factor:")
        self.factor_label.grid(row=1, column=0)
        self.factor_entry = Entry(self.middle_frame)
        self.factor_entry.grid(row=1, column=1)
        self.factor_entry.insert(0, "5")

        # cutoff入力ボックス
        self.cutoff_label = Label(self.middle_frame, text="Cutoff:")
        self.cutoff_label.grid(row=2, column=0)
        self.cutoff_entry = Entry(self.middle_frame)
        self.cutoff_entry.grid(row=2, column=1)
        self.cutoff_entry.insert(0, "100")

        # 「再処理」ボタンと行数表示ラベルの追加
        self.reprocess_button = Button(self.middle_frame, text="再処理", command=self.reprocess_image)
        self.reprocess_button.grid(row=3, column=0, pady=5)

        self.num_transitions_label = Label(self.middle_frame, text="行数：")
        self.num_transitions_label.grid(row=3, column=1, sticky="w")

        # 下段フレームの追加
        self.bottom_frame = Frame(root)
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 20))

        # 実行ボタン
        self.run_button = Button(self.bottom_frame, text="CSV出力", command=self.csv_run, width=20)
        self.run_button.pack(side="left", padx=(0, 10))  # 左側のボタンには右側にのみパディングを追加

        # EXITボタン
        self.exit_button = Button(self.bottom_frame, text="EXIT", command=root.quit, width=20)
        self.exit_button.pack(side="left")


        # 画像処理用変数
        self.image = None
        self.processed_image = None

    # 画像の読み込みを実行する関数
    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = Image.open(file_path)
            self.preview_image(self.image, self.original_image_preview)
            self.process_and_preview_image()
            self.file_path = file_path

    # 画像処理を実行する関数
    def process_and_preview_image(self):
        self.cropped_image = self.crop_image(self.image)
        self.edited_image = self.binarize_image(self.cropped_image)
        self.marking_image = self.make_pixels_coarser(self.edited_image)
        self.transitions = self.extract_transitions(self.marking_image)
        self.pil_image_with_contours, self.filtered_contours = self.extract_contours()
        self.coordinates_dict = self.flatten_contours()
        self.num_transitions_label.configure(text=f"行数：v{len(self.transitions)}/r{len(self.coordinates_dict)}/t{len(self.transitions) + len(self.coordinates_dict)}")
        self.preview_image(self.pil_image_with_contours, self.edited_image_preview)

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

    # 画像を2値化処理する関数
    def binarize_image(self, image):
        threshold = int(self.threshold_entry.get() or 30)
        grayscale_image = image.convert('L')
        return grayscale_image.point(lambda x: 255 if x > threshold else 0, '1')

    # 画像のピクセルを粗くする関数
    def make_pixels_coarser(self, image):
        factor = int(self.factor_entry.get() or 10)
        original_width, original_height = image.size
        resized_width = original_width // factor
        resized_height = original_height // factor
        coarser_image = image.resize((resized_width, resized_height), Image.NEAREST)
        return coarser_image.resize((original_width, original_height), Image.NEAREST)

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
        self.process_and_preview_image()

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
        self.num_transitions_label.configure(text=f"行数：{len(transitions)}")
        return transitions

    # 輪郭を抽出する関数
    def extract_contours(self):
        edited_image_cv = array(self.edited_image.convert('L'))
        bw_image_cv = bitwise_not(edited_image_cv)
        contours, _ = findContours(bw_image_cv, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

        cutoff_area = int(self.cutoff_entry.get() or 100)
        filtered_contours = [cnt for cnt in contours if cutoff_area <= contourArea(cnt)]

        marking_image_cv = array(self.marking_image.convert('L'))
        grayscale_bgr_image = cvtColor(marking_image_cv, COLOR_GRAY2BGR)
        drawContours(grayscale_bgr_image, filtered_contours, -1, (0, 0, 255), 2)
        pil_image_with_contours = Image.fromarray(cvtColor(grayscale_bgr_image, COLOR_BGR2RGB))

        return pil_image_with_contours, filtered_contours

    # 輪郭抽出した座標を変換する関数
    def flatten_contours(self):
        # 輪郭の座標をひとつの配列に集約する
        coordinates_dict = {}
        key_num = 1
        for contour in self.filtered_contours:

            flattened_list = []
            for point in contour:
                x, y = point[0]
                flattened_list.append((x, y))

            # 輪郭の座標を辞書変数に再構築する
            for i in range(len(flattened_list) - 1):
                x1, y1 = flattened_list[i]
                x2, y2 = flattened_list[i + 1]
                coordinates_dict[key_num + i] = [x1, y1, x2, y2]

            key_num += i + 1

        return coordinates_dict

    # csvファイルを作成実行する関数
    def csv_run(self):
        if self.image is None:
            messagebox.showwarning("警告", "画像が読み込まれていません。")
        else:
            merged_dict = self.merge_dictionaries()
            rotated_dict = self.rotate_90(merged_dict)
            scaled_and_offset_dict = self.scale_and_offset(rotated_dict)
            self.save_dict_to_csv(scaled_and_offset_dict)

    # 塗と輪郭の座標を結合する関数
    def merge_dictionaries(self):
        last_key = max(self.transitions.keys()) if self.transitions else 0
        updated_coordinates_dict = {key + last_key: value for key, value in self.coordinates_dict.items()}
        merged_dict = {**self.transitions, **updated_coordinates_dict}

        return merged_dict

    # 座標を90度回転する関数
    def rotate_90(self, merged_dict):
        rotated_dict = {}
        for index, (x1, y1, x2, y2) in merged_dict.items():
            # 各点に対して90度回転を実行
            new_x1, new_y1 = -y1, x1
            new_x2, new_y2 = -y2, x2
            rotated_dict[index] = (new_x1, new_y1, new_x2, new_y2)
        return rotated_dict

    # 座標を縮小とオフセットする関数
    def scale_and_offset(self, rotated_dict):
        # self.edited_imageのサイズを取得
        width, height = self.edited_image.size
        
        # 長い辺と短い辺の判定
        long_side = max(width, height)
        short_side = min(width, height)
        
        # 縮尺の計算
        scale_long = 40 / long_side
        scale_short = 20 / short_side
        
        scaled_and_offset_dict = {}
        for index, (x1, y1, x2, y2) in rotated_dict.items():
            # 縮尺適用
            new_x1 = round(x1 * scale_short, 2)
            new_y1 = round(y1 * scale_long, 2)
            new_x2 = round(x2 * scale_short, 2)
            new_y2 = round(y2 * scale_long, 2)
            
            # オフセット適用
            new_x1 = round(new_x1 + 10, 2)
            new_y1 = round(new_y1 - 20, 2)
            new_x2 = round(new_x2 + 10, 2)
            new_y2 = round(new_y2 - 20, 2)
            
            scaled_and_offset_dict[index] = (new_x1, new_y1, new_x2, new_y2)
            
        return scaled_and_offset_dict

    # csvファイルを保存する関数
    def save_dict_to_csv(self, edited_dict):
        image_directory = os.path.dirname(self.file_path)
        csv_file_path = os.path.join(image_directory, 'zahyou.csv')

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Index', 'X1', 'Y1', 'X2', 'Y2'])
            
            for index, (x1, y1, x2, y2) in edited_dict.items():
                writer.writerow([index, x1, y1, x2, y2])

        messagebox.showinfo("完了", "csvファイル出力完了")

if __name__ == "__main__":
    root = Tk()
    app = ImageProcessorGUI(root)
    root.mainloop()
