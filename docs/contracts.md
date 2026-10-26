# 입력·출력 계약과 제한

## 설정

| 필드 | 계약 |
|---|---|
| start_url | HTTP(S) 시작 URL, 쿼리 포함 전체가 설정 해시에 반영됨 |
| item_selector | 페이지 목록 항목 CSS 선택자 |
| fields | 고유 필드명 → selector, 선택 attribute, 선택 normalize |
| selector | 항목 내부 CSS 선택자. `:self`는 목록 항목 자체 |
| normalize | text(공백정리), decimal/integer(정확한 문자열), json(중첩값), url(절대주소) |
| next_selector | href를 읽을 다음 페이지 링크. 생략하면 단일 페이지 |
| unique_key | 필드명 또는 필드명 배열. 정규화된 값 전체의 JSON을 식별자로 보존 |
| max_pages / max_items | 실행당 읽기 예산, 기본 2 / 50 |
| requests_per_second / concurrency | 기본1 / 1, 속도 최대1, 동시성1 고정 |
| adapter | http 기본, playwright 선택 |

설정 전체를 canonical JSON SHA-256으로 고정합니다. 기관·검색조건·선택자·한도를 바꾼 작업은 다른 SQLite 경로를 사용합니다. 민감한 인증정보·고객정보를 설정에 넣지 않습니다. 동일 작업 동시 실행은 OS 파일 잠금으로 거부하며 프로세스 종료 시 자동 해제됩니다. Linux/macOS fcntl을 사용합니다.

## 상태와 저장

SQLite `records`에는 identity·source_url·fields(각 raw, normalized, missing_reason)가 저장됩니다. `pages`는 완료한 페이지, `meta`는 설정·다음 URL·잔여 큐·카운터, `rejected`는 고유키 누락 원문과 사유를 보관합니다. 고유키 누락은 임의 식별자로 대체하지 않으며 정상 내보내기에는 포함되지 않습니다.

한 페이지 처리의 레코드 삽입·완료 표시·다음 위치·잔여 큐·카운터는 하나의 트랜잭션입니다. FULL 동기화와 WAL을 사용합니다. 커밋 직전 프로세스 중단은 페이지를 재조회하며, 직후 중단은 커밋된 위치부터 재개합니다. 이는 안정된 페이지 입력에 대한 무누락·무중복 보장입니다. 외부 사이트가 중단 전후 내용을 변경하면 동일한 스냅샷을 보장하지 않습니다.

응답은 `status`, `reason`, `stored_count`, `read_count`, `duplicate_count`, `missing_key_count`, `completed_pages`, `pending_items`, `next_url`, `partial`을 구분합니다. 사이트 전체 건수는 확인된 계약이 없으므로 `total_count: null`과 사유를 반환합니다. 실패가 있어도 이미 저장된 건수는 유지합니다. `status:complete`는 다음 링크까지 소비한 상태이며 고유키 누락이 있으면 `partial:true`와 `reason:missing_unique_keys`를 함께 반환합니다. export 응답도 원 작업 상태·사유·제외건수·rejected 원문 저장위치를 표시합니다. 알려진 0개 결과와 선택자 오류를 구분할 근거가 없으므로 목록 미검출은 실패입니다.

페이지 재방문 순환·다른 URL의 동일 목록 내용 반복·다른 origin의 다음 링크는 중단합니다. HTTP redirect는 추가 요청 없이 redirect_requires_review로 중단하므로 최종 공개 URL을 새 설정에 명시해야 합니다. 네트워크·HTTP·파싱 실패는 현재 위치를 보존합니다. 요청 실패를 자동으로 반복하지 않습니다. HTTP 응답은 최대10MB입니다. CSS 기반 범용 수집기로, 모든 CAPTCHA 변형을 식별할 수는 없습니다. 입력 비밀번호 요소, captcha ID/class/iframe, 대표 사람 확인·접근거절 문구를 중단 신호로 사용합니다.

## Excel과 CSV의 정확성

