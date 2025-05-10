import os
import Levenshtein

def collect_all_folders(root_dir):
    """
    遍历root_dir及其所有子目录，收集所有文件夹的绝对路径和文件夹名。
    返回：列表，每个元素为 (文件夹名, 绝对路径)
    """
    folders = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # dirpath是当前目录，dirnames 是当前目录下的所有子目录
        for dname in dirnames:
            full_path = os.path.join(dirpath, dname)
            folders.append( (dname, full_path) )
    return folders

def search_by_levenshtein(keyword, folder_list, max_distance=3, max_results=10):
    """
    根据编辑距离，从folder_list中模糊匹配keyword。
    folder_list元组形式：(名字, 路径)
    返回值：按编辑距离排序的匹配结果列表，元素：(距离, 名字, 路径)
    """
    results = []
    for name, path in folder_list:
        dist = Levenshtein.distance(keyword, name)
        if dist <= max_distance:
            results.append( (dist, name, path) )
    results.sort(key=lambda x: x[0])
    return results[:max_results]

def main():
    root_dir = input("请输入你的电视剧根目录路径：").strip()
    if not os.path.isdir(root_dir):
        print(f"路径不存在或不是文件夹：{root_dir}")
        return

    print("正在扫描文件夹，请稍等...")
    folder_list = collect_all_folders(root_dir)
    print(f"扫描完毕，发现 {len(folder_list)} 个子文件夹。")

    while True:
        keyword = input("请输入想要搜索的电视剧名称（输入 exit 退出）：").strip()
        if keyword.lower() == "exit":
            print("程序退出")
            break
        
        matches = search_by_levenshtein(keyword, folder_list)
        if matches:
            print(f"找到 {len(matches)} 个匹配的文件夹：")
            for dist, name, path in matches:
                print(f"  - {name}   (编辑距离: {dist})")
                print(f"    路径: {path}")
        else:
            print("未找到匹配的电视剧文件夹，请尝试修改关键词。")

if __name__ == "__main__":
    main()
