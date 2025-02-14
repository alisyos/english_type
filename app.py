from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from analyzer import EnglishExamAnalyzer
import asyncio
import gc  # 가비지 컬렉션 추가

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
        
        try:
            # 파일 저장 전 메모리 정리
            gc.collect()
            
            file.save(filepath)
            
            # 타임아웃 설정과 함께 분석 실행
            result = await asyncio.wait_for(
                analyzer.analyze_exam(filepath),
                timeout=600  # 10분으로 증가
            )
            
            # 파일 삭제 및 메모리 정리
            if os.path.exists(filepath):
                os.remove(filepath)
            gc.collect()
            
            return jsonify(result)
            
        except asyncio.TimeoutError:
            if os.path.exists(filepath):
                os.remove(filepath)
            gc.collect()
            return jsonify({'error': '분석 시간이 초과되었습니다.'}), 500
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            gc.collect()
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        gc.collect()
        return jsonify({'error': str(e)}), 500

# 메모리 정리를 위한 엔드포인트 추가
@app.route('/cleanup', methods=['POST'])
def cleanup():
    gc.collect()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True) 