"""这是一个简单的云盘，实现了完整的基本功能"""

import os
import re
import sqlite3
import hashlib
from flask import Flask, request, redirect, url_for, render_template_string, jsonify, send_from_directory, g, session, abort
from werkzeug.utils import secure_filename
from urllib.parse import unquote

# ------------------ 配置和初始化 ------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'          # 上传根目录
app.config['SECRET_KEY'] = 'your_secret_key'     # Flask 密钥
app.config['DATABASE'] = 'app.db'                # 数据库文件
# 确保上传根目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# ------------------ 数据库操作 ------------------
def get_db():
    """获取数据库连接"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db
def query_db(query, args=(), one=False):
    """数据库查询"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
def init_db():
    """初始化数据库，创建 users 表"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()
@app.before_request
def initialize_db():
    """每次请求前初始化数据库（仅首次执行）"""
    if not hasattr(g, 'db_initialized'):
        init_db()
        g.db_initialized = True
@app.teardown_appcontext
def close_connection(exception):
    """请求结束关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
def sha512_hash(password):
    """返回密码的 sha512 哈希值"""
    return hashlib.sha512(password.encode('utf-8')).hexdigest()
# ------------------ 路径和安全管理 ------------------
def clean_filename(filename):
    """
    自定义过滤函数：
    保留中文、字母、数字、下划线、中划线、点
    删除其它特殊字符
    """
    filename = filename.replace(os.path.sep, '')  # 防止目录穿越
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_.-]', '', filename)
    return cleaned

def get_user_base_dir():
    """
    返回当前登录用户的根目录，实际数据存储位置。
    """
    username = session.get('username')
    if not username:
        abort(403)
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.realpath(user_dir)

def safe_join(base, *paths):
    """
    拼接路径，并确保结果在 base 目录下，防止目录穿越
    """
    final_path = os.path.realpath(os.path.join(base, *paths))
    if os.path.commonpath([final_path, base]) != base:
        abort(403)
    return final_path

def get_current_dir():
    """
    根据 URL 参数 path 得到当前用户目录下的实际目录路径，
    默认为空字符串代表根目录
    """
    base = get_user_base_dir()
    raw_path = request.args.get('path', '')
    
    parts = []
    for p in raw_path.split("/"):
        clean_p = clean_filename(p)
        if clean_p.strip() != "":
            parts.append(clean_p)
    
    cur_dir = safe_join(base, *parts)
    return cur_dir, "/".join(parts)  # 返回真实路径与整理后的相对路径

# ------------------ HTML 模板 ------------------
index_html = '''
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>文件管理器</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <h1>欢迎使用文件管理器</h1>
      <hr>
      <div class="mb-2">
        {% if 'username' in session %}
          <p>当前用户：{{ session['username'] }}</p>
          <a href="{{ url_for('file_list') }}" class="btn btn-info">进入文件管理</a>
          <a href="{{ url_for('logout') }}" class="btn btn-danger">退出</a>
        {% else %}
          <a href="{{ url_for('register') }}" class="btn btn-primary">注册</a>
          <a href="{{ url_for('login') }}" class="btn btn-secondary">登录</a>
        {% endif %}
      </div>
    </div>
  </body>
</html>
'''
# ------------------ 注册页面 ------------------
register_html = '''
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>注册</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <h2>注册</h2>
      {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
      {% endif %}
      <form method="POST">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" class="form-control" name="username" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input type="password" class="form-control" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">注册</button>
      </form>
      <p class="mt-3">已有账号？ <a href="{{ url_for('login') }}">点击登录</a></p>
    </div>
  </body>
</html>
'''
# ------------------ 登录页面 ------------------
login_html = '''
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>登录</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  </head>
  <body>
    <div class="container mt-5">
      <h2>登录</h2>
      {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
      {% endif %}
      <form method="POST">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" class="form-control" name="username" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input type="password" class="form-control" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">登录</button>
      </form>
      <p class="mt-3">还没有注册？ <a href="{{ url_for('register') }}">点击注册</a></p>
    </div>
  </body>
</html>
'''
# ------------------ 文件管理页面 ------------------

