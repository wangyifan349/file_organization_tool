import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# ---------------------- 初始化问答字典 ----------------------
# 示例问答字典，形式为{问题: 答案}
qa_dict = {
    "今天天气怎么样？": "今天天气晴朗，适合外出。",
    "如何使用Python进行数据分析？": "你可以使用Pandas和NumPy库进行数据分析。",
    "我想学习机器学习，有什么推荐的书吗？": "可以阅读《机器学习实战》这本书。"
}
# 提取问题列表
questions = list(qa_dict.keys())
# ---------------------- 中文分词 ----------------------
# 创建一个空列表来存放分词后的问题
segmented_questions = []
# 对每个问题进行分词
for question in questions:
    # 使用jieba分词，将结果连接成一个以空格分隔的字符串
    segmented_question = ' '.join(jieba.lcut(question))
    segmented_questions.append(segmented_question)
# ---------------------- 计算TF-IDF ----------------------
# 初始化TF-IDF向量化器
vectorizer = TfidfVectorizer()
# 用分词后的问题计算TF-IDF矩阵
tfidf_matrix = vectorizer.fit_transform(segmented_questions)
# ---------------------- 处理用户问题 ----------------------
# 用户输入的问题
user_question = "今天天气如何？"
# 对用户的问题进行分词
user_question_segmented = ' '.join(jieba.lcut(user_question))
# 计算用户问题的TF-IDF向量
user_tfidf = vectorizer.transform([user_question_segmented])
# ---------------------- 计算余弦相似度 ----------------------
# 计算用户问题与问答库每个问题的余弦相似度
similarities = cosine_similarity(user_tfidf, tfidf_matrix).flatten()
# 创建字典存储每个问题的相似度
similarity_dict = {}
# 填充字典，以问题为键，相似度为值
for idx, question in enumerate(questions):
    similarity_dict[question] = similarities[idx]
# 打印所有问题的相似度
print("各问题的相似度：")
for question, similarity in similarity_dict.items():
    print(f"问题: '{question}' - 相似度: {similarity}")
# 找到最相似的问题
most_similar_question = max(similarity_dict, key=similarity_dict.get)
most_similar_value = similarity_dict[most_similar_question]
answer = qa_dict[most_similar_question]
# 打印结果
print(f"\n输入问题: '{user_question}'")
print(f"最相似的问题是：'{most_similar_question}'，相似度为：{most_similar_value}")
print(f"对应的答案是：'{answer}'")
