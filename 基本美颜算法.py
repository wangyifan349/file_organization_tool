import cv2
import dlib
import numpy as np

def smooth_skin_region(image, landmarks):
    """
    对指定面部区域进行磨皮处理.
    :param image: 输入的图像 (BGR格式)
    :param landmarks: 面部特征点的数组（n x 2）
    :return: 磨皮后图像
    """
    # 创建掩膜
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(landmarks), 255)
    # 提取面部区域
    face_region = cv2.bitwise_and(image, image, mask=mask)
    # 磨皮处理 - 使用双边滤波
    smoothed_region = cv2.bilateralFilter(face_region, d=15, sigmaColor=75, sigmaSpace=75)
    # 替换图像中的面部区域
    result_image = image.copy()
    result_image[mask == 255] = smoothed_region[mask == 255]
    return result_image

def whiten_skin(image, landmarks, alpha=1.3):
    """
    对指定面部区域进行美白处理.
    :param image: 输入的图像 (BGR格式)
    :param landmarks: 面部特征点的数组（n x 2）
    :param alpha: 增加亮度的因子
    :return: 美白后图像
    """
    # 创建掩膜
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(landmarks), 255)
    # 提取面部区域
    face_region = cv2.bitwise_and(image, image, mask=mask)
    # 美白处理
    white_face = cv2.convertScaleAbs(face_region, alpha=alpha, beta=0)  # 增加亮度
    # 替换图像中的面部区域
    result_image = image.copy()
    result_image[mask == 255] = white_face[mask == 255]
    return result_image

def slim_face(image, landmarks):
    """
    瘦脸处理：对用户选择的面部区域进行缩放.
    :param image: 输入的图像 (BGR格式)
    :param landmarks: 面部特征点的数组（n x 2）
    :return: 瘦脸后图像
    """
    # 获取面部区域的矩形边界框
    left_eye = landmarks[36:48]  # 左眼部特征
    right_eye = landmarks[42:54]  # 右眼部特征
    mouth_center = (landmarks[48] + landmarks[54]) // 2  # 嘴巴中心点
    # 计算面部区域的相对中心
    face_center = np.mean(np.vstack((left_eye, right_eye, mouth_center)), axis=0).astype(int)
    # 计算面部区域
    face_width = int(np.linalg.norm(left_eye[0] - right_eye[0]) * 1.2)  # 增加宽度比例
    face_height = int(face_width * 1.5)  # 高度与宽度的比例
    # 创建面部区域的矩形框
    x = max(face_center[0] - face_width // 2, 0)
    y = max(face_center[#citation-1](citation-1) - face_height // 2, 0)
    # 瘦脸处理：仿射变换
    face_region = image[y:y + face_height, x:x + face_width]
    slimmed_face = cv2.resize(face_region, (face_width, face_height // 2))
    # 替换原图中的面部区域
    result_image = image.copy()
    result_image[y:y + slimmed_face.shape[0], x:x + slimmed_face.shape[#citation-1](citation-1)] = slimmed_face
    return result_image

def process_image(image_path):
    """
    主处理函数，应用磨皮、美白和瘦脸效果.

    :param image_path: 输入图像的路径
    :return: 处理后的图像
    """
    # 加载图像
    image = cv2.imread(image_path)
    # 转为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 使用dlib获取人脸检测器和形状预测器
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(dlib.example_model_path())
    # 检测人脸
    faces = detector(gray)
    # 处理每个检测到的人脸
    for face in faces:
        # 获取面部特征点
        shape = predictor(gray, face)
        landmarks = np.array([(p.x, p.y) for p in shape.parts()])
        # 磨皮
        image = smooth_skin_region(image, landmarks)
        # 美白
        image = whiten_skin(image, landmarks)
        # 瘦脸
        image = slim_face(image, landmarks)
    return image

# 使用示例
image_path = 'input.jpg'  # 替换为你的图片路径
output_image = process_image(image_path)
# 显示结果
cv2.imshow('Processed Image', output_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
# 保存处理后的图像
cv2.imwrite('output.jpg', output_image)
