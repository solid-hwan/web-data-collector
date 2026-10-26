# 변경 이력

## 0.3.0 — 2026-10-26

- 공개명을 웹 데이터 수집기로 통일하고 web-data-collector / python -m web_data_collector을 제공합니다.
- 기존 명령·Python 모듈과 저장·재개·Excel 복원 계약을 유지합니다.
- README·설치 예제·CI·배포 ZIP을 새 이름에 맞춥니다. 제작자·저작권 SIONLAB은 유지합니다.

## 0.2.0 — 2026-10-26

- Excel Overview 보기와 Collection 수집 범위·조건·내보낸 시각을 추가했습니다. 원문 복원용 시트는 유지합니다.
- 원문 URL은 클릭할 수 있고 식별자·큰 금액·수식 모양 문자열은 텍스트로 보존합니다.
- 기존 사용자를 위한 전환 안내와 독립 설치 CI를 추가했습니다.
- 기존 Excel의 시트 이름이 Overview인 경우도 복원할 수 있습니다. normal/write-only 보기 링크를 검증합니다.

# 변경 이력

## 0.1.0 — 2026-10-24

- SIONLAB 독립 Python CLI crawl/resume/export/verify 신규 작성.
- 순차 HTTP·선택 브라우저 어댑터, 설정 해시와 SQLite 원자 체크포인트.
- 페이지 중간 한도 재개, 중복·고유키누락·차단·선택자 실패 구분.
- JSONL·CSV·두 XLSX 모드 및 장문 조각·정확한 금액·중첩값 복원.
- 로컬 가상 상품/교육 예제와 저장 직전·직후 실제 프로세스 중단 회귀시험.

- 비동기 동적 목록의 선택자 대기와 실제 로컬 Chromium 회귀 예제 추가.
