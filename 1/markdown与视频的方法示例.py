#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from flask import Flask, request, abort, send_from_directory, jsonify, redirect, url_for, render_template_string
from werkzeug.utils import secure_filename
import markdown  # pip install markdown

app = Flask(__name__)

# 文件存储根目录（可根据需要修改）
BASE_DIR = os.path.abspath("uploads")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# 配置允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 'doc', 'docx', 'md', 'mp4', 'webm'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
VIDEO_EXTENSIONS = {'mp4', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_abs_path(rel_path):
    safe_rel = os.path.normpath(rel_path)
    abs_path = os.path.join(BASE_DIR, safe_rel)
    if os.path.commonprefix([abs_path, BASE_DIR]) != BASE_DIR:
        abort(403)
    return abs_path

# 主目录 / 文件列表
@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def index(req_path):
    abs_path = get_abs_path(req_path)
    if not os.path.exists(abs_path):
        abort(404)
    if os.path.isfile(abs_path):
        # 文件直接下载
        return send_from_directory(directory=os.path.dirname(abs_path),
                                   filename=os.path.basename(abs_path),
                                   as_attachment=True)
    files = []
    for filename in os.listdir(abs_path):
        file_abs = os.path.join(abs_path, filename)
        files.append({
            "name": filename,
            "is_dir": os.path.isdir(file_abs)
        })
    parent_path = os.path.relpath(os.path.join(abs_path, ".."), BASE_DIR) if abs_path != BASE_DIR else ""
    if parent_path == ".":
        parent_path = ""
    return render_template_string(TEMPLATE, files=files, current_path=req_path, parent_path=parent_path)

# 文件上传
@app.route("/upload/<path:current_path>", methods=["POST"])
def upload(current_path):
    abs_path = get_abs_path(current_path)
    if "file" not in request.files:
        return redirect(f"/{current_path}")
    file = request.files["file"]
    if file.filename == "":
        return redirect(f"/{current_path}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(abs_path, filename))
    return redirect(f"/{current_path}")

# 建立目录（POST 表单方式）
@app.route("/mkdir/<path:current_path>", methods=["POST"])
def mkdir(current_path):
    abs_path = get_abs_path(current_path)
    dirname = request.form.get("dirname", "").strip()
    if dirname:
        new_dir = os.path.join(abs_path, secure_filename(dirname))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
    return redirect(f"/{current_path}")

# 建立目录（ajax方式）
@app.route("/mkdir_ajax", methods=["POST"])
def mkdir_ajax():
    data = request.get_json()
    if not data or "parent_path" not in data or "dirname" not in data:
        return jsonify({"success": False, "message": "参数错误"}), 400
    parent_rel = data["parent_path"]
    dirname = data["dirname"].strip()
    if not dirname:
        return jsonify({"success": False, "message": "目录名称不能为空"}), 400
    abs_parent = get_abs_path(parent_rel)
    new_dir = os.path.join(abs_parent, secure_filename(dirname))
    if os.path.exists(new_dir):
        return jsonify({"success": False, "message": "目录已存在"}), 400
    try:
        os.makedirs(new_dir)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 删除文件/目录（ajax）
@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    if not data or "path" not in data:
        return jsonify({"success": False, "message": "参数错误"}), 400
    rel_path = data["path"]
    abs_path = get_abs_path(rel_path)
    if not os.path.exists(abs_path):
        return jsonify({"success": False, "message": "文件不存在"}), 404
    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            shutil.rmtree(abs_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 重命名（ajax）
@app.route("/rename", methods=["POST"])
def rename():
    data = request.get_json()
    if not data or "old_path" not in data or "new_name" not in data:
        return jsonify({"success": False, "message": "参数错误"}), 400
    old_rel = data["old_path"]
    new_name = secure_filename(data["new_name"].strip())
    if not new_name:
        return jsonify({"success": False, "message": "新名称不能为空"}), 400
    old_abs = get_abs_path(old_rel)
    if not os.path.exists(old_abs):
        return jsonify({"success": False, "message": "原文件不存在"}), 404
    new_abs = os.path.join(os.path.dirname(old_abs), new_name)
    if os.path.exists(new_abs):
        return jsonify({"success": False, "message": "目标名称已存在"}), 400
    try:
        os.rename(old_abs, new_abs)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 移动（拖拽 ajax）
@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    if not data or "source" not in data or "destination" not in data:
        return jsonify({"success": False, "message": "参数错误"}), 400
    source_rel = data["source"]
    destination_rel = data["destination"]
    source_abs = get_abs_path(source_rel)
    dest_abs = get_abs_path(destination_rel)
    if not os.path.exists(source_abs):
        return jsonify({"success": False, "message": "源文件不存在"}), 404
    if not os.path.isdir(dest_abs):
        return jsonify({"success": False, "message": "目标不是文件夹"}), 400
    new_abs = os.path.join(dest_abs, os.path.basename(source_abs))
    if os.path.exists(new_abs):
        return jsonify({"success": False, "message": "目标已存在同名文件/文件夹"}), 400
    try:
        os.rename(source_abs, new_abs)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 在线预览与编辑
@app.route("/view/<path:req_path>", methods=["GET", "POST"])
def view(req_path):
    abs_path = get_abs_path(req_path)
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        abort(404)
    ext = os.path.splitext(abs_path)[1].lower()[1:]
    content = ""
    if request.method == "POST":
        new_content = request.form.get("content", "")
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return redirect(url_for("index", req_path=os.path.dirname(req_path)))
        except Exception as e:
            return f"保存失败: {str(e)}", 500
    else:
        if ext in IMAGE_EXTENSIONS:
            return render_template_string(PREVIEW_IMAGE_TEMPLATE,
                                          file_url=url_for("download_file", req_path=req_path),
                                          current_path=req_path)
        elif ext in VIDEO_EXTENSIONS:
            return render_template_string(PREVIEW_VIDEO_TEMPLATE,
                                          file_url=url_for("download_file", req_path=req_path),
                                          current_path=req_path)
        elif ext in {"txt", "md", "json", "py", "log"}:
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"读取文件失败: {str(e)}"
            if ext == "md":
                html_content = markdown.markdown(content)
                return render_template_string(PREVIEW_MD_TEMPLATE,
                                              content=content,
                                              html_content=html_content,
                                              current_path=req_path)
            else:
                return render_template_string(PREVIEW_EDITOR_TEMPLATE,
                                              content=content,
                                              current_path=req_path)
        else:
            return redirect(url_for("download_file", req_path=req_path))

# 文件下载路由
@app.route("/download/<path:req_path>")
def download_file(req_path):
    abs_path = get_abs_path(req_path)
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        abort(404)
    return send_from_directory(directory=os.path.dirname(abs_path),
                               filename=os.path.basename(abs_path),
                               as_attachment=True)

# HTML 模板：文件列表页面
TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>文件管理器</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
  <style>
    #context-menu {
      position: absolute;
      z-index: 1000;
      display: none;
      background: #fff;
      border: 1px solid #ccc;
      min-width: 150px;
      box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    }
    #context-menu ul {
      list-style: none;
      padding: 5px 0;
      margin: 0;
    }
    #context-menu li {
      padding: 8px 12px;
      cursor: pointer;
    }
    #context-menu li:hover { background-color: #f2f2f2; }
    tr.draggable { cursor: move; }
  </style>
