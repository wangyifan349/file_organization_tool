# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime
# -----------------------------------------------------------------------------
# 创建Flask应用
app = Flask(__name__)
# 配置应用的密钥和数据库
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'storage/user_uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
# 初始化数据库
db = SQLAlchemy(app)
# -----------------------------------------------------------------------------
# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)
# 文件模型
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(200), nullable=False)  # 新增字段，存储文件的相对路径
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# -----------------------------------------------------------------------------
# 检查文件是否允许上传
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# 获取用户上传目录
def get_user_upload_dir():
    if 'user_id' not in session:
        return None
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(session['user_id']))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir
# -----------------------------------------------------------------------------
# 初始化数据库和上传目录
@app.before_first_request
def initialize():
    db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
# -----------------------------------------------------------------------------
# 登录保护装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
# -----------------------------------------------------------------------------
# 首页重定向到文件页面
@app.route('/')
@login_required
def home():
    return redirect(url_for('files'))
# -----------------------------------------------------------------------------
# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # 检查密码是否一致
        if password != confirm_password:
            flash('两次密码不一致', 'danger')
            return redirect(url_for('register'))
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
        # 检查邮箱是否已注册
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        # 创建新用户
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')
# -----------------------------------------------------------------------------
# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 验证用户
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['user_id'] = user.id
            flash('登录成功', 'success')
            return redirect(url_for('files'))
        else:
            flash('登录失败，请检查用户名和密码', 'danger')
    return render_template('login.html')
# -----------------------------------------------------------------------------
# 注销
@app.route('/logout')
def logout():
    session.clear()
    flash('您已退出登录', 'info')
    return redirect(url_for('login'))
# -----------------------------------------------------------------------------
# 文件管理页面，支持目录层级结构
@app.route('/files', defaults={'path': ''})
@app.route('/files/<path:path>')
@login_required
def files(path):
    # 获取当前用户的文件目录
    user_dir = get_user_upload_dir()
    full_path = os.path.join(user_dir, path)
    if not os.path.exists(full_path):
        flash('目录不存在', 'danger')
        return redirect(url_for('files'))
    # 列出目录中的文件和子目录
    files = []
    directories = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            directories.append(item)
        else:
            files.append(item)
    # 生成面包屑路径
    breadcrumbs = []
    breadcrumbs.append({'name': '首页', 'url': url_for('home')})
    if path:
        parts = path.split('/')
        for i in range(len(parts)):
            part = parts[i]
            breadcrumbs.append({
                'name': part,
                'url': url_for('files', path='/'.join(parts[:i+1]))
            })

    return render_template('files.html', files=files, directories=directories, breadcrumbs=breadcrumbs, current_path=path)
# -----------------------------------------------------------------------------
# 上传文件
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_dir = get_user_upload_dir()
        current_path = request.form.get('current_path', '')
        full_path = os.path.join(user_dir, current_path, filename)
        # 检查文件是否已存在
        if os.path.exists(full_path):
            return jsonify({'error': '文件已存在'}), 400
        # 保存文件
        file.save(full_path)
        new_file = File(filename=filename, filepath=os.path.join(current_path, filename), user_id=session['user_id'])
        db.session.add(new_file)
        db.session.commit()
        return jsonify({
            'id': new_file.id,
            'filename': filename,
            'upload_time': new_file.upload_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'error': '不支持的文件类型'}), 400
# -----------------------------------------------------------------------------
# 下载文件
@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != session['user_id']:
        abort(403)
    user_dir = get_user_upload_dir()
    return send_from_directory(os.path.join(user_dir, os.path.dirname(file.filepath)), os.path.basename(file.filepath), as_attachment=True)
# -----------------------------------------------------------------------------
# 删除文件
@app.route('/delete_file', methods=['DELETE'])
@login_required
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    current_path = data.get('current_path', '')
    user = User.query.get(session['user_id'])
    file = File.query.filter_by(filename=filename, filepath=os.path.join(current_path, filename), user_id=user.id).first()
    if not file:
        return jsonify({'error': '文件不存在'}), 404
    try:
        user_dir = get_user_upload_dir()
        os.remove(os.path.join(user_dir, file.filepath))
        db.session.delete(file)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# -----------------------------------------------------------------------------
