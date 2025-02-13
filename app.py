from flask import Flask, render_template, request, jsonify
import os
from analyzer import EnglishExamAnalyzer
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

api_key = os.getenv('OPENAI_API_KEY')
analyzer = EnglishExamAnalyzer(api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '선택된 파일이 없습니다.'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        result = analyzer.analyze_exam(filepath)
        os.remove(filepath)  # 분석 후 파일 삭제
        return jsonify(result)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)  # 에러 발생 시에도 파일 삭제
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True) 