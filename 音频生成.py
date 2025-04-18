import pyttsx3
from pydub import AudioSegment
import os
def text_to_speech(directory_path):
    # 初始化 pyttsx3 引擎
    engine = pyttsx3.init()
    # 设置语速（默认值通常是 200）
    rate = 150
    # 设置音量（范围从 0.0 到 1.0，1.0 是最大音量）
    volume = 1.0
    # 获取所有可用的声音
    voices = engine.getProperty('voices')
    # 可选：列出所有可用声音
    print("可用的声音列表:")
    for index, voice in enumerate(voices):
        print(f"索引: {index}, 名称: {voice.name}, ID: {voice.id}, 语言: {voice.languages}")
    # 设置使用的声音（例如选择第一个声音）
    selected_voice_index = 0  
    engine.setProperty('voice', voices[selected_voice_index].id)
    # 应用语速和音量设置
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)
    # 遍历指定目录下的每个文件
    for filename in os.listdir(directory_path):
        # 检查文件是否为文本文件
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            # 将文本转换为语音并保存为临时 WAV 文件
            output_wav = file_path.replace('.txt', '.wav')
            engine.save_to_file(text, output_wav)
            engine.runAndWait()
            # 将 WAV 文件转换为 MP3 文件
            output_mp3 = file_path.replace('.txt', '.mp3')
            sound = AudioSegment.from_wav(output_wav)
            sound.export(output_mp3, format='mp3')
            # 删除临时的 WAV 文件
            os.remove(output_wav)
            print(f"保存为 MP3 文件: {output_mp3}")

if __name__ == "__main__":
    while True:
        # 提示用户输入目录路径
        directory_path = input("请输入包含文本文件的目录路径：")
        # 检查目录路径是否有效
        if os.path.isdir(directory_path):
            text_to_speech(directory_path)
            break
        else:
            print("输入的目录路径无效，请重新输入。")
