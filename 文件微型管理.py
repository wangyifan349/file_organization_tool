import os
import shutil
import sqlite3
from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template_string, g
)
from werkzeug.security import generate_password_hash, check_password_hash
# ---------------------------- 初始化和配置 ----------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'
BASE_UPLOAD_FOLDER = 'uploads'
DATABASE = 'users.db'

# 确保上传根目录存在
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
# ---------------------------- 数据库工具函数 ----------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()
# ---------------------------- 用户文件夹获取 ----------------------------
def get_user_folder(username):
    # 返回用户文件根目录路径
    folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    return folder
# ---------------------------- 路由：主页 登录注册 ----------------------------
@app.route('/')
def index():
    auth_html = '''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>登录 / 注册</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script>
            function submitForm(action) {
                const form = document.getElementById('auth-form');
                const url = action === 'login' ? '/login' : '/register';
                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams(new FormData(form))
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        alert(action.toUpperCase() + ' 成功');
                        window.location.href = '/files/' + form.username.value;
                    } else {
                        alert(data.error || '操作失败');
                    }
                })
                .catch(e => console.error(e));
            }
        </script>
    </head>
    <body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="text-center">登录 / 注册</h3>
                        <form id="auth-form">
                            <div class="mb-3">
                                <label>用户名</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>密码</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-primary" onclick="submitForm('login')">登录</button>
                                <button type="button" class="btn btn-success" onclick="submitForm('register')">注册</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    '''
    return render_template_string(auth_html)

# ---------------------------- 路由：注册 ----------------------------
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名或密码不能为空'})

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user:
        return jsonify({'success': False, 'error': '用户名已存在'})

    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
    db.commit()

    # 创建用户文件夹
    os.makedirs(get_user_folder(username), exist_ok=True)

    return jsonify({'success': True})
# ---------------------------- 路由：登录 ----------------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名或密码不能为空'})

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '用户名或密码错误'})
# ---------------------------- 路由：上传文件（加密文件流） ----------------------------
@app.route('/upload/<username>/', defaults={'subpath': ''}, methods=['POST'])
@app.route('/upload/<username>/<path:subpath>', methods=['POST'])
def upload(username, subpath):
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(folder, exist_ok=True)

    save_path = os.path.join(folder, file.filename)
    file.save(save_path)

    return jsonify({'success': True})
