import json
import re
from pathlib import Path
from typing import Dict, Any
import openai
from bs4 import BeautifulSoup, NavigableString
from cfg import OPENAI_API_KEY, OPENAI_MODEL
from utils import should_skip_node

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 강화된 번역 프롬프트
SYSTEM_PROMPT = """You are a professional EN→KO technical translator.

Hard rules:
- Translate ONLY natural-language content to Korean.
- NEVER translate code, commands, file paths, JSON/YAML, logs, stack traces, configuration keys, environment variables, or inline code in backticks.
- Preserve all HTML tags and attributes EXACTLY (do not add/remove).
- Keep bold/italic/heading/list structure as-is.
- Keep product names, API/class/function identifiers, and code tokens in English.
- If a heading contains code tokens, translate only the natural-language part.
- Keep numbers, entities, and metric units accurate; don't localize code examples.
- If a segment looks like a "table used for code", skip translation.

Terminology:
- agent → 에이전트; agentic → 에이전트형; tool → 도구; orchestrator → 오케스트레이터; prompt → 프롬프트; reflection → 리플렉션.

Style:
- Clear, concise, and technically faithful. Avoid over-translation. When necessary, keep the English term in parentheses on first occurrence (e.g., 에이전트(agent))."""

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
    """텍스트 청크 번역 (캐시 활용)"""
    # 캐시 확인
    text_key = text.strip()
    if text_key in tm:
        return tm[text_key]
    
    # 빈 텍스트나 너무 짧은 텍스트는 스킵
    if not text_key or len(text_key) < 3:
        return text
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        translated = response.choices[0].message.content.strip()
        
        # 캐시에 저장
        tm[text_key] = translated
        return translated
        
    except Exception as e:
        print(f"[ERROR] 번역 실패: {e}")
        return text

def extract_translatable_texts(soup: BeautifulSoup) -> list:
    """번역 가능한 텍스트 노드 추출"""
    translatable_nodes = []
    
    for element in soup.find_all(string=True):
        if isinstance(element, NavigableString):
            if not should_skip_node(element):
                text = str(element).strip()
                if text and len(text) > 2:  # 의미있는 텍스트만
                    translatable_nodes.append(element)
    
    return translatable_nodes

def translate_html(input_html: Path, output_html: Path, tm_path: Path) -> None:
    """HTML 파일 번역"""
    print(f"[번역 시작] {input_html} -> {output_html}")
    
    # 번역 메모리 로드
    tm = load_translation_memory(tm_path)
    initial_tm_size = len(tm)
    
    # HTML 파싱
    with open(input_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # 번역 가능한 텍스트 노드 추출
    translatable_nodes = extract_translatable_texts(soup)
    print(f"[번역 대상] {len(translatable_nodes)}개 텍스트 노드")
    
    # 배치 번역을 위한 텍스트 그룹화
    batch_size = 10
    batches = []
    current_batch = []
    current_length = 0
    
    for node in translatable_nodes:
        text = str(node).strip()
        if current_length + len(text) > 3000 or len(current_batch) >= batch_size:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_length = 0
        
        current_batch.append((node, text))
        current_length += len(text)
    
    if current_batch:
        batches.append(current_batch)
    
    print(f"[배치 처리] {len(batches)}개 배치로 분할")
    
    # 배치별 번역 처리
    for i, batch in enumerate(batches, 1):
        print(f"[진행률] {i}/{len(batches)} 배치 처리 중...")
        
        # 배치 텍스트 결합
        batch_texts = [text for _, text in batch]
        combined_text = "\n\n---\n\n".join(batch_texts)
        
        # 번역
        translated_combined = translate_text_chunk(combined_text, tm)
        translated_parts = translated_combined.split("\n\n---\n\n")
        
        # 결과 적용
        for j, (node, original_text) in enumerate(batch):
            if j < len(translated_parts):
                translated_text = translated_parts[j].strip()
                if translated_text and translated_text != original_text:
                    node.replace_with(translated_text)
    
    # 번역 메모리 저장
    save_translation_memory(tm_path, tm)
    new_entries = len(tm) - initial_tm_size
    print(f"[TM 업데이트] {new_entries}개 새 항목 추가 (총 {len(tm)}개)")
    
    # 번역된 HTML 저장
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"[번역 완료] {output_html}")