file_list_html = '''
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>文件管理 - {{ rel_path if rel_path else '根目录' }}</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
      .clickable { cursor: pointer; color: blue; text-decoration: underline; }
      /* Context menu style */
      #context-menu, #blank-context-menu {
        display: none;
        position: absolute;
        z-index: 1000;
        background-color: #f8f9fa;
        border: 1px solid #ccc;
        padding: 5px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        border-radius: 4px;
      }
      #context-menu a, #blank-context-menu a {
        display: block;
        padding: 5px 15px;
        color: #333;
        text-decoration: none;
        white-space: nowrap;
        cursor: pointer;
      }
      #context-menu a:hover, #blank-context-menu a:hover {
        background-color: #e0e0e0;
      }
    </style>
  </head>
  <body>
    <div class="container mt-5">
      <h2>文件管理 - 用户: {{ session['username'] }}</h2>
      <p>当前目录：/{{ rel_path }}</p>
      {% if parent_path is not none %}
        <p><a href="{{ url_for('file_list', path=parent_path) }}" class="btn btn-secondary btn-sm">返回上一级</a></p>
      {% endif %}
      <hr>
      <!-- 留空以供右键 -->
      <div id="file-area" style="min-height: 400px;">
        <!-- 文件夹列表 -->
        <h4>文件夹</h4>
        <ul class="list-group mb-4" id="folder-list">
          {% for d in dirs %}
          <li class="list-group-item clickable" data-name="{{ d }}" data-type="dir">
            <span onclick="enterDir('{{ d }}')">{{ d }}</span>
          </li>
          {% endfor %}
        </ul>
        <!-- 文件列表 -->
        <h4>文件</h4>
        <ul class="list-group" id="file-list">
          {% for f in files %}
          <li class="list-group-item clickable" data-name="{{ f }}" data-type="file">
            <span>{{ f }}</span>
            <a href="{{ url_for('download_file') }}?path={{ rel_path }}&name={{ f }}" class="btn btn-outline-primary btn-sm float-right">下载</a>
          </li>
          {% endfor %}
        </ul>
      </div>
      <a href="{{ url_for('logout') }}" class="btn btn-danger mt-4">退出登录</a>
    </div>

    <!-- Context Menu for Right-click Actions -->
    <div id="context-menu">
      <a href="#" id="rename-item">重命名</a>
      <a href="#" id="delete-item">删除</a>
    </div>

    <!-- Blank Area Context Menu for Folder Creation -->
    <div id="blank-context-menu">
      <a href="#" id="create-folder">创建文件夹</a>
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script>
      // ----------------- JavaScript Section -----------------

      // Current selected item for context menu actions
      var currentItem = null;

      // 进入子目录逻辑
      function enterDir(dirname) {
        var path = "{{ rel_path }}";
        if (path && path.length > 0) {
          path += "/" + dirname;
        } else {
          path = dirname;
        }
        window.location.href = "{{ url_for('file_list') }}" + "?path=" + encodeURIComponent(path);
      }

      // 绑定右键菜单和屏蔽默认右键
      $('.clickable').on('contextmenu', function (e) {
        e.preventDefault();

        currentItem = $(this);

        $('#context-menu')
          .css({
            top: e.pageY + 'px',
            left: e.pageX + 'px'
          })
          .show();

        return false;
      });

      // 点击列表之外时显示创建文件夹菜单
      $('#file-area').on('contextmenu', function (e) {
        if (!$(e.target).closest('.clickable').length) {
          e.preventDefault();

          $('#blank-context-menu')
            .css({
              top: e.pageY + 'px',
              left: e.pageX + 'px'
            })
            .show();

          return false;
        }
      });

      // 点击页面的其他位置时隐藏菜单
      $(document).click(function () {
        $('#context-menu').hide();
        $('#blank-context-menu').hide();
      });

      // 重命名逻辑
      $('#rename-item').click(function () {
        var name = currentItem.data('name');
        var type = currentItem.data('type');
        var newName = prompt("请输入新名称：", name);
        if (newName && newName !== name) {
          $.post("{{ url_for('rename_item') }}", {
            name: name,
            new_name: newName,
            type: type,
            path: "{{ rel_path }}"
          }, function (response) {
            if (response.success) {
              location.reload();
            } else {
              alert("重命名失败：" + (response.error || ""));
            }
          });
        }
      });

      // 删除逻辑
      $('#delete-item').click(function () {
        var name = currentItem.data('name');
        var type = currentItem.data('type');
        if (confirm("确定删除 " + name + " 吗？")) {
          $.post("{{ url_for('delete_item') }}", {
            name: name,
            type: type,
            path: "{{ rel_path }}"
          }, function (response) {
            if (response.success) {
              location.reload();
            } else {
              alert("删除失败：" + (response.error || ""));
            }
          });
        }
      });

      // 创建文件夹逻辑
      $('#create-folder').click(function () {
        var foldername = prompt("请输入文件夹名称：");
        if (foldername) {
          $.post("{{ url_for('new_folder') }}", {
            foldername: foldername,
            path: "{{ rel_path }}"
          }, function (response) {
            if (response.success) {
              location.reload();
            } else {
              alert("创建文件夹失败：" + (response.error || ""));
            }
          });
        }
      });

      // ----------------- End of JavaScript Section -----------------
    </script>
  </body>
</html>
'''
# ------------------ 路由实现 ------------------
@app.route('/')
def home():
    return render_template_string(index_html)
# ------------------ 注册 ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        if not username or not password:
            error = "请输入用户名和密码。"
        else:
            hashed_password = sha512_hash(password)
            db = get_db()
            try:
                db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                db.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = "用户名已存在，请更换用户名。"
    return render_template_string(register_html, error=error)
