from flask import Flask, request, jsonify, send_file, render_template
import os
import shutil
import zipfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.secret_key = 'supersecretkey'
# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# ---------------------- Flask Routes ----------------------
# 首页，渲染HTML模板
@app.route('/')
def index():
    return render_template('index.html')

# 列出文件和目录，返回JSON格式
@app.route('/list_files', methods=['GET'])
def list_files():
    folder = request.args.get('folder', '')
    abs_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    files = []
    directories = []
    # 遍历指定目录下的文件和文件夹
    for entry in os.scandir(abs_folder):
        if entry.is_file():
            files.append(entry.name)
        elif entry.is_dir():
            directories.append(entry.name)
    return jsonify({
        'files': files,
        'directories': directories,
        'current_folder': folder
    })
# 上传文件接口，支持任何文件格式
@app.route('/upload', methods=['POST'])
def upload_file():
    folder = request.form.get('folder', '')
    abs_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(abs_folder, exist_ok=True)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(abs_folder, filename))
    return jsonify({'success': True})

# 下载一个文件
@app.route('/download/<path:filename>')
def download_file(filename):
    folder, file = os.path.split(filename)
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), file, as_attachment=True)

# 下载文件夹为ZIP
@app.route('/download_zip/<path:foldername>')
def download_zip(foldername):
    abs_folder = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
    output_filename = foldername.rstrip('/').split('/')[-1] + '.zip'
    zip_path = os.path.join('/tmp', output_filename)

    # 创建ZIP文件
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(abs_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, abs_folder)
                zipf.write(file_path, arcname)

    return send_file(zip_path, as_attachment=True, attachment_filename=output_filename)

