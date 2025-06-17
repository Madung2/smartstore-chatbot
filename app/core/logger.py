import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

# 로그 포맷 설정
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 로거 인스턴스 생성
logger = logging.getLogger('smartstore-chatbot')
logger.setLevel(logging.INFO)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# 로그 디렉토리 생성
LOG_DIR = '/logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 파일명에 날짜 포함
current_date = datetime.now().strftime('%Y-%m-%d')
log_file = os.path.join(LOG_DIR, f'chatbot_{current_date}.log')

# 날짜별 파일 핸들러 설정
file_handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',  # 자정에 새로운 파일 생성
    interval=1,       # 1일 간격
    backupCount=30,   # 30일치 보관
    encoding='utf-8'
)

# 로그 파일명 형식 지정
file_handler.suffix = "%Y-%m-%d"

file_handler.setFormatter(log_format)
file_handler.flush = True
logger.addHandler(file_handler)

# 다른 모듈에서 import할 수 있도록 logger 인스턴스 export
__all__ = ['logger']
