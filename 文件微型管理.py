from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'
BASE_UPLOAD_FOLDER = 'uploads'

# Simplified in-memory "database"
users = {}

def get_user_folder(username):
    """Return the folder path for the given user."""
    return os.path.join(BASE_UPLOAD_FOLDER, username)

@app.route('/')
def index():
    auth_template = '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login / Register</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script>
            function handleFormSubmit(action) {
                const form = document.getElementById('auth-form');
                const url = action === 'login' ? '/login' : '/register';
                
                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams(new FormData(form))
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`${action.toUpperCase()} successful!`);
                        window.location.href = '/files/' + form.username.value;
                    } else {
                        alert(data.error || 'Something went wrong');
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        </script>
    </head>
    <body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="card-title text-center">Login or Register</h3>
                        <form id="auth-form">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="d-flex justify-content-between">
                                <button type="button" onclick="handleFormSubmit('login')" class="btn btn-primary">Login</button>
                                <button type="button" onclick="handleFormSubmit('register')" class="btn btn-success">Register</button>
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
    return render_template_string(auth_template)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if username in users:
        return jsonify({'success': False, 'error': 'Username already exists'})
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    users[username] = {'password': password_hash}
    os.makedirs(get_user_folder(username), exist_ok=True)
    return jsonify({'success': True})

@app.route('/upload/<username>/<path:subpath>', methods=['POST'])
def upload(username, subpath=''):
    print(f"Received upload request for username: {username}, subpath: {subpath}")
    if 'file' not in request.files:
        print("No file part in the request.")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        print("No selected file in the request.")
        return jsonify({'error': 'No selected file'}), 400

    user_folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, file.filename)
    
    print(f"Saving file to: {file_path}")

    file.save(file_path)
    return jsonify({'success': True})

