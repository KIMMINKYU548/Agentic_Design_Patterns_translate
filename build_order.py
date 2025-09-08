from pathlib import Path
import re
from typing import List

# 사용자가 지정한 '상위 섹션' 순서 (파일/폴더 명에 포함되기만 해도 매칭)
# Part/Appendix 항목은 폴더 하위의 Chapter들을 '자연 정렬'로 모두 포함
TOC_ORDER = [
    "Dedication",
    "Acknowledgment",
    "Foreword",
    "A Thought Leader",
    "Introduction",
    "What makes an AI system an Agent",
    ("Part One", "chapters"),
    ("Part Two", "chapters"),
    ("Part Three", "chapters"),
    ("Part Four", "chapters"),
    ("Appendix", "chapters"),
    "Conclusion",
    "Glossary",
    "Index of Terms",
    "Online Contribution - Frequently Asked Questions- Agentic Design Patterns",
]

DOCX_PAT = re.compile(r"\.docx$", re.I)

def natural_key(s: str):
    # "Chapter 10 ..." 이 "Chapter 2 ..." 뒤로 가도록 자연 정렬 키
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def find_one_file(root: Path, keyword: str) -> Path | None:
    # 상위 폴더 전체를 훑어 '파일명'에 keyword가 포함된 단일 파일 탐색
    cands = [p for p in root.rglob("*.docx") if keyword.lower() in p.stem.lower() and p.is_file()]
    if not cands:
        return None
    # 가장 짧은 경로/가까운 깊이/자연 정렬로 우선 선택
    cands.sort(key=lambda p: (len(p.parts), natural_key(p.name)))
    return cands[0]

def find_dir(root: Path, keyword: str) -> Path | None:
    # 폴더명에 keyword가 포함된 폴더 찾기
    dirs = [d for d in root.rglob("*") if d.is_dir() and keyword.lower() in d.name.lower()]
    if not dirs:
        return None
    dirs.sort(key=lambda d: (len(d.parts), d.name.lower()))
    return dirs[0]

def list_chapters_in_dir(dirpath: Path) -> List[Path]:
    # 폴더의 docx를 챕터 순서대로 자연 정렬해 나열
    docs = [p for p in dirpath.glob("*.docx") if p.is_file()]
    docs.sort(key=lambda p: natural_key(p.name))
    return docs

def build_order(root: Path) -> List[Path]:
    ordered: List[Path] = []
    for item in TOC_ORDER:
        if isinstance(item, tuple):
            # ("Part One", "chapters") 같은 항목
            section, kind = item
            d = find_dir(root, section)
            if d is None:
                print(f"[WARN] 폴더 없음: {section}")
                continue
            if kind == "chapters":
                chs = list_chapters_in_dir(d)
                if not chs:
                    print(f"[WARN] 챕터 파일 없음: {d}")
                ordered.extend(chs)
            else:
                print(f"[WARN] 알 수 없는 kind: {item}")
        else:
            # 단일 파일 매칭
            f = find_one_file(root, item)
            if f is None:
                print(f"[WARN] 파일 없음: {item}")
                continue
            ordered.append(f)
    # 중복 제거(앞쪽 우선)
    seen, uniq = set(), []
    for p in ordered:
        if p not in seen:
            uniq.append(p); seen.add(p)
    return uniq

