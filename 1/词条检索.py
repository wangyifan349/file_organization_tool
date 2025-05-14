from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

# 初始化数据库
def initialize_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        year INTEGER NOT NULL
    )
    ''')
    # 插入初始数据
    entries_data = [
        ("Photosynthesis", "Process used by plants to convert light energy into chemical energy.", 1779),
        ("Theory of Relativity", "A theory of gravitation developed by Albert Einstein.", 1915),
        ("DNA Structure", "The molecular structure of the DNA double helix.", 1953)
    ]
    c.executemany('INSERT OR IGNORE INTO entries (title, description, year) VALUES (?, ?, ?)', entries_data)
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

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        search_term = request.form['search']
        query = "SELECT * FROM entries WHERE title LIKE ? OR description LIKE ?"
        results = query_database(query, ('%' + search_term + '%', '%' + search_term + '%'))
    return render_template_string(INDEX_PAGE_TEMPLATE, entries=results)

@app.route('/entry/<int:entry_id>')
def entry_detail(entry_id):
    entry = query_database("SELECT * FROM entries WHERE id = ?", (entry_id,), one=True)
    if entry is None:
        return "Entry not found!", 404
    return render_template_string(DETAIL_PAGE_TEMPLATE, entry=entry)

# 首页模板
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
    <div class="search-container">
        <h2 class="mb-4">Data Entry Search</h2>
        <form method="post" class="form-inline justify-content-center">
            <input class="form-control mr-2" type="text" name="search" placeholder="Enter title or description" style="width: 70%;">
            <input class="btn btn-outline-success" type="submit" value="Search">
        </form>
        <div class="result-list mt-3">
            <ul class="list-group">
            {% for entry in entries %}
                <li class="list-group-item">
                    <a href="{{ url_for('entry_detail', entry_id=entry['id']) }}" class="text-info">{{ entry['title'] }} ({{ entry['year'] }})</a>
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
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
'''

# 详细信息页面模板
DETAIL_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ entry['title'] }}</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h2>{{ entry['title'] }}</h2>
        <p>{{ entry['description'] }}</p>
        <p><strong>Year of Significance:</strong> {{ entry['year'] }}</p>
        <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Search</a>
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
    app.run(debug=True)
