"""
pip install flask flask-httpauth werkzeug
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import logging
from flask import Flask, request, send_from_directory, jsonify, render_template_string
from werkzeug.utils import secure_filename
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
# ----------- 配置区 ----------------------------------------------------------
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大文件上传50MB
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
# 认证配置
auth = HTTPBasicAuth()
users = {
    "admin": generate_password_hash("password")  # 实例密码，生产环境请改！
}
# 日志配置
logging.basicConfig(level=logging.INFO)
# ----------- 认证相关 --------------------------------------------------------
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None
# ----------- 工具函数 --------------------------------------------------------
def allowed_file(filename):
    filename_lower = filename.lower()
    if '.' not in filename_lower:
        return False
    ext = filename_lower.rsplit('.', 1)[1]
    return ext in ALLOWED_EXTENSIONS
def safe_join(base, *paths):
    """
    安全拼接路径，防止目录穿越。
    合成路径必须在base目录或其子目录内。
    """
    final_path = os.path.abspath(os.path.join(base, *paths))
    base = os.path.abspath(base)
    if final_path == base or final_path.startswith(base + os.sep):
        return final_path
    raise ValueError("试图访问非法目录")
def list_directory(path):
    """
    递归读取文件夹，返回结构化数据。
    采用简单循环，不使用复杂嵌套或列表推导。
    """
    items = []
    try:
        entries = os.listdir(path)
    except Exception as e:
        logging.warning(f"读取目录失败: {e}")
        return items
    for entry_name in entries:
        entry_path = os.path.join(path, entry_name)
        rel_path = os.path.relpath(entry_path, app.config['UPLOAD_FOLDER']).replace("\\", "/")
        if os.path.isdir(entry_path):
            children = list_directory(entry_path)
            items.append({
                'name': entry_name,
                'path': rel_path,
                'type': 'folder',
                'children': children,
            })
        else:
            items.append({
                'name': entry_name,
                'path': rel_path,
                'type': 'file',
            })
    return items
# ----------- 首页路由 ----------------------------------------------------------
@app.route('/')
@auth.login_required
def index():
    files = list_directory(app.config['UPLOAD_FOLDER'])
    html_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <title>文件管理器</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet" />
    <style>
        body {
            background-color: #f0f2f5;
            min-height: 100vh;
            user-select:none;
        }
        #file-list {
            max-width: 900px;
            margin: 40px auto;
            background: #ffffff;
            padding: 20px 30px;
            border-radius: 0.5rem;
            box-shadow: 0 6px 15px rgb(0 0 0 / 0.1);
        }
        .file-item {
            padding: 10px 14px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            margin-bottom: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            background-color: #fff;
            transition: background-color 0.2s ease-in-out;
        }
        .file-item.folder {
            background-color: #e9f7fe;
            font-weight: 600;
        }
        .file-item:hover {
            background-color: #dbefff;
        }
        .file-name {
            flex-grow: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .folder.drag-over {
            border: 2px dashed #0d6efd !important;
            background-color: #e7f1ff !important;
        }
        ul.custom-ul {
            list-style:none;
            padding-left: 1.4rem;
            margin-bottom:0;
        }
        /* 右键菜单 */
        #context-menu {
            position: absolute;
            z-index: 2000;
            background: #FFFFFF;
            border-radius: 0.375rem;
            box-shadow: 0 2px 12px rgb(0 0 0 / 0.07);
            min-width: 160px;
            user-select:none;
        }
        #context-menu ul {
            padding: 0;
            margin: 0;
            list-style: none;
        }
        #context-menu li {
            padding: 10px 16px;
            cursor: pointer;
            font-weight: 500;
            border-bottom: 1px solid #eee;
            transition: background-color 0.15s;
        }
        #context-menu li:last-child {
            border-bottom: none;
        }
        #context-menu li:hover {
            background-color: #0d6efd;
            color: white;
        }
    </style>
</head>
<body>
    <div id="file-list" role="main" aria-label="文件管理器">
        <h2 class="mb-4">文件管理</h2>
        <!-- 上传表单 -->
        <form id="upload-form" enctype="multipart/form-data" class="row g-3 align-items-end mb-4">
            <div class="col-md-5">
                <label for="upload-file" class="form-label">选择文件</label>
                <input type="file" name="file" id="upload-file" required class="form-control" />
            </div>
            <div class="col-md-5">
                <label for="upload-folder" class="form-label">上传目录（相对于 uploads/，可空）</label>
                <input type="text" id="upload-folder" name="folder" class="form-control" placeholder="如 documents/subdir" />
            </div>
            <div class="col-md-2 d-grid">
                <button type="submit" class="btn btn-primary">上传文件</button>
            </div>
        </form>

        <!-- 文件树展示 -->
        <div id="tree-container" role="tree" tabindex="0" aria-label="文件和文件夹列表" >
        {% macro render_tree(items) %}
            <ul class="custom-ul">
            {% for item in items %}
                <li role="treeitem" aria-expanded="true" class="file-item {% if item.type=='folder' %}folder{% endif %}" 
                    draggable="true" data-path="{{ item.path }}" data-type="{{ item.type }}" tabindex="0">
                    <i class="bi me-3 {% if item.type=='folder' %}bi-folder-fill text-warning{% else %}bi-file-earmark{% endif %} fs-5"></i>
                    <span class="file-name">{{ item.name }}</span>
                    {% if item.type == 'file' %}
                    <a href="{{ url_for('download', filepath=item.path) }}" download class="btn btn-sm btn-outline-success ms-3" title="下载 {{item.name}}">
                        <i class="bi bi-download"></i> 下载
                    </a>
                    {% endif %}
                </li>
                {% if item.type == 'folder' and item.children %}
                    {{ render_tree(item.children) }}
                {% endif %}
            {% endfor %}
            </ul>
        {% endmacro %}
        {{ render_tree(files) }}
        </div>

        <!-- 右键菜单 -->
        <div id="context-menu" style="display:none;" role="menu" aria-hidden="true" tabindex="-1" >
            <ul>
                <li id="ctx-rename" role="menuitem" tabindex="-1">重命名</li>
                <li id="ctx-delete" role="menuitem" tabindex="-1">删除</li>
                <li id="ctx-create-folder" role="menuitem" tabindex="-1">新建文件夹</li>
                <li id="ctx-upload-file" role="menuitem" tabindex="-1">上传文件</li>
            </ul>
        </div>
    </div>

    <!-- Bootstrap JS + jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" crossorigin="anonymous"></script>

    <script>
    $(function(){
        // 当前选中文件/文件夹路径和类型
        let selectedPath = null;
        let selectedType = null;
        const $contextMenu = $('#context-menu');

        // ---------------- 显示右键菜单 -------------------
        function showContextMenu(x, y){
            $contextMenu.css({top: y + 'px', left: x + 'px'}).show();
            $contextMenu.attr('aria-hidden', 'false').focus();
        }
        // ---------------- 隐藏右键菜单 -------------------
        function hideContextMenu(){
            $contextMenu.hide();
            $contextMenu.attr('aria-hidden', 'true');
        }

        // ---------------- 文件项右键点击 -------------------
        $('#tree-container').on('contextmenu', '.file-item', function(e){
            e.preventDefault();
            selectedPath = $(this).data('path');
            selectedType = $(this).data('type');
            showContextMenu(e.pageX, e.pageY);
        });

        // 点击页面空白处隐藏菜单
        $(document).on('click', function(e){
            if (!$(e.target).closest('#context-menu').length){
                hideContextMenu();
            }
        });

        // ----------- 上传表单提交 -------------
        $('#upload-form').on('submit', function(e){
            e.preventDefault();
            const form = this;
            const formData = new FormData(form);
            const folder = $('#upload-folder').val().trim();
            $.ajax({
                url:'/upload?folder=' + encodeURIComponent(folder),
                method:'POST',
                data: formData,
                processData:false,
                contentType:false,
                success: function(res){
                    alert(res.message);
                    if(res.success) location.reload();
                },
                error: function(xhr){
                    alert("上传失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                }
            });
        });

        // ----------- 右键菜单功能函数 --------------

        // 重命名
        $('#ctx-rename').on('click', function(){
            hideContextMenu();
            if(!selectedPath) return alert('请选择文件或文件夹进行重命名');
            const newName = prompt('请输入新名称（不含 / 或 \\）');
            if(!newName) return;
            if(newName.includes('/') || newName.includes('\\')){
                alert('名称不能包含斜杠');
                return;
            }
            $.ajax({
                url:'/rename',
                method:'POST',
                contentType:'application/json',
                data: JSON.stringify({old_path: selectedPath, new_name: newName.trim()}),
                success: function(res){
                    alert(res.message);
                    if(res.success) location.reload();
                },
                error: function(xhr){
                    alert("重命名失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                }
            });
        });

        // 删除
        $('#ctx-delete').on('click', function(){
            hideContextMenu();
            if(!selectedPath) return alert('请选择文件或文件夹进行删除');
            if(!confirm('确认删除选中的文件/文件夹？')) return;
            $.ajax({
                url:'/delete',
                method:'POST',
                contentType:'application/json',
                data: JSON.stringify({path: selectedPath}),
                success: function(res){
                    alert(res.message);
                    if(res.success) location.reload();
                },
                error: function(xhr){
                    alert("删除失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                }
            });
        });

        // 新建文件夹
        $('#ctx-create-folder').on('click', function(){
            hideContextMenu();
            // 创建到当前文件夹内，若选中是文件则放其父目录，未选中就根目录
            let parentPath = '';
            if(selectedType === 'folder'){
                parentPath = selectedPath || '';
            } else if(selectedPath) {
                parentPath = selectedPath.split('/').slice(0, -1).join('/');
            }
            const folderName = prompt('请输入新文件夹名称（不含 / 或 \\）');
            if(!folderName) return;
            if(folderName.includes('/') || folderName.includes('\\')){
                alert('名称不能包含斜杠');
                return;
            }
            $.ajax({
                url:'/create_folder',
                method:'POST',
                contentType:'application/json',
                data: JSON.stringify({parent_path: parentPath, folder_name: folderName.trim()}),
                success: function(res){
                    alert(res.message);
                    if(res.success) location.reload();
                },
                error: function(xhr){
                    alert("新建文件夹失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                }
            });
        });

        // 上传文件（右键菜单）
        $('#ctx-upload-file').on('click', function(){
            hideContextMenu();
            // 动态创建文件输入框触发
            const input = $('<input type="file" />');
            input.on('change', function(){
                if(this.files.length === 0) return;
                const formData = new FormData();
                formData.append('file', this.files[0]);
                let folder = '';
                if(selectedType === 'folder'){
                    folder = selectedPath || '';
                } else if(selectedPath){
                    folder = selectedPath.split('/').slice(0,-1).join('/');
                }
                $.ajax({
                    url: '/upload?folder=' + encodeURIComponent(folder),
                    method: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(res){
                        alert(res.message);
                        if(res.success) location.reload();
                    },
                    error: function(xhr){
                        alert("上传失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                    }
                });
            });
            input.trigger('click');
        });

        // ----------- 拖拽移动 ---------------
        let dragSource = null;

        $('#tree-container').on('dragstart', '.file-item', function(e){
            dragSource = $(this).data('path');
            e.originalEvent.dataTransfer.setData('text/plain', dragSource);
            e.originalEvent.dataTransfer.effectAllowed = 'move';
            $(this).addClass('dragging');
        });

        $('#tree-container').on('dragend', '.file-item', function(e){
            dragSource = null;
            $(this).removeClass('dragging');
            $('.folder').removeClass('drag-over');
        });

        $('#tree-container').on('dragover', '.folder', function(e){
            e.preventDefault();
            $(this).addClass('drag-over');
        });

        $('#tree-container').on('dragleave', '.folder', function(e){
            $(this).removeClass('drag-over');
        });

        $('#tree-container').on('drop', '.folder', function(e){
            e.preventDefault();
            const targetFolder = $(this).data('path');
            const sourcePath = e.originalEvent.dataTransfer.getData('text/plain');
            $(this).removeClass('drag-over');
            if(!dragSource || !targetFolder){
                alert('路径错误，无法完成移动');
                return;
            }
            // 防止移动到自身或子目录，前端简单判断，后端再严格验证
            if(sourcePath === targetFolder || targetFolder.startsWith(sourcePath + '/')){
                alert('不能移动到自身或子目录');
                return;
            }
            $.ajax({
                url: '/move',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({source_path: sourcePath, target_folder: targetFolder}),
                success: function(res){
                    alert(res.message);
                    if(res.success) location.reload();
                },
                error: function(xhr){
                    alert("移动失败：" + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : '未知错误'));
                }
            });
        });
    });
    </script>
</body>
</html>
    '''
    return render_template_string(html_template, files=files)
# ----------- 上传接口 ----------------------------------------------------------
@app.route('/upload', methods=['POST'])
@auth.login_required
def upload():
    """
    文件上传，支持 ?folder= 子目录
    """
    folder = request.args.get('folder', '').replace("\\", "/").strip("/")
    try:
        target_folder = safe_join(app.config['UPLOAD_FOLDER'], folder)
    except ValueError:
        return jsonify({'success': False, 'message': '非法目录路径'}), 400
    if not os.path.exists(target_folder):
        try:
            os.makedirs(target_folder, exist_ok=True)
        except Exception as e:
            logging.error(f"创建目录失败: {e}")
            return jsonify({'success': False, 'message': '创建目录失败'}), 500
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未检测到上传文件'}), 400
    file_obj = request.files['file']
    if not file_obj or file_obj.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    filename_raw = file_obj.filename.replace("/", "").replace("\\", "")
    name_part, ext_part = os.path.splitext(filename_raw)
    name_part_secure = secure_filename(name_part)
    if len(name_part_secure) > 100:
        return jsonify({'success': False, 'message': '文件名过长'}), 400
    filename = name_part_secure + ext_part
    if not allowed_file(filename):
        return jsonify({'success': False, 'message': '不允许的文件类型'}), 400
    save_path = os.path.join(target_folder, filename)
    try:
        file_obj.save(save_path)
        logging.info(f"文件上传: {save_path}")
        return jsonify({'success': True, 'message': '文件上传成功'})
    except Exception as e:
        logging.error(f"保存文件失败: {e}")
        return jsonify({'success': False, 'message': '保存文件失败'}), 500
# ----------- 下载接口 ----------------------------------------------------------
@app.route('/download/<path:filepath>')
@auth.login_required
def download(filepath):
    """
    文件下载接口
    """
    try:
        safe_path = safe_join(app.config['UPLOAD_FOLDER'], filepath)
    except ValueError:
        return "非法路径", 400
    if not os.path.isfile(safe_path):
        return "文件不存在", 404
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        os.path.relpath(safe_path, app.config['UPLOAD_FOLDER']),
        as_attachment=True,
        download_name=os.path.basename(safe_path)
    )
# ----------- 删除接口 ----------------------------------------------------------
@app.route('/delete', methods=['POST'])
@auth.login_required
def delete():
    """
    删除文件或文件夹接口
    """
    data = request.get_json()
    rel_path = data.get('path')
    if not rel_path:
        return jsonify({'success': False, 'message': '未提供删除路径'}), 400
    try:
        abs_path = safe_join(app.config['UPLOAD_FOLDER'], rel_path)
    except ValueError:
        return jsonify({'success': False, 'message': '非法路径'}), 400
    if not os.path.exists(abs_path):
        return jsonify({'success': False, 'message': '目标不存在'}), 404
    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            shutil.rmtree(abs_path)
        logging.info(f"删除成功: {abs_path}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logging.error(f"删除失败: {e}")
        return jsonify({'success': False, 'message': '删除失败'}), 500
# ----------- 重命名接口 --------------------------------------------------------
@app.route('/rename', methods=['POST'])
@auth.login_required
def rename():
    """
    重命名文件或文件夹接口
    """
    data = request.get_json()
    old_path = data.get('old_path')
    new_name = data.get('new_name')
    if not old_path or not new_name:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    try:
        abs_old_path = safe_join(app.config['UPLOAD_FOLDER'], old_path)
    except ValueError:
        return jsonify({'success': False, 'message': '非法路径'}), 400
    if not os.path.exists(abs_old_path):
        return jsonify({'success': False, 'message': '文件或文件夹不存在'}), 404
    new_name = new_name.replace("/", "").replace("\\", "").strip()
    if new_name == '':
        return jsonify({'success': False, 'message': '新名称无效'}), 400
    new_path = os.path.join(os.path.dirname(abs_old_path), new_name)
    if os.path.exists(new_path):
        return jsonify({'success': False, 'message': '目标名称已存在'}), 400
    try:
        os.rename(abs_old_path, new_path)
        logging.info(f"重命名: {abs_old_path} -> {new_path}")
        return jsonify({'success': True, 'message': '重命名成功'})
    except Exception as e:
        logging.error(f"重命名失败: {e}")
        return jsonify({'success': False, 'message': '重命名失败'}), 500
# ----------- 移动接口 ----------------------------------------------------------
@app.route('/move', methods=['POST'])
@auth.login_required
def move():
    """
    移动文件或文件夹接口
    """
    data = request.get_json()
    source_path = data.get('source_path')
    target_folder = data.get('target_folder')
    if not source_path or target_folder is None:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    try:
        abs_source_path = safe_join(app.config['UPLOAD_FOLDER'], source_path)
        abs_target_folder = safe_join(app.config['UPLOAD_FOLDER'], target_folder)
    except ValueError:
        return jsonify({'success': False, 'message': '非法路径'}), 400
    if not os.path.exists(abs_source_path):
        return jsonify({'success': False, 'message': '源文件或文件夹不存在'}), 404
    if not os.path.isdir(abs_target_folder):
        return jsonify({'success': False, 'message': '目标文件夹不存在'}), 404
    norm_source = os.path.normpath(abs_source_path)
    norm_target = os.path.normpath(abs_target_folder)
    if norm_target == norm_source or norm_target.startswith(norm_source + os.sep):
        return jsonify({'success': False, 'message': '不能将目录移动到自身或其子目录'}), 400
    new_path = os.path.join(abs_target_folder, os.path.basename(abs_source_path))
    if os.path.exists(new_path):
        return jsonify({'success': False, 'message': '目标目录已有同名文件或文件夹'}), 400
    try:
        shutil.move(abs_source_path, new_path)
        logging.info(f"移动: {abs_source_path} -> {new_path}")
        return jsonify({'success': True, 'message': '移动成功'})
    except Exception as e:
        logging.error(f"移动失败: {e}")
        return jsonify({'success': False, 'message': '移动失败'}), 500
# ----------- 创建文件夹接口 ----------------------------------------------------
@app.route('/create_folder', methods=['POST'])
@auth.login_required
def create_folder():
    """
    创建新文件夹接口
    """
    data = request.get_json()
    parent_path = data.get('parent_path', '').strip('/')
    new_folder_name = data.get('folder_name', '').strip().replace("/", "").replace("\\", "")
    if new_folder_name == '':
        return jsonify({'success': False, 'message': '请输入有效的文件夹名称'}), 400
    try:
        abs_parent = safe_join(app.config['UPLOAD_FOLDER'], parent_path)
    except ValueError:
        return jsonify({'success': False, 'message': '非法目录路径'}), 400
    if not os.path.isdir(abs_parent):
        return jsonify({'success': False, 'message': '父目录不存在'}), 404
    new_folder_path = os.path.join(abs_parent, new_folder_name)
    if os.path.exists(new_folder_path):
        return jsonify({'success': False, 'message': '文件夹已存在'}), 400
    try:
        os.makedirs(new_folder_path)
        logging.info(f"新建文件夹: {new_folder_path}")
        return jsonify({'success': True, 'message': '文件夹创建成功'})
    except Exception as e:
        logging.error(f"创建文件夹失败: {e}")
        return jsonify({'success': False, 'message': '创建文件夹失败'}), 500
# ----------- 错误处理 ----------------------------------------------------------
@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'message': '上传文件过大'}), 413
# ----------- 启动入口 ----------------------------------------------------------
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
