"""
legacy_report.py — 서강카페 월간 매출 리포트 생성 스크립트 (레거시 버전)

[AI 오케스트레이션 스튜디오 · 5주차 과제 1 — 리팩터링 대상 파일]

이 스크립트는 '동작은 하지만 보안상 위험한' 레거시 코드의 전형이다.
과제: 비밀 값을 .env 로 분리하고, .gitignore / .env.example 을 작성하여
      python-dotenv 로 읽어 오도록 리팩터링한다. (강의노트 3.4절)

※ 아래 API 키·DB 비밀번호는 실제 권한이 전혀 없는 교육용 더미 값이다.
※ 표준 라이브러리만 사용하며, 실제 DB·외부 API에는 접속하지 않는다.
   (DB는 메모리 내 샘플 데이터로, LLM 호출은 모의 응답으로 대체)

실행:  python legacy_report.py
"""

import os
import sqlite3
from urllib.parse import urlparse
from dotenv import load_dotenv

# FIX: dotenv 라이브러리를 사용해 .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# FIX: 하드코딩된 API 키와 DB 주소를 제거하고, os.getenv를 통해 환경 변수에서 안전하게 가져옵니다.
API_KEY = os.getenv("ANTHROPIC_API_KEY")
DB_URL = os.getenv("DB_URL")
MODEL = "claude-sonnet-4-5"
REPORT_MONTH = "2026-09"

# FIX: 환경 변수가 정상적으로 로드되었는지 확인하는 방어적 코드를 추가했습니다.
if API_KEY is None or DB_URL is None:
    raise RuntimeError("환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

def connect_db(db_url):
    # FIX: 비밀번호가 포함된 DB_URL 전체가 로그에 출력되지 않도록 디버그 메시지를 안전하게 수정했습니다.
    print(f"[DEBUG] DB 접속 시도") 
    info = urlparse(db_url)
    print(f"[INFO] 호스트 {info.hostname}:{info.port} / DB {info.path.lstrip('/')}")
    print("[데모] 실제 DB 대신 내장 샘플 데이터를 사용합니다.")

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sales (sold_on TEXT, category TEXT, amount INTEGER)")
    sample = [
        ("2026-09-01", "음료", 4500), ("2026-09-01", "음료", 5000),
        ("2026-09-02", "디저트", 6500), ("2026-09-03", "음료", 4500),
        ("2026-09-05", "원두", 18000), ("2026-09-07", "디저트", 5500),
        ("2026-09-10", "음료", 5500), ("2026-09-12", "원두", 22000),
        ("2026-09-15", "음료", 4500), ("2026-09-18", "디저트", 7000),
        ("2026-09-21", "음료", 5000), ("2026-09-25", "원두", 18000),
        ("2026-08-30", "음료", 4500), 
    ]
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?)", sample)
    return conn

def monthly_summary(conn, month):
    rows = conn.execute(
        """SELECT category, COUNT(*), SUM(amount)
           FROM sales
           WHERE substr(sold_on, 1, 7) = ?
           GROUP BY category
           ORDER BY SUM(amount) DESC""",
        (month,),
    ).fetchall()
    return [{"category": c, "count": n, "total": t} for c, n, t in rows]

def request_llm_comment(summary, api_key):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # FIX: 보안상 API 키 전체가 콘솔/로그에 남지 않도록 출력 메시지를 안전하게 수정했습니다.
    print(f"[DEBUG] API 요청 헤더 생성 완료 (보안상 상세 출력 생략)") 
    top = summary[0]["category"] if summary else "없음"
    print(f"[데모] {MODEL} 호출을 생략하고 모의 응답을 사용합니다.")
    return f"[MOCK] 이번 달 매출 1위 카테고리는 '{top}'입니다. 상위 품목 재고를 점검하세요."

def print_report(month, summary, comment):
    total = sum(r["total"] for r in summary)
    print("\n" + "=" * 46)
    print(f"  서강카페 월간 매출 리포트 ({month})")
    print("=" * 46)
    for r in summary:
        share = r["total"] / total * 100 if total else 0
        print(f"  {r['category']:<6} {r['count']:>3}건  {r['total']:>8,}원  ({share:4.1f}%)")
    print("-" * 46)
    print(f"  합계            {total:>8,}원")
    print(f"\n  AI 코멘트: {comment}")
    print("=" * 46)

def main():
    conn = connect_db(DB_URL)
    summary = monthly_summary(conn, REPORT_MONTH)
    comment = request_llm_comment(summary, API_KEY)
    print_report(REPORT_MONTH, summary, comment)
    conn.close()

if __name__ == "__main__":
    main()