import pandas as pd
import os
import re
from abc import ABC, abstractmethod

class BasePreprocessor(ABC):
    """
    데이터셋 전처리 기본 클래스
    
    Attributes:
        input_path (str): 입력 파일 경로
        output_path (str): 출력 파일 경로
        
    """
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path

    @abstractmethod
    def preprocess_row(self, row):
        """각 row에 대한 전처리 로직을 구현 (dict 반환)"""
        pass

    def run(self):
        df = pd.read_csv(self.input_path)
        processed = []
        for _, row in df.iterrows():
            processed.append(self.preprocess_row(row))
        processed_df = pd.DataFrame(processed)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        processed_df.to_csv(self.output_path, index=False)
        return len(processed_df)

class SmartstorePreprocessor(BasePreprocessor):
    """
    Smartstore 데이터셋 전처리 클래스 , 
    "위 도움말이 도움이 되었나요" 기준으로 답변 추출, 관련 도움말/키워드 추출
    
    Attributes:
        input_path (str): 입력 파일 경로
        output_path (str): 출력 파일 경로
        
    """
    def __init__(self, input_path, output_path):
        super().__init__(input_path, output_path)

    def extract_answer(self, text):
        # "위 도움말이 도움이 되었나요?" 이전 텍스트만 추출
        split_token = "위 도움말이 도움이 되었나요?"
        if split_token in text:
            return text.split(split_token)[0].strip()
        return text.strip()

    def extract_keywords(self, text):
        # "관련 도움말/키워드" ~ "도움말 닫기" 사이 텍스트 추출 후 줄바꿈 split
        start_token = "관련 도움말/키워드"
        end_token = "도움말 닫기"
        keywords = []
        if start_token in text and end_token in text:
            start_idx = text.index(start_token) + len(start_token)
            end_idx = text.index(end_token)
            keyword_block = text[start_idx:end_idx]
            # 줄바꿈으로 split, 공백/빈줄 제거
            keywords = [kw.strip() for kw in keyword_block.split('\n') if kw.strip()]
        return keywords

    def preprocess_row(self, row):
        question = str(row['question']).strip()
        answer_raw = str(row['answer'])
        answer = self.extract_answer(answer_raw)
        keywords = self.extract_keywords(answer_raw)
        return {
            "question": question,
            "answer": answer,
            "keyword": ";".join(keywords)  # CSV 저장시 리스트 대신 세미콜론 구분 문자열
        }

