"""
pip install flask flask-httpauth
python app.py
""""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
from flask import Flask, request, send_from_directory, jsonify, render_template_string
from werkzeug.utils import secure_filename
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
# ----------- 认证配置 -------------
auth = HTTPBasicAuth()
users = {
    "admin": generate_password_hash("password")
}
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None
# -----------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_subpath(candidate, base):
    # 判断 candidate 是否base路径下（避免跳出base目录）
    candidate = os.path.normpath(candidate)
    base = os.path.normpath(base)
    return os.path.commonpath([candidate]) == os.path.commonpath([candidate, base])

def safe_join(base, *paths):
    # 安全合并路径，防止越权
    final_path = os.path.normpath(os.path.join(base, *paths))
    if os.path.commonpath([final_path, base]) != base:
        raise ValueError("试图访问非法目录")
    return final_path

def list_directory(current_path):
    items = []
    try:
        for entry in os.scandir(current_path):
            try:
                relative_path = os.path.relpath(entry.path, UPLOAD_FOLDER).replace("\\", "/")
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
            except Exception:
                # 避免单个文件异常导致整体失败
                continue
    except Exception:
        pass
    return items

# ----------------------------------------------------
@app.route('/')
@auth.login_required
def index():
    file_list = list_directory(UPLOAD_FOLDER)
    html_template = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <title>Flask 文件管理</title>
      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <!-- Bootstrap Icons -->
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
      <style>
        html, body, #file-list {
          height: 100%;
          margin: 0; padding: 0;
          user-select:none;
        }
        body {
          background-color: #f8f9fa;
        }
        #file-list {
          overflow-y: auto;
          padding-bottom: 80px;
        }
        .file-item {
          padding: 8px 12px;
          border: 1px solid #dee2e6;
          border-radius: .25rem;
          margin-bottom: 5px;
          cursor: pointer;
          background-color: white;
          display: flex;
          align-items: center;
          user-select:none;
        }
        .file-item.folder {
          background-color: #e9f7fe;
          font-weight: 600;
        }
        .file-item:hover {
          background-color: #dbefff;
        }
        .context-menu {
          display: none;
          position: absolute;
          z-index: 2000;
          background: #fff;
          border: 1px solid #ccc;
          min-width: 140px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.15);
          border-radius: 0.25rem;
          font-weight: 500;
          user-select:none;
        }
        .context-menu ul {
          padding: 0;
          margin: 0;
          list-style: none;
        }
        .context-menu li {
          padding: 10px 15px;
          cursor: pointer;
          transition: background-color 0.2s ease-in-out;
        }
        .context-menu li:hover {
          background-color: #0d6efd;
          color: white;
        }
        /* 目录树样式 */
        #folder-tree ul {
          padding-left: 1rem;
          list-style-type: none;
          max-height: 400px;
          overflow-y: auto;
        }
        #folder-tree li.folder-node:hover {
          background-color: #0d6efd;
          color: white;
          cursor: pointer;
        }
        #folder-tree li.folder-node.active {
          background-color: #0d6efd;
          color: white;
          font-weight: bold;
        }
        /* 上传表单提示 */
        .form-text {
          font-size: 0.85rem;
          color: #6c757d;
        }
      </style>
    </head>
    <body>
      <div class="container mt-3 mb-5" style="max-width: 900px;">
        <h1 class="mb-4">Flask 文件管理</h1>
        <!-- 上传表单 -->
        <div class="card mb-4 shadow-sm">
          <div class="card-body">
            <form id="upload-form" enctype="multipart/form-data" class="row g-3 align-items-center">
              <div class="col-12 col-md-6">
                <label for="fileInput" class="form-label">选择文件</label>
                <input type="file" class="form-control" name="file" id="fileInput" required>
              </div>
              <div class="col-12 col-md-6">
                <label for="folderInput" class="form-label">上传目录（相对于 uploads/）</label>
                <input type="text" class="form-control" name="folder" id="folderInput" placeholder="例：子目录或 空表示根目录">
                <div class="form-text">支持多级目录：如 subdir/documents</div>
              </div>
              <div class="col-12 text-end">
                <button type="submit" class="btn btn-primary">上传</button>
              </div>
            </form>
          </div>
        </div>

        <!-- 文件列表 -->
        <div id="file-list" tabindex="0" aria-label="文件列表">
          {% macro render_items(items) %}
            <ul class="list-unstyled ps-3">
              {% for item in items %}
                <li>
                  <div class="file-item {% if item.type=='folder' %}folder{% endif %}" tabindex="0" role="listitem" aria-label="{{item.type}} {{item.name}}" data-path="{{ item.path }}" data-type="{{ item.type }}">
                    <i class="bi me-2 {% if item.type=='folder' %}bi-folder-fill text-warning{% else %}bi-file-earmark{% endif %}"></i>
                    <span class="flex-grow-1 text-truncate">{{ item.name }}</span>
                    {% if item.type == 'file' %}
                      <a href="{{ url_for('download', filepath=item.path) }}" class="btn btn-sm btn-outline-success ms-2" title="下载 {{item.name}}">下载</a>
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
          {% if files|length == 0 %}
            <p class="text-muted">空目录，暂无文件</p>
          {% endif %}
        </div>
      </div>

      <!-- 右键菜单（文件夹/文件） -->
      <div id="context-menu" class="context-menu" role="menu" aria-hidden="true">
        <ul class="mb-0">
          <li id="rename" role="menuitem" tabindex="-1">重命名</li>
          <li id="delete" role="menuitem" tabindex="-1">删除</li>
          <li id="move" role="menuitem" tabindex="-1">移动</li>
        </ul>
      </div>

      <!-- 空白处右键菜单（带上传） -->
      <div id="context-menu-blank" class="context-menu" role="menu" aria-hidden="true" style="min-width: 120px;">
        <ul class="mb-0">
          <li id="upload-btn" role="menuitem" tabindex="-1">上传文件</li>
        </ul>
      </div>

      <!-- 移动目标目录选择模态框 -->
      <div class="modal fade" id="moveModal" tabindex="-1" aria-labelledby="moveModalLabel" aria-hidden="true" aria-modal="true" role="dialog">
        <div class="modal-dialog modal-dialog-scrollable modal-sm">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="moveModalLabel">选择目标目录</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
            </div>
            <div class="modal-body">
              <div id="folder-tree" tabindex="0" aria-label="移动目标文件夹列表">
                {% macro render_folder_tree(items) %}
                <ul>
                  {% for item in items if item.type == 'folder' %}
                  <li class="folder-node list-group-item" tabindex="0" data-path="{{ item.path }}">
                    <i class="bi bi-folder-fill me-1 text-warning"></i>{{ item.name }}
                    {% if item.children %}
                      {{ render_folder_tree(item.children) }}
                    {% endif %}
                  </li>
                  {% endfor %}
                </ul>
                {% endmacro %}
                {{ render_folder_tree(files) }}
              </div>
            </div>
            <div class="modal-footer">
              <input type="hidden" id="move-target-path" value="">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button type="button" class="btn btn-primary" id="confirm-move-btn" disabled>确定移动</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传隐藏弹窗(点击空白右键用) -->
      <div class="modal fade" id="uploadModal" tabindex="-1" aria-labelledby="uploadModalLabel" aria-hidden="true" aria-modal="true" role="dialog">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="uploadModalLabel">上传文件</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
            </div>
            <div class="modal-body">
              <form id="uploadModalForm" enctype="multipart/form-data">
                <div class="mb-3">
                  <label for="uploadModalFileInput" class="form-label">选择文件</label>
                  <input type="file" class="form-control" name="file" id="uploadModalFileInput" required>
                </div>
                <div class="mb-3">
                  <label for="uploadModalFolderInput" class="form-label">上传目录（相对于 uploads/）</label>
                  <input type="text" class="form-control" name="folder" id="uploadModalFolderInput" placeholder="例如：subdir/documents">
                  <div class="form-text">为空时上传到根目录</div>
                </div>
                <button type="submit" class="btn btn-primary w-100">上传</button>
              </form>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Bootstrap JS Bundle -->
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  
      <script>
        let selectedPath = "";
        let moveSourcePath = "";
        let moveTargetPath = "";

        const showContextMenu = (menuId, x, y) => {
          $(".context-menu").hide();
          const menu = $(menuId);
          menu.css({ top: y + "px", left: x + "px", display: "block" });
          menu.attr("aria-hidden", "false");
        };

        const hideAllContextMenus = () => {
          $(".context-menu").hide().attr("aria-hidden", "true");
        };

        // 右键点击文件/文件夹，显示对应菜单
        $(document).on("contextmenu", ".file-item", function(e) {
          e.preventDefault();
          selectedPath = $(this).data("path");
          showContextMenu("#context-menu", e.pageX, e.pageY);
        });

        // 右键点击空白区域，显示空白菜单（上传按钮）
        $("#file-list").on("contextmenu", function(e) {
          // 排除点击文件项时触发
          if ($(e.target).closest(".file-item").length === 0) {
            e.preventDefault();
            selectedPath = null;
            showContextMenu("#context-menu-blank", e.pageX, e.pageY);
          }
        });

        // 点击页面任意位置隐藏菜单
        $(document).click(function() {
          hideAllContextMenus();
        });

        // 重命名操作
        $("#rename").click(function() {
          hideAllContextMenus();
          let newName = prompt("请输入新的名称：");
          if (newName) {
            $.ajax({
              url: "/rename",
              type: "POST",
              contentType: "application/json",
              data: JSON.stringify({
                old_path: selectedPath,
                new_name: newName.trim()
              }),
              success: function(response) {
                alert(response.message);
                location.reload();
              },
              error: function(xhr) {
                alert("重命名失败：" + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
              }
            });
          }
        });

        // 删除操作
        $("#delete").click(function() {
          hideAllContextMenus();
          if (!selectedPath) return;
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
                alert("删除失败：" + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
              }
            });
          }
        });

        // 上传按钮(空白处右键菜单)
        $("#upload-btn").click(function() {
          hideAllContextMenus();
          // 打开上传modal，清空输入
          $("#uploadModalFileInput").val("");
          $("#uploadModalFolderInput").val("");
          new bootstrap.Modal(document.getElementById('uploadModal')).show();
        });

        // 上传表单提交（主页面）
        $("#upload-form").submit(function(e) {
          e.preventDefault();
          let formData = new FormData(this);
          let folder = $("#folderInput").val().trim();
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
              alert("上传失败：" + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
            }
          });
        });

        // 上传模态弹窗提交
        $("#uploadModalForm").submit(function(e) {
          e.preventDefault();
          let formData = new FormData(this);
          let folder = $("#uploadModalFolderInput").val().trim();
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
              alert("上传失败：" + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
            }
          });
          let modalEl = document.getElementById('uploadModal');
          bootstrap.Modal.getInstance(modalEl).hide();
        });

        // 移动操作弹窗打开
        $("#move").click(function() {
          hideAllContextMenus();
          moveSourcePath = selectedPath;
          moveTargetPath = "";
          $("#confirm-move-btn").prop("disabled", true);
          $("#folder-tree li.folder-node").removeClass("active");
          new bootstrap.Modal(document.getElementById('moveModal')).show();
        });

        // 目录树点击选择目标目录
        $("#folder-tree").on("click keypress", ".folder-node", function(e) {
          if(e.type === "click" || e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            $("#folder-tree li.folder-node").removeClass("active");
            $(this).addClass("active");
            moveTargetPath = $(this).data("path");
            $("#move-target-path").val(moveTargetPath);
            $("#confirm-move-btn").prop("disabled", false);
          }
        });

        // 确认移动
        $("#confirm-move-btn").click(function() {
          if (!moveTargetPath) {
            alert("请选择目标目录");
            return;
          }
          if (!moveSourcePath) {
            alert("源路径不正确");
            return;
          }
          if (moveSourcePath === moveTargetPath || moveTargetPath.startsWith(moveSourcePath + "/") || moveSourcePath.startsWith(moveTargetPath)) {
            alert("不能将目录移动到其自身或子目录");
            return;
          }
          $.ajax({
            url: "/move",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              source_path: moveSourcePath,
              target_folder: moveTargetPath
            }),
            success: function(response) {
              alert(response.message);
              location.reload();
            },
            error: function(xhr) {
              alert("移动失败：" + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
            }
          });
          let modalEl = document.getElementById('moveModal');
          bootstrap.Modal.getInstance(modalEl).hide();
        });
      </script>
    </body>
    </html>
    '''
    return render_template_string(html_template, files=file_list)

# ----------------------------------------------------
@app.route('/upload', methods=['POST'])
@auth.login_required
def upload():
    folder = request.args.get('folder', '').replace("\\", "/").strip("/")
    try:
        target_folder = safe_join(app.config['UPLOAD_FOLDER'], folder)
    except ValueError:
        return jsonify({'success': False, 'message': '非法目录路径'}), 400

    if not os.path.exists(target_folder):
        try:
            os.makedirs(target_folder)
        except Exception as e:
            return jsonify({'success': False, 'message': f'创建目录失败: {str(e)}'}), 500

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件上传'}), 400

    file_obj = request.files['file']
    if file_obj.filename == '':
        return jsonify({'success': False, 'message': '未选中任何文件'}), 400

    # 保证文件名安全，但允许中文
    filename_raw = file_obj.filename
    # 过滤掉路径分隔符，避免路径穿越
    filename_raw = filename_raw.replace("/", "").replace("\\", "")

    # 只给文件名用secure_filename减少非法字符，不修改中文
    # 先尝试用splitext免得中文被破坏，分离名字和扩展
    name_part, ext_part = os.path.splitext(filename_raw)
    name_part_secure = secure_filename(name_part)
    # 组合回去（ext_part通常带点）
    filename = name_part_secure + ext_part

    if not allowed_file(filename):
        return jsonify({'success': False, 'message': '不允许的文件类型'}), 400

    save_path = os.path.join(target_folder, filename)

    try:
        file_obj.save(save_path)
        return jsonify({'success': True, 'message': '文件上传成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存文件失败: {str(e)}'}), 500

# ----------------------------------------------------
@app.route('/download/<path:filepath>')
@auth.login_required
def download(filepath):
    # 防止目录穿越
    try:
        safe_path = safe_join(app.config['UPLOAD_FOLDER'], filepath)
    except ValueError:
        return "非法路径", 400

    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        return "文件不存在", 404

    # 切换工作目录到上传目录发送
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.relpath(safe_path, app.config['UPLOAD_FOLDER']), as_attachment=True)

# ----------------------------------------------------
@app.route('/delete', methods=['POST'])
@auth.login_required
def delete():
    data = request.get_json()
    rel_path = data.get('path')
    if not rel_path:
        return jsonify({'success': False, 'message': '未提供要删除的路径'}), 400

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
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ----------------------------------------------------
@app.route('/rename', methods=['POST'])
@auth.login_required
def rename():
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

    folder = os.path.dirname(abs_old_path)

    # new_name 只去除路径分隔符，不要完全secure_filename防止中文被替换
    new_name = new_name.replace("/", "").replace("\\", "").strip()
    if not new_name:
        return jsonify({'success': False, 'message': '新名称无效'}), 400

    new_path = os.path.join(folder, new_name)

    # 防止重命名到已有文件
    if os.path.exists(new_path):
        return jsonify({'success': False, 'message': '目标名称已存在'}), 400

    try:
        os.rename(abs_old_path, new_path)
        return jsonify({'success': True, 'message': '重命名成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ----------------------------------------------------
@app.route('/move', methods=['POST'])
@auth.login_required
def move():
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

    if not os.path.exists(abs_target_folder) or not os.path.isdir(abs_target_folder):
        return jsonify({'success': False, 'message': '目标文件夹不存在'}), 404

    abs_source_path_norm = os.path.normpath(abs_source_path)
    abs_target_folder_norm = os.path.normpath(abs_target_folder)
    # 检查不能移动到自身或子目录
    if abs_target_folder_norm == abs_source_path_norm or abs_target_folder_norm.startswith(abs_source_path_norm + os.sep):
        return jsonify({'success': False, 'message': '不能将目录移动到其自身或子目录'}), 400

    new_path = os.path.join(abs_target_folder, os.path.basename(abs_source_path))

    # 目标已有文件或目录，提示失败
    if os.path.exists(new_path):
        return jsonify({'success': False, 'message': '目标目录已有同名文件或文件夹'}), 400
    try:
        shutil.move(abs_source_path, new_path)
        return jsonify({'success': True, 'message': '移动成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
# ----------------------------------------------------
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
