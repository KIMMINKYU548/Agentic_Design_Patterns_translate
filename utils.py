import re
import base64
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from typing import Union

# 모노스페이스 폰트 목록
MONO_FONTS = [
    "monospace", "courier", "consolas", "monaco", "menlo", 
    "dejavu sans mono", "liberation mono", "source code pro"
]

def is_codey_text(text: str) -> bool:
    """텍스트가 코드처럼 보이는지 휴리스틱으로 판단"""
    if not text or len(text.strip()) < 3:
        return False
    
    text = text.strip()
    
    # 코드 패턴들
    code_patterns = [
        r'^\w+\(\)',  # function()
        r'^\w+\.\w+',  # object.method
        r'[{}[\]();]',  # 괄호, 중괄호 등
        r'^\$\s',  # shell command
        r'^[A-Z_]+=["\']',  # environment variable
        r'^\w+:',  # key: value
        r'import\s+\w+',  # import statement
        r'from\s+\w+',  # from statement
        r'def\s+\w+',  # function definition
        r'class\s+\w+',  # class definition
        r'^\s*#\s',  # comment
        r'^\s*//',  # comment
        r'^\s*<!--',  # HTML comment
        r'^\s*\*\s',  # documentation
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    # 특수 문자 비율이 높으면 코드일 가능성
    special_chars = len(re.findall(r'[{}[\]();=<>]', text))
    if len(text) > 10 and special_chars / len(text) > 0.1:
        return True
    
    return False

def should_skip_node(node: NavigableString) -> bool:
    """번역을 건너뛸 노드인지 판단"""
    if not isinstance(node, NavigableString):
        return False
    
    parents = [p.name for p in node.parents if getattr(p, "name", None)]
    
    # 코드 관련 태그는 스킵
    if any(p in ("code", "pre", "kbd", "samp") for p in parents):
        return True
    
    # 테이블 셀에서 코드 같은 텍스트면 스킵
    if "td" in parents or "th" in parents:
        if is_codey_text(str(node)):
            return True
    
    # monospace 스타일 확인
    parent = node.parent
    if parent:
        style = (parent.get("style", "") or "").lower()
        if "font-family" in style and any(m in style for m in MONO_FONTS):
            return True
    
    return is_codey_text(str(node))

def inline_images_as_data_uri(soup: BeautifulSoup, base_dir: Path) -> None:
    """HTML의 이미지를 data URI로 인라인화"""
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src.startswith("data:"):
            continue
        
        img_path = base_dir / src
        if not img_path.exists():
            continue
        
        try:
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            # 파일 확장자로 MIME 타입 추정
            ext = img_path.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')
            
            b64_data = base64.b64encode(img_data).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{b64_data}"
            img["src"] = data_uri
            
        except Exception as e:
            print(f"[WARN] 이미지 인라인 실패: {img_path} - {e}")
            continue

