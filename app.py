from flask import Flask, render_template, request, send_file, jsonify
import pypandoc
import os
import tempfile
from werkzeug.utils import secure_filename
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

ALLOWED_EXTENSIONS = {'md', 'markdown'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file', 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as input_file:
            content = file.read().decode('utf-8')
            input_file.write(content)
            input_path = input_file.name
        
        output_filename = os.path.splitext(filename)[0] + '.docx'
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        try:
            # Convert markdown to docx
            pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
            
            # Clean up input file
            os.unlink(input_path)
            
            # Send the converted file
            return send_file(output_path, as_attachment=True, download_name=output_filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        except Exception as e:
            # Clean up on error
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            return f'Conversion error: {str(e)}', 500
    
    return 'Invalid file format. Please upload a .md or .markdown file', 400

@app.route('/convert-text', methods=['POST'])
def convert_text():
    try:
        data = request.get_json()
        if not data or 'markdown' not in data:
            return 'No markdown content provided', 400
        
        markdown_content = data['markdown']
        if not markdown_content.strip():
            return 'Empty markdown content', 400
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as input_file:
            input_file.write(markdown_content)
            input_path = input_file.name
        
        output_path = os.path.join(tempfile.gettempdir(), 'document.docx')
        
        try:
            # Convert markdown to docx
            pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
            
            # Clean up input file
            os.unlink(input_path)
            
            # Send the converted file
            return send_file(output_path, as_attachment=True, download_name='document.docx', 
                           mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        except Exception as e:
            # Clean up on error
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            return f'Conversion error: {str(e)}', 500
            
    except Exception as e:
        return f'Request error: {str(e)}', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True, threaded=True)