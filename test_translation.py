#!/usr/bin/env python3

import sys
from pathlib import Path
from translate_html_claude import translate_html

def test_translation():
    # 파일 경로 설정
    work_dir = Path("work")
    master_en_html = work_dir / "master_en.html"
    master_ko_html = work_dir / "master_ko_test.html"
    tm_path = work_dir / "tm_test.json"
    
    # 영어 HTML 파일 존재 확인
    if not master_en_html.exists():
        print(f"❌ 영어 HTML 파일이 없습니다: {master_en_html}")
        print("먼저 DOCX 병합과 HTML 변환을 완료해야 합니다.")
        return False
    
    print(f"✅ 영어 HTML 파일 확인: {master_en_html}")
    print(f"📄 파일 크기: {master_en_html.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 번역 시도
    try:
        print("🔄 Claude 번역 시작...")
        translate_html(master_en_html, master_ko_html, tm_path)
        print("✅ 번역 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 번역 실패: {e}")
        print(f"오류 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_translation()

