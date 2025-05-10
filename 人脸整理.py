"""
这个程序使用人脸识别技术在给定目录中查找与参考图像相似的人脸，并允许用户选择将这些相似图像复制或移动到指定目录。
This program uses facial recognition technology to find faces similar to a reference image within a given directory and allows the user to copy or move these similar images to a specified directory.
"""
import os
import shutil
import face_recognition
# ----------------- 查找和比较所有面孔 -----------------
def find_and_compare_faces(reference_image_path, directory_path, threshold=0.6):
    # 载入并编码参考图像
    reference_image = face_recognition.load_image_file(reference_image_path)
    # 提取参考图像中的面孔编码
    reference_encodings = face_recognition.face_encodings(reference_image)
    # 检查参考图像中是否检测到面孔
    if not reference_encodings:
        print("在参考图像中未检测到面孔。")
        return []
    # 保存相似图像路径及相似度得分的列表
    all_faces_distances = []
    # 遍历目标目录中的图像文件
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # 过滤掉非图像文件
            if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                continue
            # 获取完整图像路径
            image_path = os.path.join(root, file)
            # 载入当前图像文件
            current_image = face_recognition.load_image_file(image_path)
            # 提取当前图像中的面孔编码
            current_encodings = face_recognition.face_encodings(current_image)
            # 跳过没有检测到面孔的图像
            if not current_encodings:
                print(f"在图像中未检测到面孔: {image_path}，跳过。")
                continue
            # 比较当前图像中的每个面孔编码与参考编码
            for current_encoding in current_encodings:
                for reference_encoding in reference_encodings:
                    # 计算欧式距离
                    distance = face_recognition.face_distance([reference_encoding], current_encoding)[0]
                    # 记录图片和相似度得分
                    all_faces_distances.append((image_path, distance)
                    # 如果距离低于阈值，输出结果
                    if distance < threshold:
                        print(f"在 {image_path} 中找到相似面孔， 相似度得分: {distance}")
    # 按相似度得分对结果排序
    all_faces_distances.sort(key=lambda x: x[#citation-1](citation-1))
    return all_faces_distances
# ----------------- 移动或复制图像到目录 -----------------
def move_or_copy_images_to_directory(image_paths, output_directory, operation='copy'):
    # 如果目标目录不存在，则创建
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # 对每张图像进行移动或复制
    for image_path, _ in image_paths:
        if operation == 'move':
            shutil.move(image_path, output_directory)
            print(f"已移动 {image_path} 到 {output_directory}")
        elif operation == 'copy':
            shutil.copy(image_path, output_directory)
            print(f"已复制 {image_path} 到 {output_directory}")
# ----------------- 示例使用 -----------------
# 参考图像路径
reference_image_path = 'path_to_reference_image.jpg'
# 图像目录路径
directory_path = 'path_to_image_directory'
# 找到相似面孔
similar_faces_data = find_and_compare_faces(reference_image_path, directory_path)
# 打印所有面孔的详细相似度报告
print("\n详细相似度报告（按相似度得分排序）:")
for image_path, score in similar_faces_data:
    print(f"图像: {image_path}, 相似度得分: {score}")
# 如果需要，询问用户是否希望移动或复制这些相似图像
if similar_faces_data:
    action = input("\n您希望复制或移动这些图像吗？（copy/move）：").strip().lower()
    # 确保用户输入正确的操作类型
    if action in ['copy', 'move']:
        output_directory = input("请输入输出目录路径：").strip()
        move_or_copy_images_to_directory(similar_faces_data, output_directory, operation=action)
    else:
        print("无效操作。请重新运行脚本并选择 'copy' 或 'move'。")
