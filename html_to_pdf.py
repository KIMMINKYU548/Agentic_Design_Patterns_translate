from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

async def html_to_pdf_async(html_path: Path, pdf_path: Path) -> None:
    """HTML을 PDF로 변환 (비동기)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # HTML 파일 로드
        await page.goto(f"file://{html_path.absolute()}")
        
        # PDF 생성 옵션
        pdf_options = {
            "path": str(pdf_path),
            "format": "A4",
            "print_background": True,
            "margin": {
                "top": "1in",
                "bottom": "1in", 
                "left": "0.8in",
                "right": "0.8in"
            },
            "display_header_footer": True,
            "header_template": """
            <div style="font-size: 10px; margin: 0 auto; width: 100%; text-align: center;">
                <span>Agentic Design Patterns - Korean Edition</span>
            </div>
            """,
            "footer_template": """
            <div style="font-size: 10px; margin: 0 auto; width: 100%; text-align: center;">
                <span class="pageNumber"></span> / <span class="totalPages"></span>
            </div>
            """
        }
        
        await page.pdf(**pdf_options)
        await browser.close()

def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """HTML을 PDF로 변환 (동기 래퍼)"""
    print(f"[PDF 변환] {html_path} -> {pdf_path}")
    
    # 출력 디렉토리 생성
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 비동기 함수 실행
    asyncio.run(html_to_pdf_async(html_path, pdf_path))
    
    print(f"[PDF 완료] {pdf_path.absolute()}")

