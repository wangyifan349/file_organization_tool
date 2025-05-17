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
    query_lower = query.lower()
    for topic, info in data.items():
        if query_lower == topic.lower():
            results.append((100, topic, info))
            continue

        topic_score = fuzz.partial_ratio(query_lower, topic.lower())
        if topic_score > 80:
            results.append((topic_score, topic, info))
            continue

        # 简单检查字符串/列表/字典的内容是否模糊匹配
        def check_content(val):
            if isinstance(val, str):
                return fuzz.partial_ratio(query_lower, val.lower()) > 80
            elif isinstance(val, list):
                for v in val:
                    if check_content(v):
                        return True
            elif isinstance(val, dict):
                for v in val.values():
                    if check_content(v):
                        return True
            return False

        if check_content(info):
            results.append((90, topic, info))

    results.sort(reverse=True, key=lambda x: x[0])
    return results

@app.route('/')
def home():
    query = request.args.get('query', '').strip()
    results = search_data(query) if query else []

    page = """
    <!DOCTYPE html>
    <html lang="zh-cn">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>物理学数据查询系统</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
        <style>
          body.light-mode {
              background-color: #f8f9fa;
              color: #212529;
          }
          body.dark-mode {
              background-color: #121212;
              color: #e0e0e0;
          }
          .dark-mode .card {
              background-color: #1e1e1e;
              color: #e0e0e0;
          }
          .dark-mode .btn-primary {
              background-color: #0d6efd;
              border-color: #0d6efd;
          }
          .nested-list {
              list-style-type: none;
              padding-left: 1rem;
          }
          .nested-list li {
              margin-bottom: 0.3rem;
          }
          .search-results {
              margin-top: 2rem;
          }
          .search-input {
              max-width: 600px;
              width: 100%;
          }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-4">物理学数据查询系统</h1>
            <form id="searchForm" method="get" action="/" class="d-flex justify-content-center mb-3" role="search" aria-label="搜索物理学数据">
                <input type="search" name="query" class="form-control me-2 search-input" placeholder="请输入关键词" value="{{ query }}" required aria-label="搜索输入框" />
                <button type="submit" class="btn btn-primary" id="searchBtn">搜索</button>
                <button type="button" class="btn btn-secondary ms-2" id="toggleMode">切换模式</button>
            </form>

            {% if results %}
                <div class="search-results" tabindex="0" aria-live="polite" aria-atomic="true">
                    <h2>搜索结果：</h2>
                    <div class="row row-cols-1 row-cols-md-3 g-3">
                    {% for score, topic, info in results %}
                        <div class="col">
                            <div class="card h-100 shadow-sm">
                                <div class="card-body">
                                    <h5 class="card-title">{{ topic }}</h5>
                                    <p><small>匹配度: {{ score }}</small></p>
                                    <ul>
                                        {# 遍历info字典，只展开一层 #}
                                        {% for key, value in info.items() %}
                                            <li>
                                                <strong>{{ key }}:</strong>
                                                {# 判断value的类型，进行不同处理 #}
                                                {% if value is string %}
                                                    {{ value }}
                                                {% elif value is iterable %}
                                                    {# 如果是列表或字典，简单展开一次 #}
                                                    <ul>
                                                    {% if value is mapping %}
                                                        {% for subkey, subval in value.items() %}
                                                            <li><strong>{{ subkey }}:</strong> {{ subval }}</li>
                                                        {% endfor %}
                                                    {% else %}
                                                        {% for item in value %}
                                                            <li>{{ item }}</li>
                                                        {% endfor %}
                                                    {% endif %}
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
                </div>
            {% elif query %}
                <div class="alert alert-warning" role="alert">
                    未找到与“{{ query }}”相关的结果。
                </div>
            {% endif %}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // 深色模式开关及记忆
            const toggleBtn = document.getElementById('toggleMode');
            const body = document.body;
            const themeKey = 'physicsDataTheme';

            function applyTheme(theme) {
                if(theme === 'dark') {
                    body.classList.add('dark-mode');
                    body.classList.remove('light-mode');
                    toggleBtn.textContent = '切换到浅色模式';
                } else {
                    body.classList.add('light-mode');
                    body.classList.remove('dark-mode');
                    toggleBtn.textContent = '切换到深色模式';
                }
            }

            // 初始化主题
            const savedTheme = localStorage.getItem(themeKey);
            if(savedTheme) {
                applyTheme(savedTheme);
            } else {
                applyTheme('light');
            }

            toggleBtn.addEventListener('click', () => {
                if(body.classList.contains('dark-mode')) {
                    applyTheme('light');
                    localStorage.setItem(themeKey, 'light');
                } else {
                    applyTheme('dark');
                    localStorage.setItem(themeKey, 'dark');
                }
            });

            // 提交搜索时按钮显示正在加载
            const searchForm = document.getElementById('searchForm');
            const searchBtn = document.getElementById('searchBtn');
            searchForm.addEventListener('submit', () => {
                searchBtn.disabled = true;
                searchBtn.textContent = '搜索中...';
            });

            // 搜索后页面自动滚动到结果区域
            {% if results %}
            window.onload = () => {
                const resSection = document.querySelector('.search-results');
                if(resSection){
                    resSection.focus();
                    resSection.scrollIntoView({behavior: "smooth"});
                }
            };
            {% endif %}
        </script>
    </body>
    </html>
    """

    return render_template_string(page, results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)
