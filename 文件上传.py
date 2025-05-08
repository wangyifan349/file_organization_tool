#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from flask import Flask, request, send_from_directory, jsonify, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 设置基础目录和上传目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 定义允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 递归获取目录下的文件和子目录（支持深层目录）
def list_directory(current_path):
    items = []
    for entry in os.scandir(current_path):
        relative_path = os.path.relpath(entry.path, UPLOAD_FOLDER)
        if entry.is_dir():
            items.append({
                'name': entry.name,
                'path': relative_path,
                'type': 'folder',
                'children': list_directory(entry.path)
            })
        else:
            items.append({
                'name': entry.name,
                'path': relative_path,
                'type': 'file'
            })
    return items

# 首页，展示上传窗口及文件列表
@app.route('/')
def index():
    file_list = list_directory(UPLOAD_FOLDER)
    # 使用 render_template_string 内嵌 HTML 模板，部分引用了 Bootstrap 和 jQuery
    html_template = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <title>Flask 文件管理</title>
      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <style>
        .file-item {
          padding: 8px;
          border: 1px solid #dee2e6;
          border-radius: .25rem;
          margin-bottom: 5px;
          cursor: pointer;
        }
        .folder {
          background-color: #e9f7fe;
        }
        .context-menu {
          display: none;
          position: absolute;
          z-index: 2000;
          background: #fff;
          border: 1px solid #ccc;
          min-width: 120px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .context-menu ul {
          padding: 0;
          margin: 0;
          list-style: none;
        }
        .context-menu li {
          padding: 8px 12px;
          cursor: pointer;
        }
        .context-menu li:hover {
          background-color: #f1f1f1;
        }
      </style>
    </head>
    <body>
      <div class="container mt-4">
        <h1 class="mb-4">Flask 文件管理</h1>
        <!-- 上传表单 -->
        <div class="card mb-4">
          <div class="card-body">
            <form id="upload-form" enctype="multipart/form-data">
              <div class="mb-3">
                <label for="fileInput" class="form-label">选择文件</label>
                <input type="file" class="form-control" name="file" id="fileInput" required>
              </div>
              <div class="mb-3">
                <label for="folderInput" class="form-label">上传目录（相对于 uploads/）</label>
                <input type="text" class="form-control" name="folder" id="folderInput" placeholder="例如：subdir/documents">
              </div>
              <button type="submit" class="btn btn-primary">上传</button>
            </form>
          </div>
        </div>
  
        <!-- 文件列表 -->
        <div id="file-list">
          {% macro render_items(items) %}
            <ul class="list-unstyled ps-3">
              {% for item in items %}
                <li>
                  <div class="file-item {% if item.type=='folder' %}folder{% endif %}" data-path="{{ item.path }}" data-type="{{ item.type }}">
                    <span class="me-2">{{ item.name }}</span>
                    {% if item.type == 'file' %}
                      <a href="{{ url_for('download', filepath=item.path) }}" class="btn btn-sm btn-outline-success">下载</a>
                    {% endif %}
                  </div>
                  {% if item.type == 'folder' and item.children %}
                    {{ render_items(item.children) }}
                  {% endif %}
                </li>
              {% endfor %}
            </ul>
          {% endmacro %}
          {{ render_items(files) }}
        </div>
      </div>
  
      <!-- 自定义右键菜单 -->
      <div id="context-menu" class="context-menu">
        <ul class="mb-0">
          <li id="rename">重命名</li>
          <li id="delete">删除</li>
        </ul>
      </div>
  
      <!-- Bootstrap JS Bundle -->
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  
      <script>
        let selectedPath = "";
  
        // 显示自定义右键菜单，绑定右键事件
        $(document).on("contextmenu", ".file-item", function(e) {
          e.preventDefault();
          selectedPath = $(this).data("path");
          $("#context-menu").css({
            top: e.pageY + "px",
            left: e.pageX + "px"
          }).show();
        });
  
        $(document).click(function() {
          $("#context-menu").hide();
        });
  
        // 重命名操作
        $("#rename").click(function() {
          let newName = prompt("请输入新的名称：");
          if (newName) {
            $.ajax({
              url: "/rename",
              type: "POST",
              contentType: "application/json",
              data: JSON.stringify({
                old_path: selectedPath,
                new_name: newName
              }),
              success: function(response) {
                  alert(response.message);
                  location.reload();
              },
              error: function(xhr) {
                  alert("重命名失败：" + xhr.responseJSON.message);
              }
            });
          }
        });
  
        // 删除操作
        $("#delete").click(function() {
          if (confirm("确定删除该文件/文件夹吗？")) {
            $.ajax({
              url: "/delete",
              type: "POST",
              contentType: "application/json",
              data: JSON.stringify({ path: selectedPath }),
              success: function(response) {
                  alert(response.message);
                  location.reload();
              },
              error: function(xhr) {
                  alert("删除失败：" + xhr.responseJSON.message);
              }
            });
          }
        });
  
        // 上传操作
        $("#upload-form").submit(function(e) {
          e.preventDefault();
          let formData = new FormData(this);
          let folder = $("#folderInput").val() || "";
          $.ajax({
            url: "/upload?folder=" + encodeURIComponent(folder),
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
              alert(response.message);
              location.reload();
            },
            error: function(xhr) {
              alert("上传失败：" + xhr.responseJSON.message);
            }
          });
        });
      </script>
    </body>
    </html>
    '''
    return render_template_string(html_template, files=file_list)

# 上传文件，支持上传到指定的深层目录
@app.route('/upload', methods=['POST'])
def upload():
    folder = request.args.get('folder', '')
    target_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件上传'}), 400

    file_obj = request.files['file']
    if file_obj.filename == '':
        return jsonify({'success': False, 'message': '未选中任何文件'}), 400

    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(file_obj.filename)
        file_obj.save(os.path.join(target_folder, filename))
        return jsonify({'success': True, 'message': '文件上传成功'})
    else:
        return jsonify({'success': False, 'message': '不允许的文件类型'}), 400

# 文件下载
@app.route('/download/<path:filepath>')
def download(filepath):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filepath, as_attachment=True)

# 删除文件或文件夹
@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    rel_path = data.get('path')
    if not rel_path:
        return jsonify({'success': False, 'message': '未提供要删除的路径'}), 400

    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    if not os.path.exists(abs_path):
        return jsonify({'success': False, 'message': '目标不存在'}), 404

    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            shutil.rmtree(abs_path)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 重命名文件或文件夹
@app.route('/rename', methods=['POST'])
def rename():
    data = request.get_json()
    old_path = data.get('old_path')
    new_name = data.get('new_name')
    if not old_path or not new_name:
        return jsonify({'success': False, 'message': '参数不完整'}), 400

    abs_old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_path)
    if not os.path.exists(abs_old_path):
        return jsonify({'success': False, 'message': '文件或文件夹不存在'}), 404

    folder = os.path.dirname(abs_old_path)
    abs_new_path = os.path.join(folder, secure_filename(new_name))
    try:
        os.rename(abs_old_path, abs_new_path)
        return jsonify({'success': True, 'message': '重命名成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

