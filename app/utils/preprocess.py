import pandas as pd
import os
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pandas import DataFrame as df

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
        csv_df = processed_df.to_csv(self.output_path, index=False)
        return processed_df

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
        split_token = "위 도움말이 도움이 되었나요?"
        if split_token in text:
            return text.split(split_token)[0].strip()
        return text.strip()

    def extract_keywords(self, text):
        start_token = "관련 도움말/키워드"
        end_token = "도움말 닫기"
        keywords = []
        if start_token in text and end_token in text:
            start_idx = text.index(start_token) + len(start_token)
            end_idx = text.index(end_token)
            keyword_block = text[start_idx:end_idx]
            keywords = [kw.strip() for kw in keyword_block.split('\n') if kw.strip()]
        return ";".join(keywords)

    def extract_category(self, text):
        m = re.match(r"^\[(.*?)\]", text)
        return m.group(1) if m else ""

    def clean_question(self, text):
        # [카테고리] 태그 제거
        return re.sub(r"^\[.*?\]\s*", "", text).strip()

    def preprocess_row(self, row):
        question = str(row['question']).strip()
        answer_raw = str(row['answer'])
        answer = self.extract_answer(answer_raw)
        keywords = self.extract_keywords(answer_raw)
        category = self.extract_category(question)
        clean_q = self.clean_question(question)
        return {
            "category": category,
            "question": clean_q,
            "answer": answer,
            "keyword": keywords
        }

