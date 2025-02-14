from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from analyzer import EnglishExamAnalyzer
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 기본 설정
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB 제한
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TIMEOUT'] = 600  # 10분

# uploads 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# analyzer 인스턴스 생성
analyzer = EnglishExamAnalyzer(api_key=os.getenv('OPENAI_API_KEY'))

# ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=2)

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
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"파일 저장 시작: {filename}")
        file.save(filepath)
        logger.info(f"파일 저장 완료: {filename}")
        
        logger.info("분석 시작")
        
        # 비동기 분석 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(
                    analyzer.analyze_exam(filepath),
                    timeout=app.config['TIMEOUT']
                )
            )
            return jsonify(result)
            
        except asyncio.TimeoutError:
            logger.error("분석 시간 초과")
            return jsonify({'error': '분석 시간이 초과되었습니다.'}), 500
        finally:
            loop.close()
            
            # 임시 파일 정리
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"임시 파일 삭제 완료: {filename}")
            except Exception as e:
                logger.error(f"임시 파일 삭제 실패: {str(e)}")
        
    except Exception as e:
        logger.error(f"분석 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': '파일 크기가 너무 큽니다.'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 