from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import shutil
from contextlib import closing
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'users.db'
BASE_UPLOAD_FOLDER = 'uploads'

def init_db():
    with closing(sqlite3.connect(DATABASE)) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.execute(query, args)
        rv = [dict((cur.description[idx] [0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if one else rv

def add_user(username, password_hash):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
        conn.commit()

def get_user_folder(username):
    return os.path.join(BASE_UPLOAD_FOLDER, username)

@app.route('/')
def index():
    return render_template('auth.html')  # Load the login/register page

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
    if user and check_password_hash(user['password'], password):
        return redirect(url_for('files', username=username))
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    existing_user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
    if existing_user:
        return jsonify({'success': False, 'error': 'Username already exists'})
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    add_user(username, password_hash)
    os.makedirs(get_user_folder(username), exist_ok=True)
    return jsonify({'success': True})

@app.route('/upload/<username>/<path:subpath>', methods=['POST'])
def upload(username, subpath):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    user_folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(user_folder, exist_ok=True)
    file.save(os.path.join(user_folder, file.filename))
    return jsonify({'success': True})

@app.route('/files/<username>', defaults={'subpath': ''})
@app.route('/files/<username>/<path:subpath>')
def files(username, subpath):
    user_folder = os.path.join(get_user_folder(username), subpath)
    os.makedirs(user_folder, exist_ok=True)
    files = os.listdir(user_folder)
    files_and_dirs = [{'name': f, 'is_dir': os.path.isdir(os.path.join(user_folder, f))} for f in files]
    return render_template('files.html', files=files_and_dirs, username=username, subpath=subpath)

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
    init_db()
    app.run(debug=True)



<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login / Register</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
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
                alert(`${action.charAt(0).toUpperCase() + action.slice(1)} successful!`);
                window.location.href = '/files/' + form.username.value;
            } else {
                alert(data.error || 'Something went wrong');
            }
        })
        .catch(error => console.error('Error:', error));
    }
</script>
</body>
</html>



