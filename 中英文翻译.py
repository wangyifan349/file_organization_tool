from transformers import MarianMTModel, MarianTokenizer
# 指定模型名称（中文到英文）
model_name = "Helsinki-NLP/opus-mt-zh-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)
# 翻译输入句子
input_sentence = "你好，你好吗？"  # 中文输入
translated = model.generate(**tokenizer.prepare_seq2seq_batch(input_sentence, return_tensors="pt"))
translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
print("翻译结果（中文到英文）：", translated_text)  # 输出英文翻译



from transformers import MarianMTModel, MarianTokenizer
# 指定模型名称（英文到中文）
model_name = "Helsinki-NLP/opus-mt-en-zh"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)
# 翻译输入句子
input_sentence = "Hello, how are you?"  # 英文输入
translated = model.generate(**tokenizer.prepare_seq2seq_batch(input_sentence, return_tensors="pt"))
translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
print("翻译结果（英文到中文）：", translated_text)  # 输出中文翻译


