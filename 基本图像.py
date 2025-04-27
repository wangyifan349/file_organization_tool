import cv2
import dlib
import numpy as np

# -------------------- 初始化 --------------------
# 加载dlib的面部检测器和特征点预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
# 读取图像
image_path = 'path_to_your_image.jpg'
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# -------------------- 图像处理函数 --------------------
def apply_gaussian_blur(image, kernel_size=(5, 5), sigma=1):
    """应用高斯模糊"""
    return cv2.GaussianBlur(image, kernel_size, sigma)
def apply_median_blur(image, kernel_size=5):
    """应用中值滤波"""
    return cv2.medianBlur(image, kernel_size)
def apply_mean_blur(image, kernel_size=(5, 5)):
    """应用均值滤波"""
    return cv2.blur(image, kernel_size)
# -------------------- 瘦脸函数 --------------------
def slim_face(image, landmarks, intensity=0.15):
    """瘦脸效果"""
    # 定义面部三角区的索引
    left_cheek = [1, 2, 3, 4, 5]
    right_cheek = [11, 12, 13, 14, 15]
    jaw_line = [0, 16]
    # 获取面部特征点
    points = []
    for n in range(68):
        x = landmarks.part(n).x
        y = landmarks.part(n).y
        points.append((x, y))
    # 计算变形
    for i in range(len(left_cheek)):
        x, y = points[left_cheek[i]]
        x_jaw, y_jaw = points[jaw_line[0]]
        dx = (x - x_jaw) * intensity
        dy = (y - y_jaw) * intensity
        points[left_cheek[i]] = (int(x - dx), int(y - dy))

    for i in range(len(right_cheek)):
        x, y = points[right_cheek[i]]
        x_jaw, y_jaw = points[jaw_line[1]]
        dx = (x - x_jaw) * intensity
        dy = (y - y_jaw) * intensity
        points[right_cheek[i]] = (int(x - dx), int(y - dy))

    # 应用仿射变换
    for i in range(len(left_cheek)):
        cv2.line(image, points[left_cheek[i]], points[jaw_line[0]], (0, 255, 0), 1)
    for i in range(len(right_cheek)):
        cv2.line(image, points[right_cheek[i]], points[jaw_line[1]], (0, 255, 0), 1)
    return image
# -------------------- 面部检测和处理 --------------------
# 检测面部
faces = detector(gray)
# 遍历检测到的面部
for face in faces:
    # 获取面部特征点
    landmarks = predictor(gray, face)

    # 应用瘦脸效果
    slimmed_image = slim_face(image.copy(), landmarks)

    # 显示结果图像
    cv2.imshow("Original Image", image)
    cv2.imshow("Slimmed Image", slimmed_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