</head>
<body>
<div class="container mt-4" id="main-container">
  <h4>当前目录： /{{ current_path }}</h4>
  <div class="mb-3">
    {% if parent_path %}
      <a href="/{{ parent_path }}" class="btn btn-secondary">返回上一级</a>
    {% endif %}
  </div>
  <form method="POST" enctype="multipart/form-data" action="/upload/{{ current_path }}">
    <div class="form-group">
      <label>上传文件</label>
      <input type="file" class="form-control-file" name="file">
    </div>
    <button type="submit" class="btn btn-primary mb-2">上传</button>
  </form>
  <table class="table table-bordered" id="file-table">
    <thead>
      <tr>
        <th>文件/目录名</th>
        <th>类型</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      {% for item in files %}
      <tr class="draggable" data-path="{% if current_path %}{{ current_path }}/{{ item.name }}{% else %}{{ item.name }}{% endif %}" data-type="{{ 'dir' if item.is_dir else 'file' }}">
        <td>{{ item.name }}</td>
        <td>{{ "目录" if item.is_dir else "文件" }}</td>
        <td>
          {% if not item.is_dir %}
            {% set ext = item.name.rsplit('.', 1)[1]|lower %}
            {% if ext in ['png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'txt', 'md', 'json', 'py', 'log'] %}
              <a href="/view/{% if current_path %}{{ current_path }}/{{ item.name }}{% else %}{{ item.name }}{% endif %}" class="btn btn-sm btn-warning">预览</a>
            {% else %}
              <a href="/{% if current_path %}{{ current_path }}/{{ item.name }}{% else %}{{ item.name }}{% endif %}" class="btn btn-sm btn-success">下载</a>
            {% endif %}
          {% else %}
            <a href="/{% if current_path %}{{ current_path }}/{{ item.name }}{% else %}{{ item.name }}{% endif %}" class="btn btn-sm btn-info">进入</a>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div id="context-menu">
  <ul>
    <li id="rename">重命名</li>
    <li id="delete">删除</li>
  </ul>
</div>

<div class="modal" tabindex="-1" role="dialog" id="mkdir-modal">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">新建文件夹</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="关闭" id="modal-close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <input type="text" id="new-folder-name" class="form-control" placeholder="请输入文件夹名称">
      </div>
      <div class="modal-footer">
        <button type="button" id="create-folder" class="btn btn-primary">确定</button>
        <button type="button" class="btn btn-secondary" data-dismiss="modal" id="modal-cancel">取消</button>
      </div>
    </div>
  </div>
</div>

<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
<script>
var currentPath = "";
$(document).ready(function() {
    var $contextMenu = $("#context-menu");
    $(document).on("contextmenu", "tr[data-path]", function(e) {
        e.preventDefault();
        currentPath = $(this).attr("data-path");
        $contextMenu.css({ display: "block", left: e.pageX, top: e.pageY }).data("target", $(this));
    });
    $("#main-container").on("contextmenu", function(e) {
        if ($(e.target).closest("tr[data-path]").length === 0) {
            e.preventDefault();
            currentPath = "{{ current_path }}";
            $("#mkdir-modal").modal("show");
        }
    });
    $(document).click(function(e) {
        if (!$(e.target).closest("#context-menu").length) {
            $contextMenu.hide();
        }
    });
    $("#delete").click(function() {
        if (confirm("确认删除 " + currentPath + " ?")) {
            $.ajax({
                url: "/delete",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ path: currentPath }),
                success: function(response) {
                    if (response.success) {
                        alert("删除成功");
                        location.reload();
                    } else {
                        alert("删除失败:" + response.message);
                    }
                },
                error: function(xhr) {
                    alert("删除失败:" + xhr.responseJSON.message);
                }
            });
        }
        $contextMenu.hide();
    });
    $("#rename").click(function() {
        var newName = prompt("请输入新名称：", "");
        if (newName && newName.trim() !== "") {
            $.ajax({
                url: "/rename",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ old_path: currentPath, new_name: newName }),
                success: function(response) {
                    if (response.success) {
                        alert("重命名成功");
                        location.reload();
                    } else {
                        alert("重命名失败:" + response.message);
                    }
                },
                error: function(xhr) {
                    alert("重命名失败:" + xhr.responseJSON.message);
                }
            });
        }
        $contextMenu.hide();
    });
    $("tr.draggable").draggable({
        helper: "clone",
        opacity: 0.7,
        revert: "invalid"
    });
    $("tr.draggable[data-type='dir']").droppable({
        accept: "tr.draggable",
        hoverClass: "bg-warning",
        drop: function(event, ui) {
            var source = ui.draggable.attr("data-path");
            var destination = $(this).attr("data-path");
            if (source === destination) return;
            $.ajax({
                url: "/move",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ source: source, destination: destination }),
                success: function(response) {
                    if (response.success) {
                        alert("移动成功");
                        location.reload();
                    } else {
                        alert("移动失败:" + response.message);
                    }
                },
                error: function(xhr) {
                    alert("移动失败:" + xhr.responseJSON.message);
                }
            });
        }
    });
    $("#create-folder").click(function() {
        var dirname = $("#new-folder-name").val().trim();
        if (!dirname) {
            alert("请输入文件夹名称");
            return;
        }
        $.ajax({
            url: "/mkdir_ajax",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ parent_path: "{{ current_path }}", dirname: dirname }),
            success: function(response) {
                if (response.success) {
                    alert("目录创建成功");
                    location.reload();
                } else {
                    alert("创建目录失败:" + response.message);
                }
            },
            error: function(xhr) {
                alert("创建目录失败:" + xhr.responseJSON.message);
            }
        });
        $("#mkdir-modal").modal("hide");
        $("#new-folder-name").val("");
    });
    $("#modal-close, #modal-cancel").click(function() {
        $("#new-folder-name").val("");
    });
});
</script>
</body>
</html>
"""

# 预览编辑模板（文本文件）
PREVIEW_EDITOR_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>编辑文件 - {{ current_path }}</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    textarea { width: 100%; height: 70vh; }
  </style>
</head>
<body>
<div class="container mt-4">
  <h4>编辑文件： /{{ current_path }}</h4>
  <form method="POST">
    <textarea name="content" class="form-control">{{ content }}</textarea>
    <button type="submit" class="btn btn-primary mt-2">保存</button>
    <a href="/" class="btn btn-secondary mt-2">返回</a>
  </form>
</div>
</body>
</html>
"""

