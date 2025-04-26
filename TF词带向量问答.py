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








from flask import Flask, request, jsonify, render_template_string
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
app = Flask(__name__)
# ---------------------- 初始化问答字典 ----------------------
qa_dict = {
    "今天天气怎么样？": "今天天气晴朗，适合外出。",
    "如何使用Python进行数据分析？": (
        "你可以使用以下代码进行数据分析：\n"
        "```python\n"
        "import pandas as pd\n"
        "import numpy as np\n"
        "# 读取数据\n"
        "df = pd.read_csv('data.csv')\n"
        "print(df.head())\n"
        "```\n"
    ),
    "我想学习机器学习，有什么推荐的书吗？": "可以阅读《机器学习实战》这本书。"
}
questions = list(qa_dict.keys())
segmented_questions = [' '.join(jieba.lcut(q)) for q in questions]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(segmented_questions)
# ---------------------- 前端页面模板 ----------------------
html_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>聊天页面</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .chat-container {
            width: 400px;
            background-color: #eef2f3;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 80vh;
        }
        .chat-box {
            flex-grow: 1;
            overflow-y: auto;
            padding: 10px;
            background: #e8eff5;
            border-bottom: 2px solid #ddd;
        }
        .message {
            display: flex;
            margin: 8px;
            padding: 10px;
            border-radius: 15px;
            max-width: 70%;
        }
        .user-message {
            background-color: #9fe8c9;
            align-self: flex-end;
            border-bottom-right-radius: 0;
        }
        .bot-message {
            background-color: #dfe3ea;
            align-self: flex-start;
            border-bottom-left-radius: 0;
            white-space: pre-wrap; /* 保持代码格式 */
        }
        .chat-input {
            display: flex;
            border-top: 2px solid #ddd;
            padding: 10px;
            background: #fff;
        }
        .chat-input input {
            flex: 1;
            padding: 10px;
            margin-right: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            outline: none;
        }
        .chat-input button {
            padding: 12px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .chat-input button:hover {
            background-color: #45a049;
        }
        /* 代码块样式 */
        pre {
            background-color: #f7f7f9;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 10px;
            overflow-x: auto;
        }
        code {
            font-family: 'Courier New', Courier, monospace;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-box" id="chat-box"></div>
        <div class="chat-input">
            <input type="text" id="user-input" placeholder="请输入问题..." autocomplete="off">
            <button onclick="sendMessage()">发送</button>
        </div>
    </div>
    <script>
        // 发送消息并处理回复
        function sendMessage() {
            let userInput = document.getElementById("user-input").value.trim();
            if (userInput === "") return;

            // 添加用户输入到聊天框
            addMessageToChat('user-message', userInput);
            // 清空输入框
            document.getElementById("user-input").value = '';
            // 向后端发送请求
            fetch('/get_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: userInput })
            })
            .then(response => response.json())
            .then(data => {
                // 服务器返回的数据
                let answerContent = data.answer.replace(/```/g, '');
                addMessageToChat('bot-message', answerContent, true);
            });
        }
        // 向聊天框中添加消息
        function addMessageToChat(type, message, isCode) {
            let chatBox = document.getElementById("chat-box");
            let messageElement = document.createElement('div');
            messageElement.className = 'message ' + type;
            if (isCode) {
                messageElement.innerHTML = message.replace(/(\\n|\\t|\\s)/g, ''); // 替换预格式化中的转义字符
                messageElement.innerHTML = `<pre><code>${messageElement.innerHTML}</code></pre>`;
            } else {
                messageElement.textContent = message;
            }
            chatBox.appendChild(messageElement);
            // 滚动聊天框到最底部
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
'''
@app.route('/')
def home():
    # 返回嵌入的HTML页面
    return render_template_string(html_template)



@app.route('/get_answer', methods=['POST'])
def get_answer():
    # 获取JSON数据
    data = request.json
    user_question = data.get('question', '')
    # 分词并向量化用户问题
    user_question_segmented = ' '.join(jieba.lcut(user_question))
    user_tfidf = vectorizer.transform([user_question_segmented])
    # 计算相似度得分
    similarities = cosine_similarity(user_tfidf, tfidf_matrix).flatten()
    # 确定最相似的问题
    best_match_idx = similarities.argmax()
    most_similar_question = questions[best_match_idx]
    most_similar_value = similarities[best_match_idx]
    # 打包结果为JSON格式
    result = {
        'most_similar_question': most_similar_question,
        'answer': qa_dict[most_similar_question],
        'similarity': most_similar_value
    }
    return jsonify(result)
if __name__ == '__main__':
    app.run(debug=True)





