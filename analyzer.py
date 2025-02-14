import PyPDF2
from openai import OpenAI
from typing import Dict, Any
import json
import re
import time
import logging
import os
import tiktoken

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EnglishExamAnalyzer:
    def __init__(self, api_key: str):
        # OpenAI 클라이언트 초기화 방식 변경
        self.client = OpenAI(
            api_key=api_key,
            default_headers={"Content-Type": "application/json"}
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")
        # 영어 시험지 분석 Assistant
        self.assistant_id = "asst_pjkcpLPv9Soy3KdaiEKle221"
        logger.info("EnglishExamAnalyzer 초기화됨")
        
    def analyze_exam(self, pdf_path: str) -> Dict[str, Any]:
        """시험지를 분석하여 요청된 정보를 반환합니다."""
        logger.info(f"파일 분석 시작: {pdf_path}")
        
        try:
            # PDF에서 텍스트 추출
            exam_text = self.extract_text_from_pdf(pdf_path)
            logger.info(f"텍스트 추출 완료: {len(exam_text)} 글자")
            
            # 글자 수 계산
            total_characters = self.count_characters(exam_text)
            
            # Thread 생성
            thread = self.client.beta.threads.create()
            logger.info(f"Thread 생성됨: {thread.id}")
            
            # 메시지 전송
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""다음 영어 시험지를 분석하여 JSON 형식으로 응답해주세요:

{exam_text}

다음 형식으로 응답해주세요:
{{
    "school_name": "학교명",
    "publisher": "출판사명",
    "grade": "학년",
    "exam_type": "시험 종류",
    "total_questions": 전체 문제 수,
    "question_types": {{
        "빈칸추론": {{"count": 0, "numbers": []}},
        "주제추론": {{"count": 0, "numbers": []}},
        "제목추론": {{"count": 0, "numbers": []}},
        "요지추론": {{"count": 0, "numbers": []}},
        "필자주장": {{"count": 0, "numbers": []}},
        "밑줄어휘": {{"count": 0, "numbers": []}},
        "밑줄어법": {{"count": 0, "numbers": []}},
        "문단요약": {{"count": 0, "numbers": []}},
        "순서배열": {{"count": 0, "numbers": []}},
        "문장삽입": {{"count": 0, "numbers": []}},
        "문장삭제": {{"count": 0, "numbers": []}},
        "영영풀이": {{"count": 0, "numbers": []}},
        "지문내용": {{"count": 0, "numbers": []}},
        "분위기/심경": {{"count": 0, "numbers": []}},
        "목적": {{"count": 0, "numbers": []}},
        "부적절한": {{"count": 0, "numbers": []}},
        "알 수 없는 정보": {{"count": 0, "numbers": []}},
        "답할 수 없는 질문": {{"count": 0, "numbers": []}}
    }},
    "question_format": {{
        "multiple_choice": {{"count": 0, "numbers": []}},
        "subjective": {{"count": 0, "numbers": []}}
    }},
    "question_scope": {{
        "범위_교과서": {{"chapters": [], "count": 0, "numbers": []}},
        "범위_모의고사": {{"chapters": [], "count": 0, "numbers": []}},
        "범위_부교재": {{"chapters": [], "count": 0, "numbers": []}}
    }},
    "total_characters": 0,
    "highest_difficulty_vocab": []
}}

반드시 JSON 형식으로만 응답해주세요."""
            )
            logger.info(f"메시지 전송됨: {message.id}")
            
            # Assistant 실행
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            logger.info(f"Run 시작됨: {run.id}")
            
            # 실행 완료 대기
            timeout = 180  # 3분
            start_time = time.time()
            
            while True:
                if time.time() - start_time > timeout:
                    raise Exception("분석 시간 초과")
                
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                logger.info(f"Run 상태: {run.status}")
                
                if run.status == 'completed':
                    break
                elif run.status in ['failed', 'expired', 'cancelled']:
                    raise Exception(f"Assistant 실행 실패: {run.status}")
                
                time.sleep(3)
            
            # 응답 가져오기
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            if not messages.data:
                raise Exception("응답 메시지가 없습니다")
            
            response_content = messages.data[0].content[0].text.value
            logger.info(f"응답 받음: {response_content[:200]}")
            
            # 응답 파싱
            try:
                # 마크다운 코드 블록 제거
                if "```" in response_content:
                    response_content = re.sub(r'```(?:json)?(.*?)```', r'\1', response_content, flags=re.DOTALL)
                response_content = response_content.strip()
                
                result = json.loads(response_content)
                result['total_characters'] = total_characters
                logger.info("응답 파싱 성공")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                return {
                    'school_name': '',
                    'publisher': '',
                    'grade': '',
                    'exam_type': '',
                    'total_questions': 0,
                    'question_types': {
                        '빈칸추론': {'count': 0, 'numbers': []},
                        '주제추론': {'count': 0, 'numbers': []},
                        '제목추론': {'count': 0, 'numbers': []},
                        '요지추론': {'count': 0, 'numbers': []},
                        '필자주장': {'count': 0, 'numbers': []},
                        '밑줄어휘': {'count': 0, 'numbers': []},
                        '밑줄어법': {'count': 0, 'numbers': []},
                        '문단요약': {'count': 0, 'numbers': []},
                        '순서배열': {'count': 0, 'numbers': []},
                        '문장삽입': {'count': 0, 'numbers': []},
                        '문장삭제': {'count': 0, 'numbers': []},
                        '영영풀이': {'count': 0, 'numbers': []},
                        '지문내용': {'count': 0, 'numbers': []},
                        '분위기/심경': {'count': 0, 'numbers': []},
                        '목적': {'count': 0, 'numbers': []},
                        '부적절한': {'count': 0, 'numbers': []},
                        '알 수 없는 정보': {'count': 0, 'numbers': []},
                        '답할 수 없는 질문': {'count': 0, 'numbers': []}
                    },
                    'question_format': {
                        'multiple_choice': {'count': 0, 'numbers': []},
                        'subjective': {'count': 0, 'numbers': []}
                    },
                    'question_scope': {
                        '범위_교과서': {'chapters': [], 'count': 0, 'numbers': []},
                        '범위_모의고사': {'chapters': [], 'count': 0, 'numbers': []},
                        '범위_부교재': {'chapters': [], 'count': 0, 'numbers': []}
                    },
                    'total_characters': total_characters,
                    'highest_difficulty_vocab': [],
                    'error': f'응답 파싱 실패: {str(e)}'
                }
                
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {str(e)}")
            return {
                'school_name': '',
                'publisher': '',
                'grade': '',
                'exam_type': '',
                'total_questions': 0,
                'question_types': {
                    '빈칸추론': {'count': 0, 'numbers': []},
                    '주제추론': {'count': 0, 'numbers': []},
                    '제목추론': {'count': 0, 'numbers': []},
                    '요지추론': {'count': 0, 'numbers': []},
                    '필자주장': {'count': 0, 'numbers': []},
                    '밑줄어휘': {'count': 0, 'numbers': []},
                    '밑줄어법': {'count': 0, 'numbers': []},
                    '문단요약': {'count': 0, 'numbers': []},
                    '순서배열': {'count': 0, 'numbers': []},
                    '문장삽입': {'count': 0, 'numbers': []},
                    '문장삭제': {'count': 0, 'numbers': []},
                    '영영풀이': {'count': 0, 'numbers': []},
                    '지문내용': {'count': 0, 'numbers': []},
                    '분위기/심경': {'count': 0, 'numbers': []},
                    '목적': {'count': 0, 'numbers': []},
                    '부적절한': {'count': 0, 'numbers': []},
                    '알 수 없는 정보': {'count': 0, 'numbers': []},
                    '답할 수 없는 질문': {'count': 0, 'numbers': []}
                },
                'question_format': {
                    'multiple_choice': {'count': 0, 'numbers': []},
                    'subjective': {'count': 0, 'numbers': []}
                },
                'question_scope': {
                    '범위_교과서': {'chapters': [], 'count': 0, 'numbers': []},
                    '범위_모의고사': {'chapters': [], 'count': 0, 'numbers': []},
                    '범위_부교재': {'chapters': [], 'count': 0, 'numbers': []}
                },
                'total_characters': total_characters,
                'highest_difficulty_vocab': [],
                'error': f'분석 중 오류 발생: {str(e)}'
            }

    def count_characters(self, text: str) -> int:
        """영어 텍스트의 글자 수를 계산합니다 (공백 제외)"""
        english_text = re.sub(r'[^a-zA-Z]', '', text)
        return len(english_text)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF 파일에서 텍스트를 추출합니다."""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"PDF 파일 읽기 오류: {str(e)}")

    def count_tokens(self, text):
        return len(self.encoding.encode(text)) 