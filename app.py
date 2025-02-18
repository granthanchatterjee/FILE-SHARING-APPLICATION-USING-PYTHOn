from flask import Flask, request, render_template_string, send_file, redirect, url_for, jsonify, make_response
import sqlite3
import qrcode
import uuid
import os
import zipfile
import io

app = Flask(__name__)
DATABASE = 'file_sharing.db'
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
STATIC_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY, filename TEXT, batch_id TEXT)''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    index_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Sharing</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .file-list {
                margin: 20px 0;
            }
            .file-item {
                margin: 10px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .remove-btn {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
            }
            .upload-btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 0;
            }
            .add-more-btn {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 10px;
            }
            #fileInput {
                display: none;
            }
        </style>
    </head>
    <body>
        <h1>Upload Files</h1>
        <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="files" multiple>
            <div class="file-list" id="fileList"></div>
            <button type="button" class="add-more-btn" onclick="document.getElementById('fileInput').click()">
                Add Files
            </button>
            <button type="submit" class="upload-btn">Upload All Files</button>
        </form>

        <script>
            let selectedFiles = new Set();

            document.getElementById('fileInput').addEventListener('change', function(e) {
                const files = Array.from(e.target.files);

                files.forEach(file => {
                    if (!selectedFiles.has(file.name)) {
                        selectedFiles.add(file.name);
                        addFileToList(file);
                    }
                });
            });

            function addFileToList(file) {
                const fileList = document.getElementById('fileList');
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <span>${file.name}</span>
                    <button type="button" class="remove-btn" onclick="removeFile('${file.name}')">Remove</button>
                `;
                fileList.appendChild(div);
            }

            function removeFile(fileName) {
                selectedFiles.delete(fileName);
                const fileItems = document.querySelectorAll('.file-item');
                fileItems.forEach(item => {
                    if (item.querySelector('span').textContent === fileName) {
                        item.remove();
                    }
                });

                const fileInput = document.getElementById('fileInput');
                fileInput.value = '';
            }

            document.getElementById('uploadForm').onsubmit = function(e) {
                if (selectedFiles.size === 0) {
                    e.preventDefault();
                    alert('Please select at least one file to upload.');
                    return false;
                }
                return true;
            };
        </script>
    </body>
    </html>
    '''
    return render_template_string(index_html)


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files:
            return 'No files selected', 400

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return 'No files selected', 400

        batch_id = str(uuid.uuid4())

        for file in files:
            if file and file.filename:
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                c.execute("INSERT INTO files (filename, batch_id) VALUES (?, ?)",
                          (filename, batch_id))
                conn.commit()
                conn.close()

        generate_qr_code(batch_id)
        return redirect(url_for('sender_view', batch_id=batch_id))

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return f'Error uploading files: {str(e)}', 500


@app.route('/sender/<batch_id>')
def sender_view(batch_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename FROM files WHERE batch_id=?", (batch_id,))
    files = c.fetchall()
    conn.close()

    files_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Files Uploaded</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .qr-code {
                margin: 20px 0;
            }
            .file-list {
                margin: 20px 0;
            }
            .file-item {
                margin: 10px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            .download-link {
                color: #0066cc;
                text-decoration: none;
            }
            .download-link:hover {
                text-decoration: underline;
            }
            .add-more-section {
                margin: 20px 0;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
            .add-more-btn {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Files for Batch {{ batch_id }}</h1>
        <div class="file-list">
            <h2>Uploaded Files:</h2>
            {% for file in files %}
            <div class="file-item">{{ file[0] }}</div>
            {% endfor %}
        </div>

        <div class="add-more-section">
            <h3>Add More Files</h3>
            <form action="{{ url_for('upload_additional', batch_id=batch_id) }}" method="post" enctype="multipart/form-data">
                <input type="file" name="files" multiple>
                <button type="submit" class="add-more-btn">Upload Additional Files</button>
            </form>
        </div>

        <div class="qr-code">
            <h2>QR Code</h2>
            <img src="/static/{{ batch_id }}.png" alt="QR Code">
        </div>
        <p>Share this QR code or the link below with others to download the files:</p>
        <p><a class="download-link" href="{{ url_for('receiver_view', batch_id=batch_id, _external=True) }}">
            {{ url_for('receiver_view', batch_id=batch_id, _external=True) }}
        </a></p>
    </body>
    </html>
    '''
    return render_template_string(files_html, files=files, batch_id=batch_id)


@app.route('/upload_additional/<batch_id>', methods=['POST'])
def upload_additional(batch_id):
    try:
        if 'files' not in request.files:
            return 'No files selected', 400

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return 'No files selected', 400

        for file in files:
            if file and file.filename:
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                c.execute("INSERT INTO files (filename, batch_id) VALUES (?, ?)",
                          (filename, batch_id))
                conn.commit()
                conn.close()

        generate_qr_code(batch_id)
        return redirect(url_for('sender_view', batch_id=batch_id))

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return f'Error uploading files: {str(e)}', 500


@app.route('/receiver/<batch_id>')
def receiver_view(batch_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename FROM files WHERE batch_id=?", (batch_id,))
    files = c.fetchall()
    conn.close()

    files_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Files Available for Download</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .file-list {
                margin: 20px 0;
            }
            .file-item {
                margin: 10px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            .file-item label {
                margin-left: 10px;
                flex-grow: 1;
            }
            .download-btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 0;
            }
            .select-all {
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>Files Available for Download</h1>
        <div class="select-all">
            <label>
                <input type="checkbox" id="selectAll" checked> Select/Deselect All
            </label>
        </div>
        <div class="file-list" id="fileList">
            {% for file in files %}
            <div class="file-item">
                <input type="checkbox" class="file-checkbox" value="{{ file[0] }}" checked>
                <label>{{ file[0] }}</label>
            </div>
            {% endfor %}
        </div>
        <button onclick="downloadSelected()" class="download-btn">Download Selected Files</button>

        <script>
            document.getElementById('selectAll').addEventListener('change', function(e) {
                document.querySelectorAll('.file-checkbox').forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
            });

            function downloadSelected() {
                const selectedFiles = Array.from(document.querySelectorAll('.file-checkbox:checked'))
                    .map(checkbox => checkbox.value);

                if (selectedFiles.length === 0) {
                    alert('Please select at least one file to download.');
                    return;
                }

                if (selectedFiles.length === 1) {
                    window.location.href = '/download/' + selectedFiles[0];
                    return;
                }

                const queryString = selectedFiles.map(file => `file=${encodeURIComponent(file)}`).join('&');
                window.location.href = '/download_multiple?batch_id={{ batch_id }}&' + queryString;
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(files_html, files=files, batch_id=batch_id)


@app.route('/download_multiple')
def download_multiple():
    try:
        batch_id = request.args.get('batch_id')
        files = request.args.getlist('file')

        if not files:
            return 'No files selected', 400

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in files:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(filepath):
                    zf.write(filepath, filename)

        memory_file.seek(0)
        response = make_response(memory_file.getvalue())
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = f'attachment; filename=files_{batch_id}.zip'
        return response

    except Exception as e:
        return f'Error creating zip file: {str(e)}', 500


@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)
    except Exception as e:
        return f'Error downloading file: {str(e)}', 404


def generate_qr_code(batch_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_for('receiver_view', batch_id=batch_id, _external=True))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(STATIC_FOLDER, f'{batch_id}.png'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)