Excel/CSV의 각 데이터 셀은 **JSON 인코딩된 값**입니다. 문자열에는 따옴표가 보이며 큰 금액은 숫자로 바꾸지 않습니다. 모든 Excel 셀을 명시적으로 문자열형으로 저장해 수식 실행을 막습니다. JSONL은 원래 객체 구조를 유지합니다. CSV는 열 경로를 `.csv.columns.json`에 함께 저장합니다.

Excel은 `_columns` 시트에 열 이름과 원래 경로를, `_overflow` 시트에 30,000문자 단위 장문 조각을 보관합니다. 데이터 셀의 `@sionlab-overflow:행:열`은 참조입니다. `read_xlsx()` 또는 CLI `verify --xlsx`가 조각을 결합하고 JSON을 복원합니다. 이 두 보조 시트를 삭제하면 정확한 복원이 불가능합니다. 한글은 셀에서 그대로 읽을 수 있습니다. XML 비허용 제어문자·고립 surrogate·U+FFFE/U+FFFF는 JSON 이스케이프로 보존합니다. 열명은 `f번호:이름:raw/normalized/missing_reason`으로 충돌을 막고, 시트명 예약어·금지문자는 정리합니다. `normal`과 `write-only`는 같은 복원 계약입니다. 현재 export는 SQLite 전체 레코드를 메모리로 읽으므로 무한 스트리밍 제품은 아닙니다.

## 선택 동적 페이지

```bash
.venv/bin/python -m pip install -r requirements-browser.lock
.venv/bin/python -m playwright install chromium
```

ensurepip 없이 uv로 환경을 만들었다면 첫 명령은 `uv pip install --python .venv/bin/python -r requirements-browser.lock`으로 실행합니다.

설정 `adapter: "playwright"`를 사용합니다. 별도 새 브라우저 컨텍스트에서 초기 문서를 읽고 목록 선택자가 나타난 뒤 파싱합니다. 모든 허용 GET을 큐에 넣어 순차 처리하며 초당 최대1회로 제한합니다. 이미지·미디어·폰트·스타일시트와 GET 이외 요청은 보내지 않고, 서비스 워커·자동 redirect·재시도를 차단합니다. 하위 요청의 401·403·429도 즉시 중단합니다. 쿠키·인증·프록시·자동 로그인·은폐 기능은 없습니다. 따라서 스타일시트나 POST 요청에 의존하는 동적 사이트는 지원하지 않습니다. 선택자 등장 이후 모든 비동기 요청의 완료 판정·클릭·스크롤은 0.2.0 미지원입니다. 기본 자동 시험은 브라우저 어댑터의 가상 계약을 확인하며 별도 로컬 Chromium 시험은 지연된 목록을 확인합니다. 실제 외부 동적 사이트 동작은 미확인입니다.

## 지연된 동적 목록 확인

Playwright 어댑터는 초기 문서와 접근 차단을 확인한 뒤 설정의 `item_selector`가 DOM에 붙을 때까지 최대30초 기다립니다. 시간초과는 `dynamic_items_not_ready` 실패로 남깁니다. 선택 브라우저 의존성 설치 후 `python examples/check_browser.py`로 로컬 비동기 목록을 실제 브라우저에서 확인할 수 있습니다. 외부 동적 사이트 전체에 대한 검증은 아닙니다. API 기준: [Playwright page.wait_for_selector](https://playwright.dev/python/docs/api/class-page#page-wait-for-selector), [route.fetch](https://playwright.dev/python/docs/api/class-route#route-fetch).

## 0.2.0 보기용 시트

Overview는 정규화값을 읽기 쉽게 표시하며 Collection은 작업 설정·부분수집·다음 URL·UTC 내보낸 시각을 기록합니다. 원문 데이터 시트의 JSON 셀 인코딩은 바뀌지 않습니다. 원문을 읽는 도구는 첫 시트/활성 시트가 아닌 _columns의 헤더에 맞는 데이터 시트를 사용해야 합니다. 보기 시트의 장문은 표시만 축약하고, 빈칸은 누락 또는 정규화 실패일 수 있으므로 원문 missing_reason을 확인합니다.