# 删除文件或文件夹
@app.route('/delete', methods=['POST'])
def delete_file():
    folder = request.form.get('folder', '')
    filename = request.form.get('filename', '')
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return jsonify({'success': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 400

# 重命名文件或文件夹
@app.route('/rename', methods=['POST'])
def rename_file():
    folder = request.form.get('folder', '')
    old_name = request.form.get('old_name', '')
    new_name = request.form.get('new_name', '')
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, old_name)
    new_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, secure_filename(new_name))

    try:
        os.rename(old_path, new_path)
        return jsonify({'success': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 400

# 移动文件或文件夹
@app.route('/move', methods=['POST'])
def move_file():
    src_folder = request.form.get('src_folder', '')
    dest_folder = request.form.get('dest_folder', '')
    filename = request.form.get('filename', '')
    src_path = os.path.join(app.config['UPLOAD_FOLDER'], src_folder, filename)
    dest_path = os.path.join(app.config['UPLOAD_FOLDER'], dest_folder, filename)

    try:
        shutil.move(src_path, dest_path)
        return jsonify({'success': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 400
if __name__ == '__main__':
    app.run(debug=True)
# ---------------------- HTML and JavaScript ----------------------
# index.html

"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    <title>File Manager</title>
    <style>
        .context-menu { display: none; position: absolute; z-index: 1000; background-color: #f3f3f3; border: 1px solid #d4d4d4; }
        .context-menu a { display: block; padding: 8px 12px; color: #333; text-decoration: none; }
        .context-menu a:hover { background-color: #ccc; }
        .directory::before { content: "📁"; padding-right: 5px; }
        .file::before { content: "📄"; padding-right: 5px; }
    </style>
</head>
<body>
<div class="container">
    <h1 class="mt-5">File Manager</h1>
    <hr>
    <div class="mb-3">
        <form id="uploadForm" class="form-inline">
            <input type="file" class="form-control mr-2" id="fileInput">
            <button type="submit" class="btn btn-primary">Upload</button>
        </form>
    </div>
    <ul id="fileList" class="list-group mb-3"></ul>
    <button id="goBack" class="btn btn-secondary">Go Back</button>
</div>

<div class="context-menu" id="contextMenu">
    <a href="#" id="downloadAction">Download</a>
    <a href="#" id="downloadZipAction">Download as ZIP</a>
    <a href="#" id="renameAction">Rename</a>
    <a href="#" id="deleteAction">Delete</a>
</div>

<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
<script>
// ---------------------- JavaScript Logic ----------------------

let currentFolder = '';

function listFiles() {
    $.get('/list_files', { folder: currentFolder }, function(data) {
        $('#fileList').empty();
        $('#goBack').toggle(Boolean(data.current_folder));

        // 列出目录
        data.directories.forEach(dir => {
            $('#fileList').append('<li class="list-group-item directory" data-name="' + dir + '" draggable="true">' + dir + '</li>');
        });

        // 列出文件
        data.files.forEach(file => {
            $('#fileList').append('<li class="list-group-item file" data-name="' + file + '" draggable="true">' + file + '</li>');
        });

        // 可拖动
        $('#fileList .list-group-item').draggable({
            revert: true,
            stop: function(event, ui) {
                let targetFolder = prompt("Move to folder:", currentFolder);
                if (targetFolder !== null) {
                    moveFile($(this).data('name'), targetFolder);
                }
            }
        });
    });
}

// 移动文件或文件夹
function moveFile(filename, destFolder) {
    $.post('/move', { src_folder: currentFolder, dest_folder: destFolder, filename: filename })
        .done(listFiles)
        .fail(function(xhr) {
            alert('Error: ' + xhr.responseText);
        });
}

$(document).ready(function() {
    listFiles();

    // 上传文件
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
        let formData = new FormData();
        formData.append('file', $('#fileInput')[0].files[0]);
        formData.append('folder', currentFolder);
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function() {
                listFiles();
            },
            error: function() {
                alert('File upload failed.');
            }
        });
    });

    // 返回上一级目录
    $('#goBack').click(function() {
        const pathParts = currentFolder.split('/');
        pathParts.pop();
        currentFolder = pathParts.join('/');
        listFiles();
    });

    // 右键菜单显示
    $('#fileList').on('contextmenu', '.list-group-item', function(e) {
        e.preventDefault();
        let itemName = $(this).data('name');
        const isDir = $(this).hasClass('directory');
        $('#contextMenu').css({ top: e.pageY, left: e.pageX }).show()
            .data('itemName', itemName)
            .data('isDir', isDir);
    });

    // 隐藏右键菜单
    $(document).click(function() {
        $('#contextMenu').hide();
    });

    // 下载文件
    $('#downloadAction').click(function(e) {
        e.preventDefault();
        let itemName = $('#contextMenu').data('itemName');
        let itemPath = currentFolder + '/' + itemName;
        if (!$('#contextMenu').data('isDir')) {
            window.location.href = '/download/' + encodeURIComponent(itemPath);
        } else {
            alert('Please select "Download as ZIP" for folders.');
        }
    });

    // 下载目录为ZIP
    $('#downloadZipAction').click(function(e) {
        e.preventDefault();
        let itemName = $('#contextMenu').data('itemName');
        let itemPath = currentFolder + '/' + itemName;
        if ($('#contextMenu').data('isDir')) {
            window.location.href = '/download_zip/' + encodeURIComponent(itemPath);
        } else {
            alert('ZIP download is only for directories.');
        }
    });

    // 删除文件或目录
    $('#deleteAction').click(function(e) {
        e.preventDefault();
        let itemName = $('#contextMenu').data('itemName');
        $.post('/delete', { folder: currentFolder, filename: itemName })
            .done(listFiles)
            .fail(function(xhr) {
                alert('Error: ' + xhr.responseText);
            });
    });

    // 重命名文件或目录
    $('#renameAction').click(function(e) {
        e.preventDefault();
        let itemName = $('#contextMenu').data('itemName');
        let newName = prompt("Enter new name:", itemName);
        if (newName && newName !== itemName) {
            $.post('/rename', { folder: currentFolder, old_name: itemName, new_name: newName })
                .done(listFiles)
                .fail(function(xhr) {
                    alert('Error: ' + xhr.responseText);
                });
        }
    });
});
</script>
</body>
</html>
"""
