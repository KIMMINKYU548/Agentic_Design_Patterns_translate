import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 읽기
SRC_DIR = os.getenv("SRC_DIR", "/Users/kimminkyu/Desktop/Develop and Data analyze/Cursor/Agentic_Design_Patterns_book_crawling")
WORK = Path("work")
OUT = Path("output")
ASSETS = Path("assets")

# Mammoth 스타일 맵 (코드 블록 스타일 처리)
MAMMOTH_STYLE_MAP = """
p[style-name='Code'] => pre.code
p[style-name='Code Block'] => pre.code-block
p[style-name='Source Code'] => pre.source-code
p[style-name='Console'] => pre.console
span[style-name='Code'] => code
span[style-name='Inline Code'] => code
"""

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Anthropic 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
