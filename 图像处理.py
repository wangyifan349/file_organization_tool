import sys
import cv2
import numpy as np
import pyexif  # 用于处理清除EXIF信息
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSlider, QPushButton, QVBoxLayout,
    QWidget, QFileDialog, QHBoxLayout, QGroupBox, QLineEdit, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

class ImageProcessor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Processor")
        self.setGeometry(100, 100, 1400, 900)  # 较大窗口

        self.image = None
        self.processed_image = None

        # 主部件及整体布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 图片显示区（自适应大小）
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.image_label)

        # 控件区域：使用网格布局排列各参数控件
        self.controls_widget = QWidget(self)
        self.controls_layout = QGridLayout(self.controls_widget)
        self.controls_layout.setSpacing(10)
        self.main_layout.addWidget(self.controls_widget)

        # 创建各个参数控件（滑动条 + 文本输入框）
        self.brightness_slider = self.create_slider_with_input("Brightness", -100, 100, 0)
        self.contrast_slider   = self.create_slider_with_input("Contrast", 1, 300, 100)  # 初始值为百分比100
        self.blur_slider       = self.create_slider_with_input("Gaussian Blur", 1, 31, 1)
        self.median_slider     = self.create_slider_with_input("Median Blur", 1, 31, 1)
        self.canny_slider      = self.create_slider_with_input("Canny Edge", 0, 255, 100)

        # 将控件添加到网格布局中（两行）
        self.controls_layout.addWidget(self.brightness_slider["group"], 0, 0)
        self.controls_layout.addWidget(self.contrast_slider["group"], 0, 1)
        self.controls_layout.addWidget(self.blur_slider["group"], 0, 2)
        self.controls_layout.addWidget(self.median_slider["group"], 1, 0)
        self.controls_layout.addWidget(self.canny_slider["group"], 1, 1)

        # 按钮区域
        self.buttons_widget = QWidget(self)
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setSpacing(20)
        self.main_layout.addWidget(self.buttons_widget)

        font = QFont()
        font.setPointSize(11)

        self.sharpen_button = QPushButton("Sharpen Image", self)
        self.sharpen_button.setFont(font)
        self.sharpen_button.clicked.connect(self.sharpen_image)
        self.buttons_layout.addWidget(self.sharpen_button)

        self.equalize_button = QPushButton("Equalize Histogram", self)
        self.equalize_button.setFont(font)
        self.equalize_button.clicked.connect(self.equalize_histogram)
        self.buttons_layout.addWidget(self.equalize_button)

        self.flip_button = QPushButton("Flip Image", self)
        self.flip_button.setFont(font)
        self.flip_button.clicked.connect(self.flip_image)
        self.buttons_layout.addWidget(self.flip_button)

        self.open_button = QPushButton("Open Image", self)
        self.open_button.setFont(font)
        self.open_button.clicked.connect(self.open_image)
        self.buttons_layout.addWidget(self.open_button)

        self.save_button = QPushButton("Save Image", self)
        self.save_button.setFont(font)
        self.save_button.clicked.connect(self.save_image)
        self.buttons_layout.addWidget(self.save_button)

    def create_slider_with_input(self, name, min_val, max_val, init_val):
        """
        创建一个包含 QSlider 和 QLineEdit 的组合控件，并返回一个字典，
        包含 'group'(GroupBox), 'slider' 和 'line_edit'
        """
        group = QGroupBox(name)
        vbox = QVBoxLayout()
        group.setLayout(vbox)

        slider = QSlider(Qt.Horizontal, self)
        slider.setRange(min_val, max_val)
        slider.setValue(init_val)
        vbox.addWidget(slider)

        line_edit = QLineEdit(str(init_val), self)
        line_edit.setFixedWidth(60)
        line_edit.setAlignment(Qt.AlignCenter)
        vbox.addWidget(line_edit)

        # 双向绑定：滑动条变化更新文本框，文本框输入更新滑动条
        slider.valueChanged.connect(lambda value, le=line_edit: self.slider_value_changed(value, le))
        slider.valueChanged.connect(self.update_image)
        line_edit.returnPressed.connect(lambda s=slider, le=line_edit: self.line_edit_changed(s, le))
        
        return {"group": group, "slider": slider, "line_edit": line_edit}

    def slider_value_changed(self, value, line_edit):
        line_edit.setText(str(value))
    
    def line_edit_changed(self, slider, line_edit):
        try:
            value = int(line_edit.text())
        except ValueError:
            value = slider.value()
        value = max(slider.minimum(), min(slider.maximum(), value))
        slider.setValue(value)
        line_edit.setText(str(value))
        self.update_image()

    def open_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "",
                                                   "Images (*.png *.xpm *.jpg *.bmp *.tiff)", options=options)
        if file_name:
            self.image = cv2.imread(file_name)
            if self.image is None:
                return
            self.processed_image = self.image.copy()
            self.update_image()  # 打开图片后刷新显示

    def save_image(self):
        if self.processed_image is not None:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Image File", "",
                                                       "Images (*.png *.xpm *.jpg *.bmp *.tiff)", options=options)
            if file_name:
                # 首先使用 cv2.imwrite 保存图像（此方式默认不会保存 EXIF 信息）
                cv2.imwrite(file_name, self.processed_image)
                # 为了保险起见，调用 pyexif 清除文件内可能存在的 EXIF 信息
                try:
                    editor = pyexif.ExifEditor(file_name)
                    editor.clear()
                    editor.write_file()
                except Exception as e:
                    print("清除 EXIF 信息失败:", e)

    def update_image(self):
        if self.image is None:
            return

        # 从原图复制图像进行处理
        self.processed_image = self.image.copy()

        # 亮度、对比度调整
        brightness = self.brightness_slider["slider"].value()
        contrast = self.contrast_slider["slider"].value() / 100.0
        self.processed_image = cv2.convertScaleAbs(self.processed_image, alpha=contrast, beta=brightness)

        # 高斯模糊，注意核尺寸须为奇数
        blur_value = self.blur_slider["slider"].value()
        if blur_value % 2 == 0:
            blur_value += 1
        self.processed_image = cv2.GaussianBlur(self.processed_image, (blur_value, blur_value), 0)

        # 中值滤波，确保核尺寸为奇数
        median_value = self.median_slider["slider"].value()
        if median_value % 2 == 0:
            median_value += 1
        self.processed_image = cv2.medianBlur(self.processed_image, median_value)

        # Canny 边缘检测
        canny_threshold = self.canny_slider["slider"].value()
        edges = cv2.Canny(self.processed_image, canny_threshold, canny_threshold * 2)
        self.processed_image = cv2.bitwise_and(self.processed_image, self.processed_image, mask=edges)

        self.display_image()

    def sharpen_image(self):
        if self.processed_image is not None:
            sharpening_kernel = np.array([[-1, -1, -1],
                                          [-1,  9, -1],
                                          [-1, -1, -1]])
            self.processed_image = cv2.filter2D(self.processed_image, -1, sharpening_kernel)
            self.display_image()

    def equalize_histogram(self):
        if self.processed_image is not None:
            # 判断图像是灰度还是彩色
            if len(self.processed_image.shape) == 2 or self.processed_image.shape[2] == 1:
                self.processed_image = cv2.equalizeHist(self.processed_image)
            else:
                ycrcb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2YCrCb)
                ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
                self.processed_image = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
            self.display_image()

    def flip_image(self):
        if self.processed_image is not None:
            self.processed_image = cv2.flip(self.processed_image, 1)
            self.display_image()

    def display_image(self):
        if self.processed_image is None:
            return

        height, width, channel = self.processed_image.shape
        bytes_per_line = 3 * width
        # QImage 格式转换（BGR888 格式）
        q_img = QImage(self.processed_image.data, width, height, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        # 保持比例自适应显示
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.display_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessor()
    window.show()
    sys.exit(app.exec_())
