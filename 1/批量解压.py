import os
import zipfile

root_directory = input("请输入要扫描解压的根目录路径：")
output_directory = input("请输入解压目标根目录（不输入则默认解压到zip所在目录）：").strip() or None

for dirpath, dirnames, filenames in os.walk(root_directory):
    for filename in filenames:
        if filename.lower().endswith('.zip'):
            zip_path = os.path.join(dirpath, filename)
            if output_directory:
                rel_path = os.path.relpath(dirpath, root_directory)
                target_dir = os.path.join(output_directory, rel_path, os.path.splitext(filename)[0])
            else:
                target_dir = os.path.join(dirpath, os.path.splitext(filename)[0])

            os.makedirs(target_dir, exist_ok=True)

            print(f'正在解压: {zip_path} 到 {target_dir}')
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            except zipfile.BadZipFile:
                print(f'错误：无法解压坏的zip文件 {zip_path}')

print("解压完成！")
