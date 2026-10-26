# 웹 데이터 수집기 활용 방법

이 문서는 제공된 수집·재개·내보내기를 다양한 목록에 적용하는 방법입니다. 외부 접근 없이 가상 예제를 먼저 확인한 뒤 사용 권한이 있는 공개 페이지에 설정을 맞춥니다. [계약](contracts.md)은 모든 활용 사례에 동일하게 적용됩니다.

## 1. 상품 비교와 교육 공지 실습

```bash
.venv/bin/python examples/run_examples.py --output /tmp/web-recipes-demo
```

로컬 HTTP 서버에서 가상 HTML을 읽습니다. `products/`, `education/`에 각각 job.sqlite·sample.jsonl·sample.csv·sample.xlsx가 생성됩니다. `verification.json`의 두 사례가 pass이고 `xlsx_exact_match=true`인지 확인합니다. 예제 출력 폴더는 재사용하지 않습니다.

## 2. 공개 상품·자료·공지 목록에 맞추기

| 목록 | 고유키 후보 | 필드 구성 | 주의 |
|---|---|---|---|
| 상품 | 상품코드 또는 안정적인 상세 URL | 이름·가격·통화·링크 | 가격은 문자열, 단위는 별도 필드 |
| 교육 공지 | 공지번호 | 제목·일정·대상·링크 | 제목만 고유키로 쓰면 같은 제목을 합칠 수 있음 |
| 문서 자료실 | 문서번호·판본의 복합키 | 제목·발행처·날짜·링크 | 첨부 URL 수집과 파일 다운로드는 다름 |
| 행사 일정 | 행사번호 또는 식별 가능한 복합키 | 이름·기간·장소·링크 | 날짜 추정·일정 자동등록은 제공하지 않음 |

고유키는 실제 페이지에서 안정적으로 확인할 수 있어야 합니다. 추정값으로 채우지 않습니다. HTML 구조를 보고 `item_selector`와 항목 내부 필드 selector를 지정합니다. 다음 페이지 링크가 없다면 `next_selector`를 생략합니다. 상세 URL은 필드로 저장되며 자동으로 방문하지 않습니다.

실제 수집 명령은 대상 페이지로 HTTP 요청을 보냅니다.

```bash
.venv/bin/web-data-collector crawl --config my-config.json --job ./jobs/research-001.sqlite
.venv/bin/web-data-collector resume --job ./jobs/research-001.sqlite
.venv/bin/web-data-collector export --job ./jobs/research-001.sqlite --output ./output/research-001.xlsx
.venv/bin/web-data-collector verify --job ./jobs/research-001.sqlite --xlsx ./output/research-001.xlsx
```

## 3. 한도·재개·정기 조사 설계

최대 페이지·항목 수는 실행당 한도입니다. 페이지 중간에서 멈추면 남은 원문은 DB 큐에 있고 resume이 이어갑니다. 실행을 자동 반복하는 스케줄러는 이 패키지에 포함하지 않습니다. 사용자의 스케줄러와 연결한다면 상태·partial·reason을 보고 중단·알림 정책을 따로 정하세요.

한 작업의 설정과 이미 처리한 페이지는 고정됩니다. 다음 날짜의 가격·공지 변화를 조사하려면 새 작업 DB로 시작하고 JSONL을 외부 분석 코드에서 비교합니다. 동일 DB 재개는 변경 감지·전체 재동기화가 아닙니다.

## 4. Python에 내장하기 — 외부 호출 없는 예제

가상 어댑터는 HTML과 실제로 읽은 URL의 튜플을 반환합니다. 이 예제는 두 항목 중 하나를 저장한 뒤 큐를 재개하고 Excel 원문을 대조합니다.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from sionlab_web_collector.core import collect, load_records
from sionlab_web_collector.exporting import export_job, read_xlsx


class Fixture:
    def fetch(self, url):
        html = '<article><b>001</b><p>가상 상품</p></article><article><b>002</b><p>다음 상품</p></article>'
        return html, url


config = {
    "start_url": "https://example.invalid/list",
    "item_selector": "article",
    "fields": {"id": {"selector": "b"}, "title": {"selector": "p"}},
    "unique_key": "id", "max_items": 1
}
with TemporaryDirectory() as temporary:
    job = Path(temporary) / "demo.sqlite"
    first = collect(job, config, adapter=Fixture())
    assert first["stored_count"] == 1 and first["pending_items"] == 1
    second = collect(job, resume=True, adapter=Fixture())
    assert second["stored_count"] == 2 and second["pending_items"] == 0
    xlsx = Path(temporary) / "demo.xlsx"
    export_job(job, xlsx)
    assert read_xlsx(xlsx) == load_records(job)
    print({"fixture_only": True, "rows": second["stored_count"], "xlsx_matches": True})
```

내부 API 경로 `sionlab_web_collector.*`는 새 공개명에서도 유지합니다. 실제 HTTP 어댑터를 쓰려면 `adapter` 주입을 생략하며, 이때는 네트워크 요청이 발생합니다.

## 5. Excel·분석 도구와 연결

Overview는 사람이 읽는 목록입니다. 원문 검증·프로그램 재사용은 JSONL 또는 `read_xlsx()`로 복원한 객체를 사용합니다. CSV의 각 셀도 JSON 값이므로 따옴표를 단순 삭제하거나 큰 금액을 숫자로 강제 변환하지 마세요. CSV와 함께 생성한 `.columns.json`을 보관합니다.

Python 표준 `json`이나 사용자가 선택한 오픈소스 분석 도구에서 추가 필터·집계를 할 수 있습니다. 이 패키지는 대시보드·외부 DB·일정등록·알림 발송을 자동으로 수행하지 않습니다.

## 6. 동적 목록과 확장 지점

HTTP로 항목이 보이지 않고 JavaScript 후에 나타나면 선택 Playwright 어댑터를 검토합니다. 설치·로컬 동작 확인은 README를 따릅니다. 단순 목록 대기 이외의 클릭·로그인·POST 기반 UI는 현재 지원 범위 밖입니다.

새 정규화나 내보내기 형식을 기여할 때는 `core.py`의 설정·정규화와 `exporting.py`의 원문 복원을 함께 확인하세요. 가상 HTML·기대값·차단·누락·기존 DB 호환 시험을 추가하고 [CONTRIBUTING.md](../CONTRIBUTING.md)에 따라 제출합니다.
