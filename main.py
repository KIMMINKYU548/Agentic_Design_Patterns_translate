from pathlib import Path
from bs4 import BeautifulSoup

from cfg import SRC_DIR, WORK, OUT, ASSETS
from build_order import build_order
from merge_to_html import merge_docx_in_order, master_docx_to_html
from translate_html_claude import translate_html
from html_to_pdf import html_to_pdf
from utils import inline_images_as_data_uri

def ensure_dirs():
    for d in [WORK, OUT]:
        d.mkdir(parents=True, exist_ok=True)

def run():
    ensure_dirs()

    # 0) 사용자가 지정한 목차 순서로 파일 목록 구성
    file_list = build_order(Path(SRC_DIR))
    if not file_list:
        raise SystemExit(f"No docx files found under {SRC_DIR}")
    print("[ORDER] Total files:", len(file_list))
    for p in file_list[:5]: print("  ", p.name, "…")
    if len(file_list) > 5: print("  ...")

    master_docx = WORK / "master_en.docx"
    master_en_html = WORK / "master_en.html"
    master_ko_html = WORK / "master_ko.html"
    tm_path = WORK / "tm.json"
    out_pdf = OUT / "Agentic_Design_Patterns_KO.pdf"

    # 1) 병합 (표지/목차 배치)
    cover_docx = ASSETS / "cover.docx"  # 있으면 사용
    toc_docx   = ASSETS / "toc.docx"    # 있으면 사용
    master_docx, insert_auto_toc = merge_docx_in_order(
        file_list, master_docx, cover_docx=cover_docx, toc_docx=toc_docx
    )
    print(f"[OK] Merged: {master_docx}")

    # 2) HTML 변환 (+ 자동 TOC 옵션)
    master_docx_to_html(master_docx, master_en_html, insert_auto_toc)
    print(f"[OK] To HTML: {master_en_html}")

    # 3) 이미지 인라인(경로 문제 예방)
    soup = BeautifulSoup(master_en_html.read_text(encoding="utf-8"), "lxml")
    inline_images_as_data_uri(soup, master_en_html.parent)
    master_en_html.write_text(str(soup), encoding="utf-8")

    # 4) 번역(코드/명령/코드표 스킵) + 캐시
    translate_html(master_en_html, master_ko_html, tm_path)
    print(f"[OK] Translated HTML: {master_ko_html}")

    # 5) PDF 출력(페이지번호/한글폰트)
    html_to_pdf(master_ko_html, out_pdf)
    print(f"[DONE] PDF: {out_pdf.resolve()}")

if __name__ == "__main__":
    run()