# 预览Markdown模板（编辑和预览）
PREVIEW_MD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>编辑 Markdown - {{ current_path }}</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    textarea { width: 100%; height: 70vh; min-height:400px; }
    .preview { border: 1px solid #ddd; padding: 10px; height: 70vh; overflow-y: auto; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
<div class="container-fluid mt-2">
  <h4>编辑 Markdown： /{{ current_path }}</h4>
  <div class="row">
    <div class="col-md-6">
      <form method="POST" id="edit-form">
        <textarea name="content" id="md-content" class="form-control">{{ content }}</textarea>
        <button type="submit" class="btn btn-primary mt-2">保存</button>
        <a href="/" class="btn btn-secondary mt-2">返回</a>
      </form>
    </div>
    <div class="col-md-6">
      <h5>预览</h5>
      <div class="preview" id="md-preview">{{ html_content|safe }}</div>
    </div>
  </div>
</div>
<script>
  var textarea = document.getElementById("md-content");
  var preview = document.getElementById("md-preview");
  textarea.addEventListener("input", function() {
      preview.innerHTML = marked(textarea.value);
  });
</script>
</body>
</html>
"""

# 图片预览模板
PREVIEW_IMAGE_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>预览图片 - {{ current_path }}</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    img { max-width: 100%; max-height: 80vh; margin-top:20px; }
  </style>
</head>
<body>
<div class="container mt-4 text-center">
  <h4>预览图片： /{{ current_path }}</h4>
  <img src="{{ file_url }}" alt="预览图片">
  <div class="mt-3"><a href="/" class="btn btn-secondary">返回</a></div>
</div>
</body>
</html>
"""

# 视频预览模板
PREVIEW_VIDEO_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>预览视频 - {{ current_path }}</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    video { max-width: 100%; max-height: 80vh; margin-top:20px; }
  </style>
</head>
<body>
<div class="container mt-4 text-center">
  <h4>预览视频： /{{ current_path }}</h4>
  <video controls>
    <source src="{{ file_url }}" type="video/mp4">
    您的浏览器不支持 video 标签。
  </video>
  <div class="mt-3"><a href="/" class="btn btn-secondary">返回</a></div>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