@app.route('/files/<username>', defaults={'subpath': ''})
@app.route('/files/<username>/<path:subpath>')
def files(username, subpath):
    user_folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(user_folder, exist_ok=True)
    files = os.listdir(user_folder)
    files_and_dirs = [{'name': f, 'is_dir': os.path.isdir(os.path.join(user_folder, f))} for f in files]

    files_template = '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Secure File Management for {{username}}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { overflow: hidden; }
            ul { list-style-type: none; padding: 0; margin-top: 20px; }
            li { margin: 5px 0; cursor: pointer; padding: 10px; border-radius: 5px; transition: background-color 0.2s; }
            li:hover { background-color: #f1f1f1; }
            #context-menu { display: none; position: absolute; background: #ffffff; border: 1px solid #ccc; z-index: 1000; min-width: 150px; }
            #context-menu a { display: block; padding: 10px; text-decoration: none; color: black; }
            #context-menu a:hover { background-color: #e9ecef; }
            #password-container { position: fixed; top: 10px; right: 10px; z-index: 1000; }
            .file-list-container { max-height: 80vh; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div id="password-container">
            <form>
                <input type="password" id="encryption-password" placeholder="Enter encryption password" class="form-control" aria-label="encryption-password" autocomplete="new-password">
            </form>
        </div>
        <div class="container-fluid py-3">
            <h2 class="text-center">Files and Directories for {{username}}</h2>
            <div class="row">
                <div class="col-12 file-list-container">
                    <ul id="file-list" class="bg-white shadow-sm p-3 mb-5">
                        {% for item in files %}
                            <li class="{{ 'directory' if item.is_dir else 'file' }}" 
                                data-name="{{ item.name }}" 
                                data-type="{{ 'dir' if item.is_dir else 'file' }}" 
                                draggable="true" 
                                title="{{ item.name }}">
                                
                                {% if item.is_dir %}
                                    <span><i class="bi bi-folder-fill"></i> </span>
                                    <a href="{{ url_for('files', username=username, subpath=os.path.join(subpath, item.name)) }}">{{ item.name }}/</a>
                                {% else %}
                                    <span><i class="bi bi-file-earmark"></i> </span>
                                    <a href="#" onclick="downloadFile('{{ item.name }}')">{{ item.name }}</a>
                                {% endif %}
                            </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
        <div id="context-menu">
            <a href="#" id="upload-file-btn">Upload File</a>
            <a href="#" id="rename-file-btn" style="display: none;">Rename</a>
            <a href="#" id="delete-file-btn" style="display: none;">Delete</a>
        </div>
        <input type="file" id="file-upload" style="display: none;">
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const contextMenu = document.getElementById('context-menu');
                const fileInput = document.getElementById('file-upload');
                const passwordInput = document.getElementById('encryption-password');
                let currentFile = "";
                let currentDir = "{{ subpath }}";

                async function encryptFile(file, password) {
                    const enc = new TextEncoder();
                    const passwordKey = await window.crypto.subtle.importKey(
                        "raw",
                        enc.encode(password),
                        "PBKDF2",
                        false,
                        ["deriveKey"]
                    );
                    const key = await window.crypto.subtle.deriveKey(
                        {
                            name: "PBKDF2",
                            salt: window.crypto.getRandomValues(new Uint8Array(16)),
                            iterations: 100000,
                            hash: "SHA-256"
                        },
                        passwordKey,
                        { name: "AES-GCM", length: 256 },
                        false,
                        ["encrypt", "decrypt"]
                    );
                    const iv = window.crypto.getRandomValues(new Uint8Array(12));
                    const data = await file.arrayBuffer();
                    const encryptedContent = await window.crypto.subtle.encrypt(
                        { name: "AES-GCM", iv: iv },
                        key,
                        data
                    );
                    return { iv, encryptedContent };
                }

                async function downloadFile(filename) {
                    const password = passwordInput.value;
                    if (!password) {
                        alert("Please enter a password for decryption.");
                        return;
                    }

                    fetch(`/download/{{ username }}/${currentDir}/${filename}`)
                        .then(response => response.json())
                        .then(async ({ encryptedContent, iv }) => {
                            const key = await window.crypto.subtle.deriveKey(
                                {
                                    name: "PBKDF2",
                                    salt: window.crypto.getRandomValues(new Uint8Array(16)),
                                    iterations: 100000,
                                    hash: "SHA-256"
                                },
                                await window.crypto.subtle.importKey(
                                    "raw",
                                    new TextEncoder().encode(password),
                                    "PBKDF2",
                                    false,
                                    ["deriveKey"]
                                ),
                                { name: "AES-GCM", length: 256 },
                                false,
                                ["encrypt", "decrypt"]
                            );
                            const decryptedContent = await window.crypto.subtle.decrypt(
                                { name: "AES-GCM", iv: new Uint8Array(iv) },
                                key,
                                encryptedContent
                            );
                            const url = URL.createObjectURL(new Blob([decryptedContent]));
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            URL.revokeObjectURL(url);
                        })
                        .catch(error => {
                            console.error("Decryption error:", error);
                            alert("Failed to decrypt file with the provided password.");
                        });
                }

                fileInput.addEventListener('change', async function() {
                    const file = fileInput.files[0];
                    if (file) {
                        const password = passwordInput.value;
                        if (!password) {
                            alert("Please enter a password for encryption.");
                            return;
                        }

                        const { iv, encryptedContent } = await encryptFile(file, password);
                        const formData = new FormData();
                        formData.append('file', new Blob([encryptedContent], { type: 'application/octet-stream' }), file.name);
                        formData.append('iv', new Blob([iv]));

                        const uploadUrl = `/upload/${encodeURIComponent('{{ username }}')}/${encodeURIComponent(currentDir)}`;
                        console.log('Upload URL:', uploadUrl);

                        fetch(uploadUrl, {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log("Upload response:", data);
                            alert(data.success ? 'File uploaded and encrypted successfully!' : (data.error || 'Upload failed'));
                            if (data.success) window.location.reload();
                        })
                        .catch(error => {
                            console.error("Upload failed:", error);
                        });
                    }
                });

                document.getElementById('file-list').addEventListener('contextmenu', function(e) {
                    e.preventDefault();

                    const targetElement = e.target.closest('li');
                    if (targetElement) {
                        currentFile = targetElement.getAttribute('data-name');
                        const isFile = targetElement.getAttribute('data-type') === 'file';

                        document.getElementById('rename-file-btn').style.display = isFile ? 'block' : 'none';
                        document.getElementById('delete-file-btn').style.display = isFile ? 'block' : 'none';
                    } else {
                        currentFile = '';
                        document.getElementById('rename-file-btn').style.display = 'none';
                        document.getElementById('delete-file-btn').style.display = 'none';
                    }

                    contextMenu.style.top = `${e.clientY}px`;
                    contextMenu.style.left = `${e.clientX}px`;
                    contextMenu.style.display = 'block';
                });

                document.addEventListener('click', function() {
                    contextMenu.style.display = 'none';
                });

                document.getElementById('upload-file-btn').addEventListener('click', function() {
                    contextMenu.style.display = 'none';
                    fileInput.click();
                });

                document.getElementById('rename-file-btn').addEventListener('click', function() {
                    contextMenu.style.display = 'none';
                    const newName = prompt("Enter new name for the file:", currentFile);
                    if (newName) {
                        fetch(`/rename/{{ username }}/${encodeURIComponent(currentDir)}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ old_name: currentFile, new_name: newName })
                        })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.success ? 'File renamed successfully!' : (data.error || 'Rename failed'));
                            if (data.success) window.location.reload();
                        });
                    }
                });

                document.getElementById('delete-file-btn').addEventListener('click', function() {
                    contextMenu.style.display = 'none';
                    if (confirm("Are you sure you want to delete " + currentFile + "?")) {
                        fetch(`/delete/{{ username }}/${encodeURIComponent(currentDir)}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ filename: currentFile })
                        })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.success ? 'File deleted successfully!' : (data.error || 'Delete failed'));
                            if (data.success) window.location.reload();
                        });
                    }
                });

                document.querySelectorAll('#file-list li').forEach(function(item) {
                    item.addEventListener('dragstart', function(e) {
                        e.dataTransfer.setData('text/plain', item.getAttribute('data-name'));
                    });
                });

                document.querySelectorAll('#file-list .directory').forEach(function(dir) {
                    dir.addEventListener('dragover', function(e) {
                        e.preventDefault();
                    });

                    dir.addEventListener('drop', function(e) {
                        e.preventDefault();
                        const srcFileName = e.dataTransfer.getData('text/plain');
                        const destDirName = dir.getAttribute('data-name');
                        const srcPath = `${currentDir}/${srcFileName}`;
                        const destPath = `${currentDir}/${destDirName}/${srcFileName}`;

                        fetch(`/move/{{ username }}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ src_path: srcPath, dest_path: destPath })
                        })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.success ? 'File moved successfully!' : (data.error || 'Move failed'));
                            if (data.success) window.location.reload();
                        });
                    });
                });
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(files_template, username=username, files=files_and_dirs, subpath=subpath)

@app.route('/download/<username>/<path:subpath>/<filename>')
def download(username, subpath, filename):
    user_folder = os.path.join(get_user_folder(username), subpath)
    return send_from_directory(user_folder, filename)

@app.route('/rename/<username>/<path:subpath>', methods=['POST'])
def rename(username, subpath):
    old_name = request.json.get('old_name')
    new_name = request.json.get('new_name')
    if not old_name or not new_name:
        return jsonify({'error': 'Invalid filenames'}), 400
    folder_path = os.path.join(get_user_folder(username), subpath)
    old_file_path = os.path.join(folder_path, old_name)
    new_file_path = os.path.join(folder_path, new_name)
    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)
        return jsonify({'success': True})
    return jsonify({'error': 'File does not exist'}), 404

@app.route('/delete/<username>/<path:subpath>', methods=['POST'])
def delete(username, subpath):
    filename = request.json.get('filename')
    folder_path = os.path.join(get_user_folder(username), subpath)
    file_path = os.path.join(folder_path, filename)
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return jsonify({'success': True})
    return jsonify({'error': 'File does not exist'}), 404

@app.route('/move/<username>', methods=['POST'])
def move(username):
    src_path = request.json.get('src_path')
    dest_path = request.json.get('dest_path')
    if not src_path or not dest_path:
        return jsonify({'error': 'Invalid paths'}), 400
    full_src_path = os.path.join(BASE_UPLOAD_FOLDER, username, src_path)
    full_dest_path = os.path.join(BASE_UPLOAD_FOLDER, username, dest_path)
    if os.path.exists(full_src_path):
        shutil.move(full_src_path, full_dest_path)
        return jsonify({'success': True})
    return jsonify({'error': 'Source file does not exist'}), 404

if __name__ == '__main__':
    os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