# ------------------ 登录 ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        hashed_password = sha512_hash(password)
        user = query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password), one=True)
        if user is not None:
            session['username'] = username   # 存储登录信息
            return redirect(url_for('file_list'))
        else:
            error = "用户名或密码错误！"
    return render_template_string(login_html, error=error)
# ------------------ 退出登录 ------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))
# ------------------ 登录保护装饰器 ------------------
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper
# ------------------ 文件列表视图 ------------------
@app.route('/files', methods=['GET'])
@login_required
def file_list():
    cur_dir, rel_path = get_current_dir()
    # 获取当前目录下所有文件和目录
    try:
        entries = os.listdir(cur_dir)
    except FileNotFoundError:
        entries = []
    files = []
    for e in entries:
        if os.path.isfile(os.path.join(cur_dir, e)):
            files.append(e)

    dirs = []
    for e in entries:
        if os.path.isdir(os.path.join(cur_dir, e)):
            dirs.append(e)

    files.sort()
    dirs.sort()

    if rel_path:
        parent = "/".join(rel_path.split("/")[:-1])
    else:
        parent = None
    return render_template_string(file_list_html, files=files, dirs=dirs, rel_path=rel_path, parent_path=parent)
# ------------------ 文件上传 ------------------
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    cur_dir, rel_path = get_current_dir()
    if 'file' not in request.files:
        return "未发现上传文件", 400
    file = request.files.get('file')
    if file.filename == '':
        return "文件名为空", 400
    filename = clean_filename(file.filename)
    if not filename:
        return "文件名不合法", 400
    target = os.path.join(cur_dir, filename)
    file.save(target)
    return redirect(url_for('file_list', path=rel_path))
# ----------------- 文件下载 ------------------
@app.route('/download', methods=['GET'])
@login_required
def download_file():
    rel_path = request.args.get('path', '')
    name = request.args.get('name', '')
    if not name:
        abort(400)
    base = get_user_base_dir()

    parts = []
    for p in rel_path.split("/"):
        clean_p = clean_filename(p)
        if clean_p.strip():
            parts.append(clean_p)

    cur_dir = safe_join(base, *parts)
    filename = clean_filename(name)
    return send_from_directory(cur_dir, filename, as_attachment=True)
# ------------------ 删除文件或文件夹 ------------------
@app.route('/delete_item', methods=['POST'])
@login_required
def delete_item():
    name = request.form.get('name')
    item_type = request.form.get('type')  # file 或 dir
    rel_path = request.form.get('path', '')
    if not name or item_type not in ['file', 'dir']:
        return jsonify(success=False, error="缺少必要参数")
    base = get_user_base_dir()
    parts = []
    for p in rel_path.split("/"):
        clean_p = clean_filename(p)
        if clean_p.strip():
            parts.append(clean_p)
    cur_dir = safe_join(base, *parts)
    target = os.path.join(cur_dir, clean_filename(name))
    if not os.path.exists(target):
        return jsonify(success=False, error="目标不存在")
    try:
        if item_type == 'file' and os.path.isfile(target):
            os.remove(target)
        elif item_type == 'dir' and os.path.isdir(target):
            os.rmdir(target) # 仅删除空文件夹
        else:
            return jsonify(success=False, error="类型不匹配")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))
# ------------------ 重命名文件或文件夹 ------------------
@app.route('/rename_item', methods=['POST'])
@login_required
def rename_item():
    name = request.form.get('name')
    new_name = request.form.get('new_name')
    item_type = request.form.get('type')  # file 或 dir
    rel_path = request.form.get('path', '')
    if not name or not new_name or item_type not in ['file', 'dir']:
        return jsonify(success=False, error="缺少必要参数")
    base = get_user_base_dir()
    parts = []
    for p in rel_path.split("/"):
        clean_p = clean_filename(p)
        if clean_p.strip():
            parts.append(clean_p)
    cur_dir = safe_join(base, *parts)
    src = os.path.join(cur_dir, clean_filename(name))
    dst = os.path.join(cur_dir, clean_filename(new_name))
    if not os.path.exists(src):
        return jsonify(success=False, error="原路径不存在")
    try:
        os.rename(src, dst)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))
# ------------------ 创建文件夹 ------------------
@app.route('/new_folder', methods=['POST'])
@login_required
def new_folder():
    foldername = request.form.get('foldername')
    rel_path = request.form.get('path', '')
    if not foldername:
        return jsonify(success=False, error="未提供文件夹名称")
    foldername = clean_filename(foldername)
    base = get_user_base_dir()

    parts = []
    for p in rel_path.split("/"):
        clean_p = clean_filename(p)
        if clean_p.strip():
            parts.append(clean_p)
    cur_dir = safe_join(base, *parts)
    target = os.path.join(cur_dir, foldername)
    if os.path.exists(target):
        return jsonify(success=False, error="文件夹已存在")
    try:
        os.makedirs(target)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))
# ------------------ 应用启动 ------------------
if __name__ == '__main__':
    app.run(debug=False)
