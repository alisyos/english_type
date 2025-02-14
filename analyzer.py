import PyPDF2
from openai import OpenAI
from typing import Dict, Any
import json
import re
import time
import logging
import os
import tiktoken
import asyncio
import gc
from io import BytesIO

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EnglishExamAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        # 3개의 Assistant ID 설정
        self.assistant_ids = {
            'basic': "asst_rFJYSZCis03y97Ggt6SMyz6e",  # 기본 정보 분석
            'format': "asst_xqgDNuRKRvPtyLR1U6OM8DQC", # 문제 형식과 출제 범위
            'types': "asst_GYvv8reXIB10ucoN38Uu3woE"   # 문제 유형
        }
        logger.info("EnglishExamAnalyzer 초기화됨")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF 파일에서 텍스트를 추출합니다."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"PDF 파일 읽기 오류: {str(e)}")
            raise

    async def analyze_with_assistant(self, thread_id: str, assistant_id: str, exam_text: str) -> Dict:
        """Assistant를 사용하여 분석을 수행합니다."""
        try:
            # 메시지 전송
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=exam_text
            )
            logger.info(f"메시지 전송됨: {message.id}")
            
            # Assistant 실행
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            logger.info(f"Run 시작됨: {run.id}")
            
            # 실행 완료 대기
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == 'completed':
                    break
                elif run.status in ['failed', 'expired', 'cancelled']:
                    raise Exception(f"Assistant 실행 실패: {run.status}")
                
                await asyncio.sleep(3)
            
            # 응답 가져오기
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            if not messages.data:
                raise Exception("응답 메시지가 없습니다")
            
            response_content = messages.data[0].content[0].text.value
            
            # 응답 파싱
            if "```" in response_content:
                response_content = re.sub(r'```(?:json)?(.*?)```', r'\1', response_content, flags=re.DOTALL)
            response_content = response_content.strip()
            
            return json.loads(response_content)
            
        except Exception as e:
            logger.error(f"Assistant 분석 중 오류: {str(e)}")
            raise

    async def analyze_exam(self, pdf_path: str) -> Dict[str, Any]:
        """시험지를 분석하여 요청된 정보를 반환합니다."""
        logger.info(f"파일 분석 시작: {pdf_path}")
        
        try:
            # PDF 텍스트 추출
            exam_text = self.extract_text_from_pdf(pdf_path)
            logger.info(f"텍스트 추출 완료: {len(exam_text)} 글자")
            
            # Thread 생성
            thread = self.client.beta.threads.create()
            logger.info(f"Thread 생성됨: {thread.id}")
            
            # 각 Assistant로 순차적 분석 수행
            basic_info = await self.analyze_with_assistant(thread.id, self.assistant_ids['basic'], exam_text)
            format_info = await self.analyze_with_assistant(thread.id, self.assistant_ids['format'], exam_text)
            types_info = await self.analyze_with_assistant(thread.id, self.assistant_ids['types'], exam_text)
            
            # 결과 병합
            result = {
                **basic_info,
                'question_format': format_info.get('question_format', {}),
                'question_scope': format_info.get('question_scope', {}),
                'question_types': types_info.get('question_types', {})
            }
            
            return result
            
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {str(e)}")
            raise

    def count_characters(self, text: str) -> int:
        """영어 텍스트의 글자 수를 계산합니다 (공백 제외)"""
        english_text = re.sub(r'[^a-zA-Z]', '', text)
        return len(english_text)
        
    def count_tokens(self, text):
        return len(self.encoding.encode(text)) 