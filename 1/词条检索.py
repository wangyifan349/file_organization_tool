from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import csv
import json
import os

# 创建 Flask 应用实例
app = Flask(__name__)
# 设置安全密钥（部署时请替换为更安全的密钥）
app.secret_key = 'supersecretkey'

# 上传文件夹路径，不存在时创建
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 数据库文件路径
DB_PATH = 'database.db'

def get_db_connection():
    """
    建立SQLite数据库连接，使用Row类型方便按列名访问
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """
    初始化数据库，创建虚拟表FTS5全文索引表（标题和内容）
    并在首次运行时插入示例数据
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS entries USING fts5(
        title, 
        content
    );
    ''')
    c.execute('SELECT count(*) FROM entries')
    count = c.fetchone()[0]
    if count == 0:
        entries_data = [
            ("Photosynthesis", "Photosynthesis is the process used by plants to convert light energy into chemical energy, which can later be released to fuel the organisms' activities."),
            ("Theory of Relativity", "The theory of relativity is a scientific theory describing the interrelation of time, space, and gravity. It was developed mainly by Albert Einstein."),
            ("DNA Structure", "DNA is a molecule composed of two polynucleotide chains that coil around each other to form a double helix carrying genetic instructions.")
        ]
        c.executemany('INSERT INTO entries (title, content) VALUES (?, ?)', entries_data)
        conn.commit()
    conn.close()

def query_database(query, args=(), one=False):
    """
    执行数据库查询并返回结果
    参数：
    - query: SQL语句
    - args: 绑定参数元组
    - one: 是否只返回一条结果
    返回：
    - 查询结果列表，或单条结果（Row对象）
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows

def execute_insert(title, content):
    """
    插入新的条目数据，包含标题和内容
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO entries (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    主页面及搜索逻辑
    - GET: 显示空搜索界面
    - POST: 接收搜索词，利用FTS5全文索引进行模糊搜索
      使用通配符*实现前缀匹配
    - 显示搜索结果，包含标题和内容片段（高亮匹配词）
    """
    entries = []
    search_term = ''
    if request.method == 'POST':
        search_term = request.form['search'].strip()
        if search_term:
            # 添加*符号实现前缀模糊匹配
            match_pattern = f'{search_term}*'
            # 使用 snippet() 生成内容片段，自动高亮匹配词
            query = '''
            SELECT rowid, title, snippet(entries, 1, '<mark>', '</mark>', '...', 30) AS snippet_content
            FROM entries WHERE entries MATCH ? LIMIT 50
            '''
            entries = query_database(query, (match_pattern,))
    return render_template_string(INDEX_PAGE_TEMPLATE, entries=entries, search=search_term)

@app.route('/entry/<int:entry_id>')
def entry_detail(entry_id):
    """
    详情页，显示条目完整标题与内容
    内容区无边框，自动撑开，适合长文本显示
    不显示相关词条
    """
    entry = query_database('SELECT * FROM entries WHERE rowid = ?', (entry_id,), one=True)
    if not entry:
        return "Entry not found", 404
    return render_template_string(DETAIL_PAGE_TEMPLATE, entry=entry)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """
    上传接口，允许上传CSV或JSON文件导入数据
    请求需密码保护（请修改密码）
    CSV格式要求每行两个字段：title, content
    JSON格式要求是列表字典，每个字典包含title和content字段
    上传后导入数据库并反馈处理结果
    """
    if request.method == 'POST':
        password = request.form['password']
        if password != 'yourpassword':  # 请改成实际密码
            flash('Incorrect password!', 'danger')
            return redirect(url_for('upload_file'))
        file = request.files['file']
        if not file:
            flash('No file uploaded', 'warning')
            return redirect(url_for('upload_file'))
        filename = file.filename.lower()
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        try:
            if filename.endswith('.csv'):
                with open(filepath, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) != 2:
                            continue
                        title = row[0].strip()
                        content = row[1].strip()
                        if title and content:
                            execute_insert(title, content)
            elif filename.endswith('.json'):
                with open(filepath, encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        title = item.get('title', '').strip()
                        content = item.get('content', '').strip()
                        if title and content:
                            execute_insert(title, content)
            else:
                flash('Unsupported file type. Use CSV or JSON.', 'danger')
                return redirect(url_for('upload_file'))
            flash('File uploaded and imported successfully!', 'success')
        except Exception as e:
            flash(f'Error processing file: {e}', 'danger')
        return redirect(url_for('index'))
    return render_template_string(UPLOAD_PAGE_TEMPLATE)

# 首页搜索页面模板
INDEX_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Search Entries</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
<style>
  body {padding-top: 50px; background-color: #f8f9fa;}
  .search-box {max-width: 700px; margin: auto;}
  .result-item {padding: 15px; border-bottom: 1px solid #ddd;}
  mark { background-color:yellow; color: black; }
</style>
</head>
<body>
<div class="container">
  <div class="search-box">
    <h2 class="text-center mb-4">Data Entry Search</h2>
    <form method="post" autocomplete="off" aria-label="Search form">
      <div class="input-group mb-3">
        <input type="text" class="form-control" name="search" placeholder="Enter search term" value="{{search}}" required aria-required="true" />
        <div class="input-group-append">
          <button class="btn btn-primary" type="submit" aria-label="Search button">Search</button>
        </div>
      </div>
    </form>
    <a href="{{ url_for('upload_file') }}" class="btn btn-secondary mb-3">Upload Entries (CSV/JSON)</a>
    {% if entries %}
      <div role="region" aria-live="polite">
        <h5>Results ({{ entries|length }})</h5>
        {% for e in entries %}
          <article class="result-item">
            <a href="{{ url_for('entry_detail', entry_id=e['rowid']) }}"><strong>{{ e['title'] }}</strong></a>
            <p class="mb-0">{{ e['snippet_content']|safe }}</p>
          </article>
        {% endfor %}
      </div>
    {% elif search %}
      <div class="alert alert-warning" role="alert">No results found for "{{search}}".</div>
    {% endif %}
  </div>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# 详情页模板，内容部分无边框，内容区自动撑开，适合显示长文本
DETAIL_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ entry['title'] }}</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
<style>
  body {padding-top: 50px; background-color: #f8f9fa;}
  .container {max-width: 900px;}
  #entryContent {
    white-space: pre-wrap;
    background-color: #fff;
    padding: 25px 30px;
    border: none;
    box-shadow: none;
    margin-bottom: 20px;
    font-size: 1.1em;
    line-height: 1.5em;
    border-radius: 0;
  }
</style>
<script>
function copyContent() {
  const content = document.getElementById('entryContent').innerText;
  navigator.clipboard.writeText(content).then(() => {
    alert('Content copied to clipboard!');
  }).catch(() => {
    alert('Failed to copy content.');
  });
}
</script>
</head>
<body>
<div class="container">
  <h2>{{ entry['title'] }}</h2>
  <div id="entryContent" tabindex="0" aria-label="Entry content">{{ entry['content'] }}</div>
  <button class="btn btn-outline-secondary mt-3" onclick="copyContent()" aria-label="Copy content to clipboard">Copy Content</button>
  <a href="{{ url_for('index') }}" class="btn btn-primary mt-3 ml-2">Back to Search</a>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# 上传界面模板
UPLOAD_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Upload Entries</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
</head>
<body>
<div class="container" style="padding-top:50px; max-width:600px;">
  <h2 class="mb-4">Upload Entries (CSV or JSON)</h2>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  <form action="" method="post" enctype="multipart/form-data" aria-label="Upload form">
    <div class="form-group">
      <input type="password" name="password" class="form-control" placeholder="Enter Password" required aria-required="true" />
    </div>
    <div class="form-group">
      <input type="file" name="file" class="form-control-file" accept=".csv,.json" required aria-required="true" />
    </div>
    <button type="submit" class="btn btn-primary">Upload</button>
    <a href="{{ url_for('index') }}" class="btn btn-secondary ml-2">Back to Search</a>
  </form>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

if __name__ == '__main__':
    # 程序启动时先初始化数据库及示例数据
    initialize_database()
    # 启动Flask服务器，生产环境请使用WSGI服务器代替debug=False
    app.run(debug=False)
