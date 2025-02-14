from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from analyzer import EnglishExamAnalyzer
import asyncio

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TIMEOUT'] = 300

# uploads 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# analyzer 인스턴스 생성
analyzer = EnglishExamAnalyzer(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
async def analyze():
    try:
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
            # 비동기로 분석 실행
            result = await analyzer.analyze_exam(filepath)
            
            # 임시 파일 삭제
            os.remove(filepath)
            
            return jsonify(result)
            
        except Exception as e:
            # 에러 발생 시 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except:
                pass
            raise e
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 