# ---------------------------- 路由：文件列表显示 ----------------------------
@app.route('/files/<username>/', defaults={'subpath': ''})
@app.route('/files/<username>/<path:subpath>')
def file_manager(username, subpath):
    folder = os.path.join(get_user_folder(username), subpath)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    entries = os.listdir(folder)

    # 下面不使用列表推导，拼接html字符串实现显示
    list_items = ""
    for name in entries:
        full_path = os.path.join(folder, name)
        if os.path.isdir(full_path):
            list_items += '<li class="directory" data-name="{0}"><a href="/files/{1}/{2}/{0}">{0}/</a></li>'.format(
                name, username, subpath + "/" if subpath else "", )
        else:
            # 下载按钮调用前端解密函数，传用户名，路径，文件名
            list_items += '<li class="file" data-name="{0}"><a href="#" onclick="downloadAndDecrypt(\'{1}\', \'{2}\', \'{0}\');return false;">{0}</a></li>'.format(
                name, username, subpath)

    page_html = '''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8" />
        <title>文件管理 - {{username}}</title>
    </head>
    <body>
        <h2>用户：{{username}} - 目录：{{subpath}}</h2>
        <input type="password" id="encryption-password" placeholder="请输入加密密码" autocomplete="new-password" style="width: 300px; margin-bottom: 10px;">
        <br>
        <input type="file" id="file-upload" />
        <button onclick="uploadFile()">上传加密文件</button>
        <ul>
            ''' + list_items + '''
        </ul>

    <script>
        // 加密函数，返回加密后的整体二进制(buffer)
        async function encryptFile(file, password) {
            const enc = new TextEncoder();
            const salt = window.crypto.getRandomValues(new Uint8Array(16));
            const passwordKey = await window.crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
            const key = await window.crypto.subtle.deriveKey({
                "name": "PBKDF2",
                salt: salt,
                iterations: 100000,
                hash: "SHA-256"
            }, passwordKey, {name: "AES-GCM", length: 256}, false, ["encrypt"]);
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const data = await file.arrayBuffer();
            const encryptedContent = await window.crypto.subtle.encrypt({name: "AES-GCM", iv: iv}, key, data);
            const combined = new Uint8Array(salt.byteLength + iv.byteLength + encryptedContent.byteLength);
            combined.set(salt, 0);
            combined.set(iv, salt.byteLength);
            combined.set(new Uint8Array(encryptedContent), salt.byteLength + iv.byteLength);
            return combined.buffer;
        }

        // 上传加密文件
        async function uploadFile() {
            const fileInput = document.getElementById("file-upload");
            const passwordInput = document.getElementById("encryption-password");
            if(fileInput.files.length === 0) {
                alert("请选择文件！");
                return;
            }
            if(!passwordInput.value) {
                alert("请输入加密密码！");
                return;
            }
            const file = fileInput.files[0];
            const password = passwordInput.value;
            try {
                const encryptedBuffer = await encryptFile(file, password);
                const blob = new Blob([encryptedBuffer], {type:"application/octet-stream"});
                const formData = new FormData();
                formData.append("file", blob, file.name);

                let path = '{{subpath}}';
                if(path) path = encodeURIComponent(path) + '/';
                else path = '';
                const url = "/upload/{{username}}/" + path;

                const response = await fetch(url, {
                    method: "POST",
                    body: formData
                });
                const result = await response.json();
                if(result.success) {
                    alert("上传成功!");
                    location.reload();
                } else {
                    alert(result.error || "上传失败");
                }
            } catch(e) {
                alert("加密或上传失败");
                console.error(e);
            }
        }

        // 解密函数，返回解密后buffer
        async function decryptFile(buffer, password) {
            const salt = buffer.slice(0,16);
            const iv = buffer.slice(16,28);
            const data = buffer.slice(28);
            const enc = new TextEncoder();
            const passwordKey = await window.crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
            const key = await window.crypto.subtle.deriveKey({
                name: "PBKDF2",
                salt: new Uint8Array(salt),
                iterations: 100000,
                hash: "SHA-256"
            }, passwordKey, {name:"AES-GCM", length:256}, false, ["decrypt"]);
            try {
                return await window.crypto.subtle.decrypt({name:"AES-GCM", iv: new Uint8Array(iv)}, key, data);
            } catch(e) {
                throw new Error("解密失败");
            }
        }

        // 下载并解密文件
        async function downloadAndDecrypt(username, subpath, filename) {
            const passwordElem = document.getElementById("encryption-password");
            if(!passwordElem.value) {
                alert("请输入解密密码");
                return;
            }
            const password = passwordElem.value;
            const urlPath = subpath ? encodeURIComponent(subpath) + '/' : '';
            const url = "/download/" + encodeURIComponent(username) + "/" + urlPath + encodeURIComponent(filename);
            try {
                const response = await fetch(url);
                if(!response.ok) {
                    alert("下载失败");
                    return;
                }
                const encryptedBuffer = await response.arrayBuffer();
                const decryptedBuffer = await decryptFile(encryptedBuffer, password);
                const blob = new Blob([decryptedBuffer]);
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch(e) {
                alert(e.message);
                console.error(e);
            }
        }
    </script>

    </body>
    </html>
    '''
    # 渲染模板字符串，传递变量
    return render_template_string(page_html, username=username, subpath=subpath)
# ---------------------------- 路由：下载文件 ----------------------------
@app.route('/download/<username>/<path:subpath>/<filename>')
def download_file(username, subpath, filename):
    folder = os.path.join(get_user_folder(username), subpath)
    return send_from_directory(folder, filename, as_attachment=True)
