from flask import Flask, render_template, request, jsonify
import os
from analyzer import EnglishExamAnalyzer
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['TIMEOUT'] = 300

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
        # 결과 검증
        required_fields = [
            'school_name', 'publisher', 'grade', 'exam_type', 'total_questions',
            'question_types', 'question_format', 'question_scope',
            'total_characters', 'highest_difficulty_vocab'
        ]
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f'필수 필드 {field}가 누락되었습니다.')
        
        # question_types 검증
        question_type_fields = [
            '빈칸추론', '주제추론', '제목추론', '요지추론', '필자주장',
            '밑줄어휘', '밑줄어법', '문단요약', '순서배열', '문장삽입',
            '문장삭제', '영영풀이', '지문내용', '분위기/심경', '목적',
            '부적절한', '알 수 없는 정보', '답할 수 없는 질문'
        ]
        
        for type_field in question_type_fields:
            if type_field not in result['question_types']:
                result['question_types'][type_field] = {'count': 0, 'numbers': []}
        
        os.remove(filepath)  # 분석 후 파일 삭제
        return jsonify(result)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)  # 에러 발생 시에도 파일 삭제
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True) 