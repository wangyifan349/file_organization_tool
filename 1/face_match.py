#!/usr/bin/env python3
import os
import cv2
import numpy as np
import face_recognition

# 读取图片并转换为rgb格式，如果读取失败返回None
def load_image_rgb(path):
    img = cv2.imread(path)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# ---------- 程序执行开始 ----------
# 1. 输入目标图片路径和数据库目录路径
target_path = input("请输入目标图像路径（单脸）: ").strip()
db_dir = input("请输入数据库图片目录路径: ").strip()
print("加载目标图片中...")
target_img = load_image_rgb(target_path)
if target_img is None:
    print(f"加载目标图片失败: {target_path}")
    exit(1)
# 2. 目标图片检测人脸位置，确保只有一张人脸
target_locs = face_recognition.face_locations(target_img)
if len(target_locs) == 0:
    print("目标图片中无脸!")
    exit(1)
elif len(target_locs) > 1:
    print("目标图片中有多个脸，请确保目标图片只有一张人脸!")
    exit(1)
# 3. 计算目标人脸编码
target_encodings = face_recognition.face_encodings(target_img, target_locs)
if len(target_encodings) == 0:
    print("获取目标编码失败!")
    exit(1)
target_encoding = target_encodings[0]
print("处理数据库目录中的所有图片...")
allowed_ext = ('.jpg', '.jpeg', '.png', '.bmp')
total_images = 0      # 总图片计数
no_face_images = 0    # 无人脸图片计数
results = []          # 结果列表，存储每张图片最接近的脸距离和路径
# 4. 遍历数据库目录，寻找最接近目标人脸的图片
for root, dirs, files in os.walk(db_dir):
    for file in files:
        if not file.lower().endswith(allowed_ext):
            continue
        total_images += 1
        full_path = os.path.join(root, file)
        print(f"处理图片: {full_path}")
        rgb_img = load_image_rgb(full_path)
        if rgb_img is None:
            print("  读取失败，跳过")
            continue
        # 获取所有脸位置
        face_locations = face_recognition.face_locations(rgb_img)
        if len(face_locations) == 0:
            no_face_images += 1
            print("  未检测到人脸，跳过")
            continue
        best_distance = None
        # 对所有检测到的人脸，计算与目标编码的欧氏距离，选最小距离
        for loc in face_locations:
            encodings = face_recognition.face_encodings(rgb_img, [loc])
            if len(encodings) == 0:
                continue
            dist = np.linalg.norm(target_encoding - encodings[0])
            if (best_distance is None) or (dist < best_distance):
                best_distance = dist
        # 距离转换为相似度，距离越小，相似度越高
        similarity = 1 / (1 + best_distance) if best_distance is not None else 0
        results.append({
            'file': full_path,
            'best_distance': best_distance,
            'similarity': similarity
        })
# 5. 输出统计信息
print("\n统计信息:")
print(f"总图片数: {total_images}")
print(f"无脸图片数: {no_face_images}")
print(f"有脸图片数: {total_images - no_face_images}")
if len(results) == 0:
    print("数据库中无有效人脸图片！")
    exit(0)
# 6. 按相似度降序排序
results.sort(key=lambda x: x['similarity'], reverse=True)
# 7. 输出比对结果
print("\n比对结果（按相似度降序排序）:")
for res in results:
    print(f"图片: {res['file']}")
    print(f"  欧氏距离: {res['best_distance']:.4f}")
    print(f"  相似度: {res['similarity']:.4f}")