# ---------------------------- 路由：重命名 ----------------------------
@app.route('/rename/<username>/<path:subpath>', methods=['POST'])
def rename_file(username, subpath):
    old_name = request.json.get('old_name')
    new_name = request.json.get('new_name')
    if not old_name or not new_name:
        return jsonify({'error': '参数不完整'}), 400
    folder = os.path.join(get_user_folder(username), subpath)
    old_path = os.path.join(folder, old_name)
    new_path = os.path.join(folder, new_name)
    if not os.path.exists(old_path):
        return jsonify({'error': '源文件不存在'}), 404
    try:
        os.rename(old_path, new_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ---------------------------- 路由：删除 ----------------------------
@app.route('/delete/<username>/<path:subpath>', methods=['POST'])
def delete_file(username, subpath):
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'error': '缺少文件名'}), 400
    folder = os.path.join(get_user_folder(username), subpath)
    full_path = os.path.join(folder, filename)
    if not os.path.exists(full_path):
        return jsonify({'error': '文件不存在'}), 404
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ---------------------------- 路由：移动 ----------------------------
@app.route('/move/<username>', methods=['POST'])
def move_file(username):
    src_path = request.json.get('src_path')
    dest_path = request.json.get('dest_path')
    if not src_path or not dest_path:
        return jsonify({'error': '路径参数不完整'}), 400
    full_src = os.path.join(BASE_UPLOAD_FOLDER, username, src_path)
    full_dest = os.path.join(BASE_UPLOAD_FOLDER, username, dest_path)
    if not os.path.exists(full_src):
        return jsonify({'error': '源文件不存在'}), 404
    try:
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        shutil.move(full_src, full_dest)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ---------------------------- 主入口 ----------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)








import os
import shutil
import sqlite3
import logging
from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template_string, g
)
from werkzeug.security import generate_password_hash, check_password_hash
# ---------------------------- 初始化和配置 ----------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'
BASE_UPLOAD_FOLDER = 'uploads'
DATABASE = 'users.db'
# 初始化 logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
# 确保上传根目录存在
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
# ---------------------------- 数据库工具函数 ----------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db
def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()
    logger.info('数据库初始化完成')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()
        logger.debug('数据库连接关闭')
# ---------------------------- 用户文件夹获取 ----------------------------
def get_user_folder(username):
    folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    logger.debug(f"获取用户文件夹路径: {folder}")
    return folder
# ---------------------------- 路由：主页 登录注册 ----------------------------
@app.route('/')
def index():
    logger.debug("访问主页")
    auth_html = '''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>登录 / 注册</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script>
            // 页面日志区打印
            function logMessage(msg) {
                const logOutput = document.getElementById('log-output');
                logOutput.textContent += msg + '\\n';
                logOutput.scrollTop = logOutput.scrollHeight;
            }
            function submitForm(action) {
                const form = document.getElementById('auth-form');
                const url = action === 'login' ? '/login' : '/register';
                logMessage('准备执行 ' + action.toUpperCase());
                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams(new FormData(form))
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        alert(action.toUpperCase() + ' 成功');
                        logMessage(action.toUpperCase() + ' 成功，跳转文件管理界面');
                        window.location.href = '/files/' + form.username.value;
                    } else {
                        alert(data.error || '操作失败');
                        logMessage(action.toUpperCase() + ' 失败: ' + (data.error || '未知错误'));
                    }
                })
                .catch(e => {
                    console.error(e);
                    logMessage('异常: ' + e.message || e);
                });
            }
        </script>
    </head>
    <body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="text-center">登录 / 注册</h3>
                        <form id="auth-form">
                            <div class="mb-3">
                                <label>用户名</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>密码</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-primary" onclick="submitForm('login')">登录</button>
                                <button type="button" class="btn btn-success" onclick="submitForm('register')">注册</button>
                            </div>
                        </form>
                        <pre id="log-output" style="height: 120px; overflow-y: scroll; border:1px solid #ccc; margin-top: 10px;"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    '''
    return render_template_string(auth_html)
