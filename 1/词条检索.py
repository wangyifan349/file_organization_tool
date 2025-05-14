from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
# 初始化数据库
def initialize_database():
    # 连接到SQLite数据库，如果数据库文件不存在则会创建一个新的
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # 创建表格，存储数据条目信息
    c.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )
    ''')
    # 插入一些初始的词条数据
    entries_data = [
        ("Photosynthesis", "Photosynthesis is the process used by plants..."),
        ("Theory of Relativity", "The theory of relativity is a scientific theory..."),
        ("DNA Structure", "DNA is a molecule composed of two polynucleotide chains...")
    ]
    c.executemany('INSERT OR IGNORE INTO entries (title, content) VALUES (?, ?)', entries_data)
    conn.commit()
    conn.close()


# 查询数据库
def query_database(query, args=(), one=False):
    # 打开数据库连接
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # 执行SQL查询
    cur.execute(query, args)
    # 获取结果
    rv = cur.fetchall()
    conn.close()
    # 返回单个结果或多个结果
    return (rv[0] if rv else None) if one else rv


# 路由：主页，也用作搜索页面
@app.route('/', methods=['GET', 'POST'])
def index():
    # 默认搜索结果为空
    results = []
    if request.method == 'POST':
        # 获取用户输入的搜索关键词
        search_term = request.form['search']
        query = "SELECT * FROM entries WHERE title LIKE ? OR content LIKE ?"
        # 数据库查询，使用通配符进行模糊搜索
        results = query_database(query, ('%' + search_term + '%', '%' + search_term + '%'))
    # 渲染结果到首页模板
    return render_template_string(INDEX_PAGE_TEMPLATE, entries=results)

# 路由：显示具体条目详情
@app.route('/entry/<int:entry_id>')
def entry_detail(entry_id):
    # 查询特定id的条目
    entry = query_database("SELECT * FROM entries WHERE id = ?", (entry_id,), one=True)
    # 如果未找到条目则返回404错误
    if entry is None:
        return "Entry not found!", 404
    # 渲染结果到详细信息模板
    return render_template_string(DETAIL_PAGE_TEMPLATE, entry=entry)

# 首页HTML模板
INDEX_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Entry Search</title>
    <!-- 引入Bootstrap CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { margin-top: 50px; background-color: #f0f0f0; }
        .search-container { max-width: 600px; margin: auto; text-align: center; }
        .result-list { margin-top: 30px; }
        .footer { text-align: center; padding: 20px; margin-top: 20px; background-color: #343a40; color: white; }
    </style>
</head>
<body>
    <div class="search-container">
        <h2 class="mb-4">Data Entry Search</h2>
        <!-- 搜索表单 -->
        <form method="post" class="form-inline justify-content-center">
            <input class="form-control mr-2" type="text" name="search" placeholder="Enter title or content" style="width: 70%;">
            <input class="btn btn-outline-success" type="submit" value="Search">
        </form>
        <div class="result-list mt-3">
            <ul class="list-group">
            {% for entry in entries %}
                <li class="list-group-item">
                    <a href="{{ url_for('entry_detail', entry_id=entry['id']) }}" class="text-info">{{ entry['title'] }}</a>
                </li>
            {% endfor %}
            </ul>
            {% if entries|length == 0 %}
            <div class="alert alert-warning mt-3" role="alert">No results found</div>
            {% endif %}
        </div>
    </div>
    <div class="footer">
        <p>&copy; 2023 Data Entry Search Application</p>
    </div>
    <!-- 引入JS库 -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
'''

# 详细信息HTML模板
DETAIL_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ entry['title'] }}</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { margin-top: 50px; }
    </style>
    <script>
        // 复制到剪贴板
        function copyToClipboard() {
            var content = document.getElementById("entryContent").innerText;
            navigator.clipboard.writeText(content).then(function() {
                alert("Content copied to clipboard!");
            }, function() {
                alert("Failed to copy content.");
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <h2>{{ entry['title'] }}</h2>
        <!-- 条目详细信息 -->
        <div id="entryContent" class="mb-4">{{ entry['content'] }}</div>
        <!-- 复制按钮 -->
        <button onclick="copyToClipboard()" class="btn btn-outline-secondary">Copy Content</button>
        <a href="{{ url_for('index') }}" class="btn btn-primary ml-2">Back to Search</a>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
'''

# 初始化数据库并启动应用程序
if __name__ == '__main__':
    initialize_database()
    app.run(debug=False)
