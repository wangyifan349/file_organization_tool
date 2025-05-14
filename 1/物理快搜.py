from flask import Flask, request, render_template_string
from fuzzywuzzy import fuzz

app = Flask(__name__)

# 数据字典
data = {
    "相对论": {
        "简介": "相对论是阿尔伯特·爱因斯坦发展的理论框架，描述了物理学中的引力和运动。",
        "发表年份": 1905,
        "著名方程": "E=mc^2",
        "分类": {
            "狭义相对论": "主要研究物体在光速附近的运动。",
            "广义相对论": "阐述了引力是时空弯曲的结果。",
        },
    },
    "量子力学": {
        "简介": "量子力学是研究微观粒子行为的物理理论。",
        "关键人物": ["尼尔斯·玻尔", "维尔纳·海森堡", "薛定谔"],
        "著名方程": "薛定谔方程",
        "应用": ["量子计算机", "半导体"],
    },
    "经典力学": {
        "简介": "经典力学是牛顿发展的一套描述宏观物体运动的理论。",
        "关键人物": ["艾萨克·牛顿"],
        "核心原理": "牛顿三大运动定律",
    },
}

def search_data(query):
    results = []
    for topic, info in data.items():
        # 精确匹配
        if query.lower() == topic.lower():
            results.append((100, topic, info))
            continue

        # 模糊匹配
        topic_score = fuzz.partial_ratio(query.lower(), topic.lower())
        if topic_score > 80:
            results.append((topic_score, topic, info))
            continue
        
        # 检查内容匹配
        for key, value in info.items():
            content = ''
            if isinstance(value, str):
                content = value
            elif isinstance(value, list):
                content = ' '.join(value)
            elif isinstance(value, dict):
                content = ' '.join(value.values())
            
            content_score = fuzz.partial_ratio(query.lower(), content.lower())
            if content_score > 80:
                results.append((content_score, topic, info))
                break

    # 根据匹配度排序结果
    results.sort(reverse=True, key=lambda x: x[0])
    return results

@app.route('/')
def home():
    query = request.args.get('query', '')
    results = search_data(query) if query else []

    # HTML模板和内联CSS/JS
    page = """
    <!DOCTYPE html>
    <html lang="zh-cn">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>物理学数据查询系统</title>
        <!-- 引入Bootstrap的CSS样式 -->
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body.light-mode {
                background-color: #f8f9fa;
                color: #212529;
            }
            body.dark-mode {
                background-color: #212529;
                color: #f8f9fa;
            }
            .dark-mode .card {
                background-color: #343a40;
                color: #f8f9fa;
            }
            .dark-mode .list-group-item {
                background-color: #343a40;
                color: #f8f9fa;
            }
            .dark-mode .btn-primary {
                background-color: #007bff;
                border-color: #007bff;
            }
            .dark-mode .btn-secondary {
                background-color: #6c757d;
                border-color: #6c757d;
            }
        </style>
    </head>
    <body class="light-mode">
        <div class="container mt-5">
            <div class="text-center">
                <h1>物理学数据查询系统</h1>
                <form method="get" action="/" class="form-inline justify-content-center my-4">
                    <input type="text" name="query" class="form-control mr-2" placeholder="输入关键词" value="{{ query }}" required>
                    <button type="submit" class="btn btn-primary">搜索</button>
                </form>
                <button class="btn btn-secondary" id="toggleMode">切换模式</button>
            </div>

            {% if results %}
                <h2>搜索结果：</h2>
                <div class="row">
                    {% for score, topic, info in results %}
                        <div class="col-md-4 my-2">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">{{ topic }}</h5>
                                    <ul class="list-group list-group-flush">
                                        {% for key, value in info.items() %}
                                            <li class="list-group-item"><strong>{{ key }}:</strong>
                                                {% if value is iterable and not value|string %}
                                                    <ul>
                                                    {% for subkey, subvalue in value.items() %}
                                                        <li><strong>{{ subkey }}:</strong> {{ subvalue }}</li>
                                                    {% endfor %}
                                                    </ul>
                                                {% else %}
                                                    {{ value }}
                                                {% endif %}
                                            </li>
                                        {% endfor %}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% elif query %}
                <div class="alert alert-warning" role="alert">
                    未找到与“{{ query }}”相关的结果。
                </div>
            {% endif %}
        </div>
        <!-- 引入Bootstrap的JavaScript和jQuery -->
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.0.7/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        <script>
            document.getElementById('toggleMode').addEventListener('click', function() {
                document.body.classList.toggle('dark-mode');
            });
        </script>
    </body>
    </html>
    """

    return render_template_string(page, results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)
