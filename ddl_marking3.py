from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import csv

class ImageProcessor:
    def __init__(self):
        # 画像のパスをダイアログで選択
        root = tk.Tk()
        root.withdraw()  # Tkのメインウィンドウを表示しない
        file_path = filedialog.askopenfilename()
        if not file_path:
            raise ValueError("No file selected.")
        
        # 新しい画像を読み込む
        self.image = Image.open(file_path)
        self.width, self.height = self.image.size

        # crop_imageメソッドをコンストラクタ内で実行
        self.new_cropped_image = self.crop_image()

    def crop_image(self):
        # 新しい画像の寸法を抽出する
        new_width, new_height = self.width, self.height

        # 新しい画像の長辺と短辺を決定する
        new_long_side = max(new_width, new_height)
        new_short_side = min(new_width, new_height)

        # 分岐条件をチェックし、新しい画像の切り取りを実行する
        if new_short_side * 2 > new_long_side:
            # 長辺を保持し、短辺をリサイズする
            new_new_height = new_long_side // 2 if new_height == new_short_side else new_height
            new_new_width = new_long_side // 2 if new_width == new_short_side else new_width
        else:
            # 長辺をリサイズし、短辺を保持する
            new_new_height = new_short_side if new_height == new_short_side else new_short_side * 2
            new_new_width = new_short_side if new_width == new_short_side else new_short_side * 2

        # 新しい画像のための切り取りボックスを計算する
        new_left = (new_width - new_new_width) / 2
        new_top = (new_height - new_new_height) / 2
        new_right = (new_width + new_new_width) / 2
        new_bottom = (new_height + new_new_height) / 2

        # 新しい画像に切り取りを実行する
        return self.image.crop((new_left, new_top, new_right, new_bottom))

    def make_pixels_coarser(self, image, factor):
        # 元の画像サイズを取得
        original_width, original_height = image.size
        # ピクセルを5倍粗くするために、サイズを1/5に縮小
        resized_width = original_width // factor
        resized_height = original_height // factor
        # 画像を縮小してピクセルを粗くする
        coarser_image = self.new_cropped_image.resize((resized_width, resized_height), Image.NEAREST)
        # 縮小した画像を元のサイズに戻す
        coarser_image = coarser_image.resize((original_width, original_height), Image.NEAREST)
        
        return coarser_image

    def binarize_image(self, image, threshold):
        # 画像をグレースケールに変換
        grayscale_image = image.convert('L')
        # グレースケール画像を閾値を使って2値化（閾値以上は白、以下は黒）
        binary_image = grayscale_image.point(lambda x: 255 if x > threshold else 0, '1')
        
        return binary_image

    def extract_transitions(self, image):
        # 空の辞書変数を初期化
        transitions = {}
        width, height = image.size
        
        # 画像を白黒モードでデータに変換
        pixels = image.load()

        # 各行をスキャン
        index = 0
        for y in range(height):
            start = None
            for x in range(width):
                # 現在のピクセルが白か黒かを判定（0:黒, 255:白）
                current_pixel = pixels[x, y]
                if start is None and current_pixel == 0:
                    # 白から黒への変化点
                    start = (x, y)
                elif start is not None and current_pixel == 255:
                    # 黒から白への変化点
                    end = (x, y)
                    # 変化点を辞書に記録
                    transitions[index] = (start[0], start[1], end[0], end[1])
                    index += 1
                    start = None  # 次の変化点の検出のためにリセット

        return transitions

    def save_transitions_to_csv(self, transitions, file_path):

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # CSVのヘッダーを書き込み
            writer.writerow(['Index', 'X1', 'Y1', 'X2', 'Y2'])
            
            # transitions辞書の内容をCSVに書き込み
            for index, (x1, y1, x2, y2) in transitions.items():
                writer.writerow([index, x1, y1, x2, y2])

    def run(self):
        # オリジナル画像の2値化
        binary_original_image = self.binarize_image(self.new_cropped_image, 128)

        # 粗ピクセル後の2値化
        coarser_image = self.make_pixels_coarser(self.new_cropped_image, 5)
        binary_coarser_image = self.binarize_image(coarser_image, 128)

        # 塗りつぶし座標抽出
        transitions = self.extract_transitions(binary_coarser_image)
        self.save_transitions_to_csv(transitions, 'transitions.csv')

        # 画像の表示
        self.image.show()
        binary_original_image.show()
        binary_coarser_image.show()

# クラスの使用例
if __name__ == "__main__":
    IP = ImageProcessor()
    IP.run()


from tkinter import Tk, Label, Button, Entry, filedialog
from PIL import Image, ImageTk

class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")

        # 画像読み込みボタン
        self.load_button = Button(root, text="画像読み込み", command=self.load_image)
        self.load_button.grid(row=0, column=0)

        # 画像プレビュー
        self.image_preview = Label(root, text="画像プレビュー")
        self.image_preview.grid(row=0, column=1)

        # factor入力ボックス
        self.factor_label = Label(root, text="Factor:")
        self.factor_label.grid(row=1, column=0)
        self.factor_entry = Entry(root)
        self.factor_entry.grid(row=1, column=1)

        # threshold入力ボックス
        self.threshold_label = Label(root, text="Threshold:")
        self.threshold_label.grid(row=2, column=0)
        self.threshold_entry = Entry(root)
        self.threshold_entry.grid(row=2, column=1)

        # 実行ボタン
        self.run_button = Button(root, text="実行", command=self.run)
        self.run_button.grid(row=3, column=0, columnspan=2)

        # EXITボタン
        self.exit_button = Button(root, text="EXIT", command=root.quit)
        self.exit_button.grid(row=4, column=0, columnspan=2)

        # 画像処理用変数
        self.image = None
        self.new_cropped_image = None

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = Image.open(file_path)
            self.preview_image(file_path)

    def preview_image(self, file_path):
        img = Image.open(file_path)
        img.thumbnail((100, 100))
        img = ImageTk.PhotoImage(img)
        self.image_preview.configure(image=img)
        self.image_preview.image = img

    def run(self):
        # ここに`run`メソッドの内容を実装
        pass

    # 既存のImageProcessorクラスのメソッドをここに統合または適応させる

if __name__ == "__main__":
    root = Tk()
    app = ImageProcessorGUI(root)
    root.mainloop()
