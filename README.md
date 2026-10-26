# 웹 데이터 수집기 0.3.0

**웹 목록 수집과 Excel 저장**을 위한 MIT 라이선스 Python 도구입니다. 공개 저장소·패키지·실행 명령은 `web-data-collector`입니다. 제작자·저작권자는 SIONLAB입니다.

JSON 설정으로 목록·필드·다음 페이지를 지정하고 SQLite에 저장합니다. 실행이 중단되거나 한도에 도달하면 같은 작업을 재개하며, 원문·정규화값·누락 사유를 Excel·CSV·JSONL로 내보냅니다. 특정 AI 서비스·시온랩 계정 없이 CLI와 Python으로 사용할 수 있습니다.

[빠른 시작](#빠른-시작) · [설정](#설정-작성) · [활용 방법](docs/recipes.md) · [계약과 제한](docs/contracts.md) · [전환 안내](docs/migration.md) · [기여하기](CONTRIBUTING.md)

## 한눈에 보는 사용 흐름

**공개 상품 목록에서 이름·가격·링크를 모아 엑셀에서 비교하거나, 교육 공지를 목록으로 정리할 수 있습니다.**

```mermaid
flowchart LR
    A["1. 웹 목록 고르기"] --> B["2. 항목 고르기"]
    B --> C["3. 자료 모으기"]
    C --> D["4. 엑셀로 확인하기"]
```

가져올 웹 목록과 이름·가격·날짜 같은 항목을 정하면, 도구가 자료를 모아 파일로 저장합니다. 엑셀에서 목록을 읽고 비교할 수 있습니다.

처음에는 해당 웹페이지에 맞는 수집 설정이 필요합니다. [가상 예제](docs/recipes.md#1-상품-비교와-교육-공지-실습)로 먼저 사용 흐름을 익힐 수 있습니다.

중간에 멈춘 작업은 상태와 남은 한도를 확인한 뒤 이어갈 수 있습니다. 파일이 만들어졌더라도 자료가 일부만 모였을 수 있으므로 수집 상태를 함께 확인하세요.

[상황별 활용 예](docs/recipes.md) · [개발자용 상세 처리 순서](docs/diagrams.md)

## 활용할 수 있는 일

| 목적 | 설정할 필드 예 | 결과 활용 |
|---|---|---|
| 공개 상품 목록 비교 | 상품코드·명칭·가격·URL | 가격 원문과 정규화값 대조 |
| 교육·행사 공지 정리 | 공지번호·제목·기간·링크 | Excel 목록과 원문 링크 검토 |
| 공개 문서·자료 목록 정리 | 문서번호·제목·발행처·URL | 중복을 구분한 자료 인덱스 |
| 반복 조사·후속 분석 | 확인 가능한 고유키·업무별 필드 | 날짜별 별도 작업을 분석 파이프라인에 전달 |
| 수집 실습·자동화 개발 | 가상 HTML·CSS 선택자 | 외부 접속 없는 재개·내보내기 실습 |

범용 검색엔진·AI 추출·사이트 자동 탐색 도구는 아닙니다. 사용자가 반복 목록의 CSS 구조를 알아야 합니다. 링크는 필드로 저장할 수 있지만 상세 페이지 자동 순회·파일 다운로드·로그인·클릭·스크롤은 제공하지 않습니다.

## 빠른 시작

Python 3.10 이상과 Linux/macOS 파일 잠금(`fcntl`)이 필요합니다. 네이티브 Windows는 미지원이며 WSL에서 실행할 수 있습니다. CI는 Ubuntu Python 3.11·3.12에서 실행합니다.

```bash
git clone https://github.com/solid-hwan/web-data-collector.git
cd web-data-collector
python3 setup-lab.py
.venv/bin/web-data-collector --help
.venv/bin/python -m web_data_collector --help
.venv/bin/python examples/run_examples.py --output /tmp/web-data-collector-demo
```

`setup-lab.py`는 제품의 `.venv`에만 설치합니다. 의존성 설치에는 네트워크가 필요하며 가상 예제는 로컬 HTTP 자료만 사용합니다. 상품 비교·교육 공지 두 예제를 실행하고 JSONL·CSV·Excel을 생성하여 원문을 다시 읽어 대조합니다. 같은 출력 폴더로 예제를 재실행하면 기존 작업을 덮어쓰지 않도록 거부하므로 새 경로를 지정하세요.

[Releases](https://github.com/solid-hwan/web-data-collector/releases)의 검증 ZIP을 압축 해제한 폴더에서도 `python3 setup-lab.py`를 사용할 수 있습니다. PyPI 배포는 하지 않습니다. 직접 관리하는 가상환경에서는 다음 명령으로 로컬 소스를 설치합니다.

```bash
python -m pip install -r requirements.lock
python -m pip install --no-build-isolation --no-deps .
```

## 설정 작성

[config.template.json](config.template.json)을 복사해 실제 공개 목록에 맞춥니다. 다음 URL은 자리표시자이므로 그대로 외부 수집에 사용할 수 없습니다.

```json
{
  "start_url": "https://example.invalid/list",
  "item_selector": "article",
  "fields": {
    "id": {"selector": ".id"},
    "title": {"selector": "h2"},
    "url": {"selector": "a", "attribute": "href", "normalize": "url"}
  },
  "unique_key": "id",
  "next_selector": "a.next",
  "max_pages": 2,
  "max_items": 50,
  "requests_per_second": 1,
  "concurrency": 1,
  "adapter": "http"
}
```

| 항목 | 의미 |
|---|---|
| item_selector | 반복 항목 하나를 선택하는 CSS |
| fields | 항목 안에서 읽을 필드별 selector·attribute·normalize |
| unique_key | 고유 필드명 또는 필드명 배열, 누락행은 별도 보관 |
| next_selector | 다음 페이지 링크, 없으면 단일 페이지 |
| normalize | text / decimal / integer / json / url |
| max_pages / max_items | 실행당 한도, 기본2페이지·50읽은항목 |
| requests_per_second / concurrency | 초당 최대1회·순차1개 |

필드 selector `:self`는 항목 자체입니다. 큰 금액은 부동소수점으로 바꾸지 않습니다. 설정은 작업 생성 시 해시로 고정되므로 재개 중 바꿀 수 없습니다. 사이트·조건·필드를 바꾸려면 새 SQLite 작업 경로를 지정하세요. 쿠키·키·개인정보를 설정에 넣지 않습니다.

## 수집 → 재개 → 내보내기 → 검증

```bash
.venv/bin/web-data-collector crawl --config my-config.json --job ./jobs/list.sqlite
.venv/bin/web-data-collector resume --job ./jobs/list.sqlite
.venv/bin/web-data-collector export --job ./jobs/list.sqlite --output ./output/list.xlsx
.venv/bin/web-data-collector verify --job ./jobs/list.sqlite --xlsx ./output/list.xlsx
.venv/bin/web-data-collector export --job ./jobs/list.sqlite --output ./output/list.jsonl
.venv/bin/web-data-collector export --job ./jobs/list.sqlite --output ./output/list.csv
```

`crawl`은 새 작업, `resume`은 저장된 설정·남은 항목·다음 페이지를 이어갑니다. 페이지 중간에서 멈춰도 원문 잔여 큐를 DB에 보관합니다. 실행당 한도는 재개마다 다시 적용되며, 기본적으로 소스 전체를 무제한 수집하지 않습니다. 이미 완료한 페이지를 업데이트 목적으로 자동 재수집하지 않습니다. 새 시점 조사는 별도 작업으로 시작하세요.

출력은 JSON입니다. `stored_count`, `read_count`, `duplicate_count`, `missing_key_count`, `pending_items`, `partial`, `reason`을 함께 확인합니다. 사이트 전체 건수를 알 수 없으면 `total_count=null`과 사유를 반환합니다. 고유키 누락은 임의 값으로 채우지 않습니다.

수집의 blocked/failed/stopped와 검증 실패는 종료코드2입니다. 한도에 따른 부분수집은 종료코드0일 수 있으므로 종료코드만으로 전체 완료를 판단하지 마세요. 지정한 export 출력 파일은 갱신되므로 보존할 결과에는 새 이름을 사용합니다.

## Excel·CSV·JSONL 읽기

| 시트·파일 | 용도 |
|---|---|
| Overview | 정규화값·클릭 가능한 URL을 표시하는 보기 |
| Collection | 설정·건수·부분수집 이유·다음 URL·UTC 내보낸 시각 |
| Data / _columns / _overflow | JSON 셀과 경로·장문 조각을 통한 원문 복원 |
| JSONL | 행별 객체 전체를 다른 도구로 전달 |
| CSV + .columns.json | JSON 셀과 열 경로를 함께 보관 |

`verify --xlsx`는 복원한 값과 SQLite 원문 전체를 대조합니다. 보기 시트의 빈칸·축약값은 원문 삭제가 아닙니다. `@sionlab-overflow:` 표식과 보조 시트를 수정·삭제하면 복원할 수 없습니다. 수식 모양 문자열과 큰 숫자도 문자열로 보존합니다.

큰 워크시트를 작성할 때 `--xlsx-mode write-only`를 선택할 수 있지만 현재 export는 DB의 전체 행을 메모리로 읽습니다. 일정 메모리만 사용하는 스트리밍이라고 보장하지 않습니다.

## Python·선택 브라우저

기존 내부 API 경로는 호환을 위해 유지합니다.

```python
from sionlab_web_collector.core import collect
from sionlab_web_collector.exporting import export_job, read_xlsx

# config는 사용자가 작성한 설정 dict
# result = collect("./jobs/list.sqlite", config)
# export_job("./jobs/list.sqlite", "./output/list.xlsx")
```

동적으로 로딩되는 목록은 선택 Playwright 어댑터를 사용할 수 있습니다.

```bash
.venv/bin/python -m pip install -r requirements-browser.lock
.venv/bin/python -m playwright install chromium
.venv/bin/python examples/check_browser.py
```

환경에 pip가 없는 경우 `uv pip install --python .venv/bin/python -r requirements-browser.lock`을 사용할 수 있습니다. 설정을 `adapter: "playwright"`로 지정하면 목록 선택자 등장을 최대30초 기다립니다. 로컬 Chromium 예제는 외부 사이트 검증과 다릅니다. 클릭·스크롤·로그인, POST 기반 페이지, 모든 동적 사이트를 지원하지 않습니다. 자세한 계약은 [docs/contracts.md](docs/contracts.md)에 있습니다.

## 접근 제한과 문제 해결

HTTP 401·403·429, 로그인·CAPTCHA 신호에서 멈춥니다. 자동 재시도·로그인·프록시 전환을 제공하지 않습니다. 소유자 허용 범위와 사이트 이용 조건을 확인하고 수집하세요. 코드 MIT 라이선스는 수집한 콘텐츠의 권리를 부여하지 않습니다.

| 증상 | 확인할 내용 |
|---|---|
| 기존 작업 경로로 crawl 실패 | 같은 작업은 resume, 조건 변경은 새 DB |
| 설정 불일치 | 원래 설정으로 재개하거나 새 작업 시작 |
| 목록 없음·파싱 실패 | 항목/필드 CSS 확인, 오류를 정상0건으로 해석하지 않음 |
| redirect_requires_review | 이동 대상 확인 후 최종 공개 URL로 새 설정 작성 |
| dynamic_items_not_ready | 선택자·로딩 방식·선택 의존성 확인 |
| XLSX 대조 실패 | 같은 시점의 DB·파일인지, 보조 시트를 수정했는지 확인 |
| fcntl 모듈 오류 | 지원 OS 확인, Windows에서는 WSL 사용 |

## 호환·개발·라이선스

0.3.0은 명칭 변경판입니다. 기존 `sionlab-web-collector`와 `python -m sionlab_web_collector`는 같은 처리를 사용합니다. 0.2.0의 작업 DB·원문 복원 형식은 유지합니다. 패키지 파일 충돌을 피하려면 새 가상환경에 설치하고 기존 작업 파일을 지정하세요. [이전 도구와의 차이](docs/migration.md)는 별도로 확인합니다.

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

자동 시험은 외부 웹사이트를 호출하지 않으며 로컬 HTTP·가상 어댑터·임시 DB·Excel을 사용합니다. 현재 공개 버전의 결과는 Actions·릴리스, [과거 검증](docs/verification.md)은 당시 기록입니다.

[CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) · [CHANGELOG.md](CHANGELOG.md). 제보 시 OS·Python·버전·민감정보를 지운 설정·reason·최소 재현 HTML을 [Issues](https://github.com/solid-hwan/web-data-collector/issues)에 남겨 주세요.

[MIT LICENSE](LICENSE) · [외부 의존성 고지](NOTICE.md). 수정·재배포·상업적 활용 시 SIONLAB 저작권·허락 고지와 의존성의 필수 고지를 유지합니다.
