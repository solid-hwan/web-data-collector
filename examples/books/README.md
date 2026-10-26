# Books 수집 연습

대상은 https://books.toscrape.com/ 의 수집 연습용 가상 서점입니다. 표시 가격은 실제 판매·견적·시장 가격 자료로 해석하지 않습니다. 인증 없이 공개된 목록 최대2페이지와 상세1개만 별도 작업에 수집합니다.

제품 루트에서 실행합니다. 이 명령은 **외부 HTTP를 실제 호출**하며 자동 로컬 시험에는 포함되지 않습니다.

```bash
.venv/bin/sionlab-web-collector crawl --config examples/books/config.json --job /tmp/books-list.sqlite
.venv/bin/sionlab-web-collector crawl --config examples/books/detail-config.json --job /tmp/books-detail.sqlite
.venv/bin/sionlab-web-collector export --job /tmp/books-list.sqlite --output /tmp/books-list.xlsx
.venv/bin/sionlab-web-collector verify --job /tmp/books-list.sqlite --xlsx /tmp/books-list.xlsx
```

목록은 두 페이지 후 다음 URL을 남긴 partial 결과가 예상됩니다. 상세는 단일 항목입니다. 웹 페이지 구성과 결과 건수는 외부 상태에 따라 달라집니다. 실조회 결과는 상위 검증 기록에서 별도로 확인합니다. 차단 시 중단하며 우회하지 않습니다.

2026-10-24 실조회 확인: 목록 HTTP 2회로40건 저장(중복0·고유키누락0), 다음3페이지를 남긴 부분수집. 상세 HTTP1회로1건 저장. 두 SQLite 무결성과 두 XLSX 전체 레코드 복원 대조를 통과했습니다. 전체 사이트 수집이나 실제 판매가격 검증이 아닙니다. 실행 근거 ID: `owned-books-live-20261024T080720.823310Z-a57d88d6`; 공용 도구 루트 `docs/verification/runs/`에서 같은 ID의 JSON을 확인합니다. 실조회 원문 DB는 배포본에 포함하지 않습니다.
