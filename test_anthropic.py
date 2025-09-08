#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import anthropic

# .env 파일 로드
load_dotenv()

# API 키 확인
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key 앞 10자리: {api_key[:10]}..." if api_key else "API Key가 설정되지 않음")

if not api_key:
    print("ANTHROPIC_API_KEY가 .env 파일에 설정되지 않았습니다.")
    exit(1)

# 클라이언트 초기화 테스트
try:
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Anthropic 클라이언트 초기화 성공")
    
    # 간단한 API 호출 테스트
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        temperature=0.1,
        messages=[
            {
                "role": "user",
                "content": "Hello, can you translate 'Hello World' to Korean?"
            }
        ]
    )
    
    print("✅ API 호출 성공!")
    print(f"응답: {response.content[0].text}")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print(f"오류 타입: {type(e).__name__}")