<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Management for {{ username }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { overflow: hidden; }
        ul { list-style-type: none; padding: 0; margin-top: 20px; }
        li { margin: 5px 0; cursor: pointer; padding: 5px; border-radius: 5px; transition: background-color 0.2s; }
        li:hover { background-color: #f1f1f1; }
        #context-menu { display: none; position: absolute; background: #ffffff; border: 1px solid #ccc; z-index: 1000; }
        #context-menu a { display: block; padding: 8px; text-decoration: none; color: black; }
        #context-menu a:hover { background-color: #f1f1f1; }
    </style>
</head>
<body>
<div class="container-fluid py-3">
    <h2 class="text-center">Files and Directories for {{ username }}</h2>
    <div class="row">
        <div class="col-12">
            <ul id="file-list" class="bg-white shadow-sm p-3 mb-5">
                {% for item in files %}
                    <li class="{{ 'directory' if item.is_dir else 'file' }}" data-name="{{ item.name }}" data-type="{{ 'dir' if item.is_dir else 'file' }}" draggable="true">
                        {% if item.is_dir %}
                            <span><i class="bi bi-folder-fill"></i> </span>
                            <a href="{{ url_for('files', username=username, subpath=os.path.join(subpath, item.name)) }}">{{ item.name }}/</a>
                        {% else %}
                            <span><i class="bi bi-file-earmark"></i> </span>
                            <a href="{{ url_for('download', username=username, subpath=subpath, filename=item.name) }}">{{ item.name }}</a>
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>

<!-- Context Menu -->
<div id="context-menu">
    <a href="#" id="upload-file-btn">Upload File</a>
    <a href="#" id="rename-file-btn">Rename</a>
    <a href="#" id="delete-file-btn">Delete</a>
</div>

<!-- Hidden File Input -->
<input type="file" id="file-upload" style="display: none;">

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const contextMenu = document.getElementById('context-menu');
        const fileInput = document.getElementById('file-upload');
        let currentFile = "";
        let currentDir = "{{ subpath }}";

        // Right-click to show context menu
        document.getElementById('file-list').addEventListener('contextmenu', function(e) {
            e.preventDefault();
            const { clientX: mouseX, clientY: mouseY } = e;
            contextMenu.style.top = `${mouseY}px`;
            contextMenu.style.left = `${mouseX}px`;
            contextMenu.style.display = 'block';
            currentFile = e.target.closest('li') ? e.target.closest('li').getAttribute('data-name') : "";
        });

        // Hide context menu on click elsewhere
        document.addEventListener('click', function() {
            contextMenu.style.display = 'none';
        });

        // File upload on right-click menu
        document.getElementById('upload-file-btn').addEventListener('click', function() {
            contextMenu.style.display = 'none';
            fileInput.click();
        });

        fileInput.addEventListener('change', function() {
            const file = fileInput.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                fetch(`/upload/{{ username }}/${currentDir}`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.success ? 'File uploaded successfully!' : (data.error || 'Upload failed'));
                    if (data.success) window.location.reload();
                });
            }
        });

        // Rename file
        document.getElementById('rename-file-btn').addEventListener('click', function() {
            contextMenu.style.display = 'none';
            const newName = prompt("Enter new name for the file:", currentFile);
            if (newName) {
                fetch(`/rename/{{ username }}/${currentDir}`, {
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

        // Delete file
        document.getElementById('delete-file-btn').addEventListener('click', function() {
            contextMenu.style.display = 'none';
            if (confirm("Are you sure you want to delete " + currentFile + "?")) {
                fetch(`/delete/{{ username }}/${currentDir}`, {
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

        // Drag and Drop feature for moving files
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





<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure File Management for {{ username }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/crypto-js.min.js"></script>
    <style>
        body { overflow: hidden; }
        
        ul { 
            list-style-type: none; 
            padding: 0; 
            margin-top: 20px; 
        }
        
        li { 
            margin: 5px 0; 
            cursor: pointer; 
            padding: 10px; 
            border-radius: 5px; 
            transition: background-color 0.2s; 
        }
        
        li:hover { background-color: #f1f1f1; }

        #context-menu { 
            display: none; 
            position: absolute; 
            background: #ffffff; 
            border: 1px solid #ccc; 
            z-index: 1000; 
        }
        
        #context-menu a { 
            display: block; 
            padding: 10px; 
            text-decoration: none; 
            color: black; 
        }
        
        #context-menu a:hover { background-color: #e9ecef; }
        
        #password-input { 
            position: fixed; 
            top: 10px; 
            right: 10px; 
            z-index: 1000; 
        }
        
        .file-list-container { 
            max-height: 80vh; 
            overflow-y: auto;
        }
    </style>
</head>
<body>

    <!-- Password Input Field for Encryption/Decryption -->
    <div id="password-input">
        <input type="password" id="encryption-password" placeholder="Enter encryption password" class="form-control" aria-label="encryption-password">
    </div>

    <div class="container-fluid py-3">

        <!-- Page Title -->
        <h2 class="text-center">Files and Directories for {{ username }}</h2>

        <div class="row">

            <!-- File List Section -->
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

    <!-- Context Menu for File Operations -->
    <div id="context-menu">
        <a href="#" id="upload-file-btn">Upload File</a>
        <a href="#" id="rename-file-btn">Rename</a>
        <a href="#" id="delete-file-btn">Delete</a>
    </div>

    <!-- Hidden File Input Element for Uploads -->
    <input type="file" id="file-upload" style="display: none;">

    <script>
        document.addEventListener('DOMContentLoaded', function() {

            // DOM Elements
            const contextMenu = document.getElementById('context-menu');
            const fileInput = document.getElementById('file-upload');
            const passwordInput = document.getElementById('encryption-password');
            let currentFile = "";
            let currentDir = "{{ subpath }}";

            // Encrypt file using password
            function encryptFile(file, password) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = function() {
                        const wordArray = CryptoJS.lib.WordArray.create(reader.result);
                        const encrypted = CryptoJS.AES.encrypt(wordArray, password).toString();
                        resolve(encrypted);
                    };
                    reader.onerror = function() {
                        reject("Failed to encrypt file");
                    };
                    reader.readAsArrayBuffer(file);
                });
            }

            // Decrypt file using password
            function decryptFile(encryptedData, password) {
                try {
                    const decrypted = CryptoJS.AES.decrypt(encryptedData, password);
                    const typedArray = new Uint8Array(decrypted.sigBytes);
                    decrypted.words.forEach((word, idx) => {
                        typedArray[idx * 4] = (word >> 24) & 0xff;
                        typedArray[idx * 4 + 1] = (word >> 16) & 0xff;
                        typedArray[idx * 4 + 2] = (word >> 8) & 0xff;
                        typedArray[idx * 4 + 3] = word & 0xff;
                    });
                    return new Blob([typedArray]);
                } catch (error) {
                    alert("Failed to decrypt file with the provided password.");
                    return null;
                }
            }

            // Handle file upload with encryption
            fileInput.addEventListener('change', async function() {
                const file = fileInput.files[0];
                if (file) {
                    const password = passwordInput.value;
                    if (!password) {
                        alert("Please enter a password for encryption.");
                        return;
                    }

                    try {
                        const encryptedData = await encryptFile(file, password);
                        const formData = new FormData();
                        formData.append('file', new Blob([encryptedData], { type: 'text/plain' }), file.name);

                        fetch(`/upload/{{ username }}/${currentDir}`, {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.success ? 'File uploaded and encrypted successfully!' : (data.error || 'Upload failed'));
                            if (data.success) window.location.reload();
                        });
                    } catch (error) {
                        alert(error);
                    }
                }
            });

            // Handle file downloads with decryption
            async function downloadFile(filename) {
                const password = passwordInput.value;
                if (!password) {
                    alert("Please enter a password for decryption.");
                    return;
                }

                fetch(`/download/{{ username }}/${currentDir}/${filename}`)
                    .then(response => response.text())
                    .then(encryptedData => {
                        const decryptedBlob = decryptFile(encryptedData, password);

                        if (decryptedBlob) {
                            // Download decrypted file
                            const url = URL.createObjectURL(decryptedBlob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            URL.revokeObjectURL(url);
                        } else {
                            // If decryption failed, save the encrypted file
                            alert("Error occurred during file decryption. The encrypted file will be saved.");
                            const blob = new Blob([encryptedData], { type: 'text/plain' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = filename + ".enc";
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            URL.revokeObjectURL(url);
                        }
                    });
            }

            // Context Menu Operations
            // Right-click to show context menu
            document.getElementById('file-list').addEventListener('contextmenu', function(e) {
                e.preventDefault();
                const { clientX: mouseX, clientY: mouseY } = e;
                contextMenu.style.top = `${mouseY}px`;
                contextMenu.style.left = `${mouseX}px`;
                contextMenu.style.display = 'block';
                currentFile = e.target.closest('li') ? e.target.closest('li').getAttribute('data-name') : "";
            });

            // Hide context menu on click elsewhere
            document.addEventListener('click', function() {
                contextMenu.style.display = 'none';
            });

            // File upload via context menu
            document.getElementById('upload-file-btn').addEventListener('click', function() {
                contextMenu.style.display = 'none';
                fileInput.click();
            });

            // Rename file
            document.getElementById('rename-file-btn').addEventListener('click', function() {
                contextMenu.style.display = 'none';
                const newName = prompt("Enter new name for the file:", currentFile);
                if (newName) {
                    fetch(`/rename/{{ username }}/${currentDir}`, {
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

            // Delete file
            document.getElementById('delete-file-btn').addEventListener('click', function() {
                contextMenu.style.display = 'none';
                if (confirm("Are you sure you want to delete " + currentFile + "?")) {
                    fetch(`/delete/{{ username }}/${currentDir}`, {
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

            // Drag and Drop Functionality
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
