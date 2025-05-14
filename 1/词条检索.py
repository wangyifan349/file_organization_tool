from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import csv
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于闪现消息
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据库
def initialize_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # 使用 FTS5 做全文搜索
    c.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS entries USING fts5(
        title, 
        content
    );
    ''')
    entries_data = [
        ("Photosynthesis", "Photosynthesis is the process used by plants..."),
        ("Theory of Relativity", "The theory of relativity is a scientific theory..."),
        ("DNA Structure", "DNA is a molecule composed of two polynucleotide chains...")
    ]
    c.executemany('INSERT INTO entries (title, content) VALUES (?, ?)', entries_data)
    conn.commit()
    conn.close()

# 查询数据库
def query_database(query, args=(), one=False):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def calculate_similarity(query, text):
    """简单的字符串相似性度量，可以替换成更复杂的算法"""
    query_set = set(query.lower().split())
    text_set = set(text.lower().split())
    intersection = query_set.intersection(text_set)
    union = query_set.union(text_set)
    return len(intersection) / len(union) if union else 0

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        search_term = request.form['search']
        query = "SELECT rowid, * FROM entries WHERE entries MATCH ?"
        entries = query_database(query, (search_term,))
        # 计算每个条目的相似度
        results = [(entry, calculate_similarity(search_term, entry['title'] + " " + entry['content']))
                   for entry in entries]
        # 按相似度排序
        results.sort(key=lambda x: x[#citation-1](citation-1), reverse=True)
        # 返回条目数据，但不包括相似度分数
        results = [entry for entry, sim in results]
    return render_template_string(INDEX_PAGE_TEMPLATE, entries=results)

@app.route('/entry/<int:entry_id>')
def entry_detail(entry_id):
    entry = query_database("SELECT * FROM entries WHERE rowid = ?", (entry_id,), one=True)
    if entry is None:
        return "Entry not found!", 404
    related = query_database("SELECT rowid, title FROM entries WHERE rowid != ? LIMIT 5", (entry_id,))
    return render_template_string(DETAIL_PAGE_TEMPLATE, entry=entry, related_entries=related)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        password = request.form['password']
        if password != 'yourpassword':  # 更改为实际密码
            flash('Incorrect Password!', 'danger')
            return redirect(url_for('upload_file'))
        file = request.files['file']
        filename = file.filename
        # 验证文件类型
        if filename.endswith('.csv'):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            with open(filepath, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    title, content = row
                    execute_insert(title, content)
        elif filename.endswith('.json'):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            with open(filepath) as jsonfile:
                entries = json.load(jsonfile)
                for entry in entries:
                    title = entry.get('title')
                    content = entry.get('content')
                    execute_insert(title, content)
        else:
            flash('Invalid file type! Use .csv or .json', 'danger')
            return redirect(url_for('upload_file'))
        flash('File uploaded and processed successfully!', 'success')
        return redirect(url_for('index'))
    return render_template_string(UPLOAD_PAGE_TEMPLATE)

def execute_insert(title, content):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO entries (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()

INDEX_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Entry Search</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { margin-top: 50px; background-color: #f0f0f0; }
        .search-container { max-width: 600px; margin: auto; text-align: center; }
        .result-list { margin-top: 30px; }
        .footer { text-align: center; padding: 20px; margin-top: 20px; background-color: #343a40; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="search-container">
            <h2 class="mb-4">Data Entry Search</h2>
            <form method="post" class="form-inline justify-content-center">
                <input class="form-control mr-2" type="text" name="search" placeholder="Enter title or content" style="width: 70%;">
                <input class="btn btn-outline-success" type="submit" value="Search">
            </form>
            <div class="result-list mt-3">
                <ul class="list-group">
                {% for entry in entries %}
                    <li class="list-group-item">
                        <a href="{{ url_for('entry_detail', entry_id=entry['rowid']) }}" class="text-info">{{ entry['title'] }}</a>
                    </li>
                {% endfor %}
                </ul>
                {% if entries|length == 0 %}
                <div class="alert alert-warning mt-3" role="alert">No results found</div>
                {% endif %}
            </div>
        </div>
    </div>
    <div class="footer">
        <p>&copy; 2023 Data Entry Search Application</p>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

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
        <div id="entryContent" class="mb-4">{{ entry['content'] }}</div>
        <button onclick="copyToClipboard()" class="btn btn-outline-secondary">Copy Content</button>
        <a href="{{ url_for('index') }}" class="btn btn-primary ml-2">Back to Search</a>
        {% if related_entries %}
        <hr>
        <h5>Related Entries</h5>
        <ul>
        {% for related in related_entries %}
            <li><a href="{{ url_for('entry_detail', entry_id=related['rowid']) }}">{{ related['title'] }}</a></li>
        {% endfor %}
        </ul>
        {% endif %}
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

UPLOAD_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload CSV/JSON</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h2>Upload Entries</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="" method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <input type="password" name="password" class="form-control" placeholder="Enter Password" required>
            </div>
            <div class="mb-3">
                <input type="file" name="file" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Upload</button>
        </form>
        <a href="{{ url_for('index') }}" class="btn btn-secondary mt-3">Back to Search</a>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

if __name__ == '__main__':
    initialize_database()
    app.run(debug=False)
