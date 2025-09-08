import json
import re
from pathlib import Path
from typing import Dict, Any
import anthropic
from bs4 import BeautifulSoup, NavigableString
from cfg import ANTHROPIC_API_KEY
from utils import should_skip_node

# Anthropic 클라이언트 초기화
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 개선된 번역 프롬프트 - 코드 블록과 기술 문서에 특화
SYSTEM_PROMPT = """You are a professional technical translator specializing in AI and software engineering documentation, translating from English to Korean.

CRITICAL RULES:
1. **Code Preservation**: NEVER translate code, commands, file paths, JSON/YAML, logs, configuration keys, environment variables, or anything in backticks/code blocks
2. **HTML Structure**: Preserve ALL HTML tags and attributes EXACTLY (do not add/remove)
3. **Technical Terms**: Keep product names, API/class/function identifiers, and technical tokens in English
4. **Code Blocks**: Preserve formatting of code examples, especially those in boxes or special formatting
5. **Images**: Do not modify image tags or references
6. **Tables**: If a table contains code examples, preserve the code structure completely

TRANSLATION GUIDELINES:
- agent → 에이전트
- agentic → 에이전트형  
- tool → 도구
- orchestrator → 오케스트레이터
- prompt → 프롬프트
- reflection → 리플렉션
- pattern → 패턴
- workflow → 워크플로우
- pipeline → 파이프라인
- framework → 프레임워크

STYLE:
- Clear, natural Korean that maintains technical accuracy
- When first introducing English terms, use format: 한국어(English)
- Preserve sentence structure and paragraph breaks
- Keep numbered lists and bullet points intact

SPECIAL HANDLING:
- For code examples in boxes: Preserve exact formatting and indentation
- For command-line examples: Keep commands in English
- For API responses: Keep JSON/XML structure unchanged
- For configuration files: Keep syntax and keys unchanged"""

def load_translation_memory(tm_path: Path) -> Dict[str, str]:
    """번역 메모리 로드"""
    if tm_path.exists():
        try:
            with open(tm_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] TM 로드 실패: {e}")
    return {}

def save_translation_memory(tm_path: Path, tm: Dict[str, str]) -> None:
    """번역 메모리 저장"""
    try:
        with open(tm_path, 'w', encoding='utf-8') as f:
            json.dump(tm, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] TM 저장 실패: {e}")

def translate_text_chunk(text: str, tm: Dict[str, str]) -> str:
    """Claude를 사용한 텍스트 청크 번역 (캐시 활용)"""
    # 캐시 확인
    text_key = text.strip()
    if text_key in tm:
        return tm[text_key]
    
    # 빈 텍스트나 너무 짧은 텍스트는 스킵
    if not text_key or len(text_key) < 3:
        return text
    
    # 코드 블록이나 특수 형식인지 추가 확인
    if is_code_or_special_format(text_key):
        return text
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241218",
            max_tokens=4000,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate this technical content to Korean while preserving all formatting and code:\n\n{text}"
                }
            ]
        )
        
        translated = response.content[0].text.strip()
        
        # 캐시에 저장
        tm[text_key] = translated
        return translated
        
    except Exception as e:
        print(f"[ERROR] Claude 번역 실패: {e}")
        return text

def is_code_or_special_format(text: str) -> bool:
    """텍스트가 코드나 특수 형식인지 더 정확하게 판단"""
    text = text.strip()
    
    # 매우 짧은 텍스트
    if len(text) < 5:
        return True
    
    # 코드 패턴들
    code_indicators = [
        r'^\s*[{}\[\]();]',  # 시작이 특수문자
        r'^\s*\w+\s*[:=]\s*',  # key: value 형태
        r'^\s*[A-Z_]+\s*=',  # 환경변수 형태
        r'^\s*\$\s*\w+',  # shell 변수
        r'^\s*[a-zA-Z_]\w*\(',  # 함수 호출
        r'^\s*import\s+',  # import 문
        r'^\s*from\s+\w+',  # from 문
        r'^\s*def\s+\w+',  # 함수 정의
        r'^\s*class\s+\w+',  # 클래스 정의
        r'^\s*#.*',  # 주석
        r'^\s*//.*',  # 주석
        r'^\s*<!--.*-->',  # HTML 주석
        r'^\s*<[^>]+>.*</[^>]+>$',  # HTML 태그
    ]
    
    for pattern in code_indicators:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    # 특수 문자 비율이 높으면 코드
    special_chars = len(re.findall(r'[{}[\]();=<>]', text))
    if len(text) > 10 and special_chars / len(text) > 0.15:
        return True
    
    return False

def extract_translatable_texts(soup: BeautifulSoup) -> list:
    """번역 가능한 텍스트 노드 추출 (개선된 필터링)"""
    translatable_nodes = []
    
    for element in soup.find_all(string=True):
        if isinstance(element, NavigableString):
            # 기본 스킵 조건 확인
            if should_skip_node(element):
                continue
                
            text = str(element).strip()
            if not text or len(text) < 3:
                continue
                
            # 추가 코드/특수 형식 확인
            if is_code_or_special_format(text):
                continue
                
            # 부모 태그가 특정 클래스를 가진 경우 스킵
            parent = element.parent
            if parent and parent.get('class'):
                classes = parent.get('class')
                if any(cls in ['code', 'highlight', 'language-', 'hljs'] for cls in classes):
                    continue
            
            translatable_nodes.append(element)
    
    return translatable_nodes

def translate_html(input_html: Path, output_html: Path, tm_path: Path) -> None:
    """HTML 파일 번역 (Claude 사용)"""
    print(f"[Claude 번역 시작] {input_html} -> {output_html}")
    
    # 번역 메모리 로드
    tm = load_translation_memory(tm_path)
    initial_tm_size = len(tm)
    
    # HTML 파싱
    with open(input_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # 번역 가능한 텍스트 노드 추출
    translatable_nodes = extract_translatable_texts(soup)
    print(f"[번역 대상] {len(translatable_nodes)}개 텍스트 노드")
    
    # 개별 번역 처리 (더 정확한 컨텍스트 유지를 위해)
    for i, node in enumerate(translatable_nodes, 1):
        if i % 50 == 0:
            print(f"[진행률] {i}/{len(translatable_nodes)} 노드 처리 중...")
        
        original_text = str(node).strip()
        translated_text = translate_text_chunk(original_text, tm)
        
        if translated_text != original_text:
            node.replace_with(translated_text)
    
    # 번역 메모리 저장
    save_translation_memory(tm_path, tm)
    new_entries = len(tm) - initial_tm_size
    print(f"[TM 업데이트] {new_entries}개 새 항목 추가 (총 {len(tm)}개)")
    
    # 번역된 HTML 저장
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"[Claude 번역 완료] {output_html}")