# 重命名文件
@app.route('/rename_file', methods=['POST'])
@login_required
def rename_file():
    data = request.get_json()
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    current_path = data.get('current_path', '')
    if not new_name or '.' not in new_name:
        return jsonify({'error': '无效文件名'}), 400
    user = User.query.get(session['user_id'])
    file = File.query.filter_by(filename=old_name, filepath=os.path.join(current_path, old_name), user_id=user.id).first()
    if not file:
        return jsonify({'error': '文件不存在'}), 404
    if File.query.filter_by(filename=new_name, filepath=os.path.join(current_path, new_name), user_id=user.id).first():
        return jsonify({'error': '文件名已存在'}), 400
    try:
        user_dir = get_user_upload_dir()
        os.rename(
            os.path.join(user_dir, file.filepath),
            os.path.join(user_dir, current_path, new_name)
        )
        file.filename = new_name
        file.filepath = os.path.join(current_path, new_name)
        db.session.commit()
        return jsonify({'success': True, 'new_name': new_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# -----------------------------------------------------------------------------
# 运行应用
if __name__ == '__main__':
    app.run(debug=True)





```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件管理系统</title>
    <link href="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .file-operations { max-width: 800px; margin: 20px auto; }
        .rename-input { width: 200px; display: inline-block; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">文件管理系统</a>
            <div class="navbar-nav">
                {% if 'username' in session %}
                <span class="navbar-text me-3">欢迎，{{ session['username'] }}</span>
                <a class="nav-link" href="{{ url_for('logout') }}">退出</a>
                {% else %}
                <a class="nav-link" href="{{ url_for('login') }}">登录</a>
                <a class="nav-link" href="{{ url_for('register') }}">注册</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- 面包屑导航 -->
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                {% for crumb in breadcrumbs %}
                <li class="breadcrumb-item">
                    {% if not loop.last %}
                    <a href="{{ crumb.url }}">{{ crumb.name }}</a>
                    {% else %}
                    {{ crumb.name }}
                    {% endif %}
                </li>
                {% endfor %}
            </ol>
        </nav>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 文件管理页面

```html
<!-- templates/files.html -->
{% extends "base.html" %}

{% block content %}
<div class="file-operations">
    <h2 class="mb-4">文件管理</h2>
    
    <div class="card mb-4">
        <div class="card-body">
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="input-group">
                    <input type="file" class="form-control" id="fileInput" name="file" required>
                    <button type="submit" class="btn btn-success">上传文件</button>
                </div>
                <input type="hidden" name="current_path" value="{{ current_path }}">
                <div class="form-text mt-2">支持格式：{{ ALLOWED_EXTENSIONS | join(', ') }}</div>
            </form>
        </div>
    </div>

    <div class="card">
        <div class="card-body">
            <h5>目录</h5>
            <ul>
                {% for directory in directories %}
                <li><a href="{{ url_for('files', path=current_path + '/' + directory) }}">{{ directory }}</a></li>
                {% endfor %}
            </ul>

            <h5>文件</h5>
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>文件名</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="fileList">
                    {% for file in files %}
                    <tr data-filename="{{ file }}">
                        <td>{{ file }}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
                            <a href="{{ url_for('download_file', file_id=file.id) }}" 
                               class="btn btn-sm btn-outline-success">下载</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

{% block scripts %}
<script>
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);
    formData.append('current_path', document.querySelector('input[name="current_path"]').value);

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const result = await response.json();
        
        if (response.ok) {
            const newRow = `
                <tr data-filename="${result.filename}">
                    <td>${result.filename}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
                        <a href="/download/${result.id}" 
                           class="btn btn-sm btn-outline-success">下载</a>
                    </td>
                </tr>`;
            document.getElementById('fileList').insertAdjacentHTML('afterbegin', newRow);
            document.getElementById('fileInput').value = '';
        } else {
            alert(result.error || '上传失败');
        }
    } catch (error) {
        alert('网络错误');
    }
});

document.getElementById('fileList').addEventListener('click', async (e) => {
    // 删除处理
    if (e.target.classList.contains('delete-btn')) {
        const filename = e.target.closest('tr').dataset.filename;
        const currentPath = document.querySelector('input[name="current_path"]').value;
        if (confirm(`确定要永久删除 ${filename} 吗？`)) {
            try {
                const response = await fetch('/delete_file', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename, current_path: currentPath })
                });
                
                if (response.ok) {
                    e.target.closest('tr').remove();
                } else {
                    const error = await response.json();
                    alert(error.error || '删除失败');
                }
            } catch (error) {
                alert('网络错误');
            }
        }
    }
});
</script>
{% endblock %}
{% endblock %}
```

### 登录页面

```html
<!-- templates/login.html -->
{% extends "base.html" %}

{% block content %}
<div class="file-operations">
    <h2 class="mb-4">用户登录</h2>
    <form method="POST">
        <div class="mb-3">
            <label class="form-label">用户名</label>
            <input type="text" class="form-control" name="username" required>
        </div>
        <div class="mb-3">
            <label class="form-label">密码</label>
            <input type="password" class="form-control" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">登录</button>
    </form>
    <div class="mt-3">
        没有账号？<a href="{{ url_for('register') }}">立即注册</a>
    </div>
</div>
{% endblock %}
```

### 注册页面

```html
<!-- templates/register.html -->
{% extends "base.html" %}

{% block content %}
<div class="file-operations">
    <h2 class="mb-4">用户注册</h2>
    <form method="POST">
        <div class="mb-3">
            <label class="form-label">用户名</label>
            <input type="text" class="form-control" name="username" required>
        </div>
        <div class="mb-3">
            <label class="form-label">邮箱</label>
            <input type="email" class="form-control" name="email" required>
        </div>
        <div class="mb-3">
            <label class="form-label">密码</label>
            <input type="password" class="form-control" name="password" required>
        </div>
        <div class="mb-3">
            <label class="form-label">确认密码</label>
            <input type="password" class="form-control" name="confirm_password" required>
        </div>
        <button type="submit" class="btn btn-primary">注册</button>
    </form>
    <div class="mt-3">
        已有账号？<a href="{{ url_for('login') }}">立即登录</a>
    </div>
</div>
{% endblock %}
```
