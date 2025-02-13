import PyPDF2
from openai import OpenAI
from typing import Dict, Any
import json
import re

class EnglishExamAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = "asst_pjkcpLPv9Soy3KdaiEKle221"
        
    def count_characters(self, text: str) -> int:
        """영어 텍스트의 글자 수를 계산합니다 (공백 제외)"""
        english_text = re.sub(r'[^a-zA-Z]', '', text)
        return len(english_text)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF 파일에서 텍스트를 추출합니다."""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def analyze_exam(self, pdf_path: str) -> Dict[str, Any]:
        """시험지를 분석하여 요청된 정보를 반환합니다."""
        
        # PDF에서 텍스트 추출
        exam_text = self.extract_text_from_pdf(pdf_path)
        
        # 글자 수 계산
        total_characters = self.count_characters(exam_text)
        
        # 새로운 Thread 생성
        thread = self.client.beta.threads.create()
        
        # 메시지 추가
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=exam_text
        )
        
        # Assistant를 사용하여 실행
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        
        # 실행 완료 대기
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == 'completed':
                break
        
        # 응답 가져오기
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # 마지막 응답에서 JSON 추출
        try:
            response_content = messages.data[0].content[0].text.value
            # JSON 문자열 찾기
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                result = json.loads(json_str)
                # 직접 계산한 글자 수로 대체
                result['total_characters'] = total_characters
            else:
                result = {"error": "JSON 형식의 응답을 찾을 수 없습니다."}
        except Exception as e:
            result = {"error": f"응답 처리 중 오류 발생: {str(e)}"}
        
        return result 