# ---------------------------- 路由：注册 ----------------------------
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    logger.debug(f"注册请求，用户名: {username}")
    if not username or not password:
        logger.warning("注册失败，用户名或密码为空")
        return jsonify({'success': False, 'error': '用户名或密码不能为空'})
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user:
        logger.warning(f"注册失败，用户名已存在: {username}")
        return jsonify({'success': False, 'error': '用户名已存在'})

    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
    db.commit()
    os.makedirs(get_user_folder(username), exist_ok=True)
    logger.info(f"用户注册成功，目录创建完成: {username}")
    return jsonify({'success': True})
# ---------------------------- 路由：登录 ----------------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    logger.debug(f"登录请求，用户名: {username}")
    if not username or not password:
        logger.warning("登录失败，用户名或密码为空")
        return jsonify({'success': False, 'error': '用户名或密码不能为空'})
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        logger.info(f"用户登录成功: {username}")
        return jsonify({'success': True})
    else:
        logger.warning(f"登录失败，用户名或密码错误: {username}")
        return jsonify({'success': False, 'error': '用户名或密码错误'})
# ---------------------------- 路由：上传文件（加密文件流） ----------------------------
@app.route('/upload/<username>/', defaults={'subpath': ''}, methods=['POST'])
@app.route('/upload/<username>/<path:subpath>', methods=['POST'])
def upload(username, subpath):
    logger.debug(f"上传请求，用户: {username}, 路径: {subpath}")
    if 'file' not in request.files:
        logger.warning("上传失败，没有文件上传")
        return jsonify({'error': '没有文件上传'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.warning("上传失败，文件名为空")
        return jsonify({'error': '文件名为空'}), 400
    folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(folder, exist_ok=True)
    save_path = os.path.join(folder, file.filename)
    try:
        file.save(save_path)
        logger.info(f"文件保存成功: {save_path}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"文件保存失败: {e}")
        return jsonify({'error': str(e)}), 500
# ---------------------------- 路由：文件列表显示 ----------------------------
@app.route('/files/<username>/', defaults={'subpath': ''})
@app.route('/files/<username>/<path:subpath>')
def file_manager(username, subpath):
    logger.debug(f"文件管理访问，用户: {username}, 路径: {subpath}")
    folder = os.path.join(get_user_folder(username), subpath)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    entries = os.listdir(folder)
    list_items = ""
    for name in entries:
        full_path = os.path.join(folder, name)
        if os.path.isdir(full_path):
            list_items += '<li class="directory" data-name="{0}"><a href="/files/{1}/{2}/{0}">{0}/</a></li>'.format(
                name, username, subpath + "/" if subpath else "", )
        else:
            list_items += '<li class="file" data-name="{0}"><a href="#" onclick="downloadAndDecrypt(\'{1}\', \'{2}\', \'{0}\');return false;">{0}</a></li>'.format(
                name, username, subpath)

    page_html = '''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8" />
        <title>文件管理 - {{username}}</title>
    </head>
    <body>
        <h2>用户：{{username}} - 目录：{{subpath}}</h2>
        <input type="password" id="encryption-password" placeholder="请输入加密密码" autocomplete="new-password" style="width: 300px; margin-bottom: 10px;">
        <br>
        <input type="file" id="file-upload" />
        <button onclick="uploadFile()">上传加密文件</button>
        <button onclick="clearLog()">清空日志</button>
        <pre id="log-output" style="height: 150px; overflow-y: scroll; border:1px solid #ccc; margin-top:10px;"></pre>
        <ul>
            ''' + list_items + '''
        </ul>

    <script>
        function logMessage(msg) {
            const logOutput = document.getElementById('log-output');
            logOutput.textContent += msg + '\\n';
            logOutput.scrollTop = logOutput.scrollHeight;
            // 仍打印浏览器控制台
            console.log(msg);
        }
        function clearLog() {
            document.getElementById('log-output').textContent = '';
        }

        async function encryptFile(file, password) {
            logMessage("开始加密文件: " + file.name);
            const enc = new TextEncoder();
            const salt = window.crypto.getRandomValues(new Uint8Array(16));
            const passwordKey = await window.crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
            const key = await window.crypto.subtle.deriveKey({
                "name": "PBKDF2",
                salt: salt,
                iterations: 100000,
                hash: "SHA-256"
            }, passwordKey, {name: "AES-GCM", length: 256}, false, ["encrypt"]);
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const data = await file.arrayBuffer();
            const encryptedContent = await window.crypto.subtle.encrypt({name: "AES-GCM", iv: iv}, key, data);
            const combined = new Uint8Array(salt.byteLength + iv.byteLength + encryptedContent.byteLength);
            combined.set(salt, 0);
            combined.set(iv, salt.byteLength);
            combined.set(new Uint8Array(encryptedContent), salt.byteLength + iv.byteLength);
            logMessage("加密完成: " + file.name);
            return combined.buffer;
        }

        async function uploadFile() {
            const fileInput = document.getElementById("file-upload");
            const passwordInput = document.getElementById("encryption-password");
            if(fileInput.files.length === 0) {
                alert("请选择文件！");
                logMessage("上传失败：未选择文件");
                return;
            }
            if(!passwordInput.value) {
                alert("请输入加密密码！");
                logMessage("上传失败：未输入密码");
                return;
            }
            const file = fileInput.files[0];
            const password = passwordInput.value;
            logMessage("准备上传文件: " + file.name);

            try {
                const encryptedBuffer = await encryptFile(file, password);
                logMessage("开始上传文件: " + file.name);
                const blob = new Blob([encryptedBuffer], {type:"application/octet-stream"});
                const formData = new FormData();
                formData.append("file", blob, file.name);

                let path = '{{subpath}}';
                if(path) path = encodeURIComponent(path) + '/';
                else path = '';
                const url = "/upload/{{username}}/" + path;

                const response = await fetch(url, {
                    method: "POST",
                    body: formData
                });
                const result = await response.json();
                if(result.success) {
                    alert("上传成功!");
                    logMessage("上传成功: " + file.name);
                    location.reload();
                } else {
                    alert(result.error || "上传失败");
                    logMessage("上传失败: " + (result.error || "未知错误"));
                }
            } catch(e) {
                alert("加密或上传失败");
                logMessage("异常: " + (e.message || e));
                console.error(e);
            }
        }

        async function decryptFile(buffer, password) {
            logMessage("开始解密文件");
            const salt = buffer.slice(0,16);
            const iv = buffer.slice(16,28);
            const data = buffer.slice(28);
            const enc = new TextEncoder();
            const passwordKey = await window.crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
            const key = await window.crypto.subtle.deriveKey({
                name: "PBKDF2",
                salt: new Uint8Array(salt),
                iterations: 100000,
                hash: "SHA-256"
            }, passwordKey, {name:"AES-GCM", length:256}, false, ["decrypt"]);
            try {
                const decrypted = await window.crypto.subtle.decrypt({name:"AES-GCM", iv: new Uint8Array(iv)}, key, data);
                logMessage("解密成功");
                return decrypted;
            } catch(e) {
                logMessage("解密失败");
                throw new Error("解密失败");
            }
        }

        async function downloadAndDecrypt(username, subpath, filename) {
            const passwordElem = document.getElementById("encryption-password");
            if(!passwordElem.value) {
                alert("请输入解密密码");
                logMessage("下载失败：未输入解密密码");
                return;
            }
            const password = passwordElem.value;
            const urlPath = subpath ? encodeURIComponent(subpath) + '/' : '';
            const url = "/download/" + encodeURIComponent(username) + "/" + urlPath + encodeURIComponent(filename);

            logMessage("准备下载文件：" + filename);
            try {
                const response = await fetch(url);
                if(!response.ok) {
                    alert("下载失败");
                    logMessage("下载失败，响应码：" + response.status);
                    return;
                }
                const encryptedBuffer = await response.arrayBuffer();
                const decryptedBuffer = await decryptFile(encryptedBuffer, password);
                const blob = new Blob([decryptedBuffer]);
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                link.remove();
                logMessage("下载并解密完成: " + filename);
            } catch(e) {
                alert(e.message);
                logMessage("异常: " + (e.message || e));
                console.error(e);
            }
        }
    </script>

    </body>
    </html>
    '''
    return render_template_string(page_html, username=username, subpath=subpath)
# ---------------------------- 路由：下载文件 ----------------------------
@app.route('/download/<username>/<path:subpath>/<filename>')
def download_file(username, subpath, filename):
    folder = os.path.join(get_user_folder(username), subpath)
    logger.debug(f"下载请求，用户: {username}, 路径: {subpath}, 文件: {filename}")
    if not os.path.exists(os.path.join(folder, filename)):
        logger.warning(f"下载失败，文件不存在: {filename}")
        return jsonify({'error': '文件不存在'}), 404
    return send_from_directory(folder, filename, as_attachment=True)
# ---------------------------- 路由：重命名 ----------------------------
@app.route('/rename/<username>/<path:subpath>', methods=['POST'])
def rename_file(username, subpath):
    old_name = request.json.get('old_name')
    new_name = request.json.get('new_name')
    logger.debug(f"重命名请求，用户: {username}, 路径: {subpath}, {old_name} -> {new_name}")
    if not old_name or not new_name:
        logger.warning("重命名失败，参数不完整")
        return jsonify({'error': '参数不完整'}), 400
    folder = os.path.join(get_user_folder(username), subpath)
    old_path = os.path.join(folder, old_name)
    new_path = os.path.join(folder, new_name)
    if not os.path.exists(old_path):
        logger.warning("重命名失败，源文件不存在")
        return jsonify({'error': '源文件不存在'}), 404
    try:
        os.rename(old_path, new_path)
        logger.info(f"重命名成功: {old_name} -> {new_name}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"重命名失败: {e}")
        return jsonify({'error': str(e)}), 500
# ---------------------------- 路由：删除 ----------------------------
@app.route('/delete/<username>/<path:subpath>', methods=['POST'])
def delete_file(username, subpath):
    filename = request.json.get('filename')
    logger.debug(f"删除请求，用户: {username}, 路径: {subpath}, 文件: {filename}")
    if not filename:
        logger.warning("删除失败，缺少文件名")
        return jsonify({'error': '缺少文件名'}), 400
    folder = os.path.join(get_user_folder(username), subpath)
    full_path = os.path.join(folder, filename)
    if not os.path.exists(full_path):
        logger.warning("删除失败，文件不存在")
        return jsonify({'error': '文件不存在'}), 404
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        logger.info(f"删除成功: {filename}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"删除失败: {e}")
        return jsonify({'error': str(e)}), 500
# ---------------------------- 路由：移动 ----------------------------
@app.route('/move/<username>', methods=['POST'])
def move_file(username):
    src_path = request.json.get('src_path')
    dest_path = request.json.get('dest_path')
    logger.debug(f"移动请求，用户: {username}, 源: {src_path}, 目标: {dest_path}")
    if not src_path or not dest_path:
        logger.warning("移动失败，路径参数不完整")
        return jsonify({'error': '路径参数不完整'}), 400
    full_src = os.path.join(BASE_UPLOAD_FOLDER, username, src_path)
    full_dest = os.path.join(BASE_UPLOAD_FOLDER, username, dest_path)
    if not os.path.exists(full_src):
        logger.warning("移动失败，源文件不存在")
        return jsonify({'error': '源文件不存在'}), 404
    try:
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        shutil.move(full_src, full_dest)
        logger.info(f"移动成功: {src_path} -> {dest_path}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"移动失败: {e}")
        return jsonify({'error': str(e)}), 500
# ---------------------------- 全局异常捕获 ----------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error("服务器发生异常", exc_info=e)
    return jsonify({'error': f'服务器错误: {str(e)}'}), 500
# ---------------------------- 主入口 ----------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)




这是一个调试版本的，不是正式版本
