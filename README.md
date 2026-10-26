# SIONLAB Web Collector 0.2.0

상품 비교 자료나 교육 공지처럼 반복되는 웹 목록을 수집하고, 중단 위치에서 이어서 저장하며 Excel로 내보내는 독립 Python 도구입니다. 고유키 중복을 제거하고 원문·정규화 값·누락 사유를 구분합니다. MIT, Copyright 2026 SIONLAB. [외부 라이브러리 고지](NOTICE.md).

Python 3.10 이상과 Linux/macOS의 파일 잠금(fcntl)이 필요합니다. Windows 직접 실행은 0.2.0 미지원이며 WSL에서 실행할 수 있습니다. 다른 제품이나 기존 MCP 저장소가 필요하지 않습니다.

```bash
python3 setup-lab.py
.venv/bin/sionlab-web-collector --help
.venv/bin/python examples/run_examples.py --output /tmp/sionlab-web-demo
.venv/bin/python -m unittest discover -s tests -v
```

같은 출력 폴더에 예제를 다시 실행하면 기존 작업을 덮어쓰지 않고 거부합니다. 새 출력 폴더를 지정합니다. 일반 설치는 `python -m pip install -r requirements.lock` 후 `python -m pip install --no-deps .`입니다. `setup-lab.py`는 이 제품의 `.venv`만 준비하며 전역 설정을 바꾸지 않습니다.

실제 수집은 [설정 양식](config.template.json)을 대상 웹 페이지에 맞게 작성한 뒤 실행합니다.

```bash
.venv/bin/sionlab-web-collector crawl --config my-config.json --job /tmp/my-job.sqlite
.venv/bin/sionlab-web-collector resume --job /tmp/my-job.sqlite
.venv/bin/sionlab-web-collector export --job /tmp/my-job.sqlite --output /tmp/my-result.xlsx
.venv/bin/sionlab-web-collector export --job /tmp/my-job.sqlite --output /tmp/my-stream.xlsx --xlsx-mode write-only
.venv/bin/sionlab-web-collector verify --job /tmp/my-job.sqlite --xlsx /tmp/my-result.xlsx
```

- `crawl`: 새 SQLite 작업만 시작합니다. 동일 경로가 이미 초기화됐으면 `resume`을 안내합니다.
- `resume`: 저장된 설정과 남은 페이지·항목 큐를 사용합니다. 선택 `--config`가 원 설정과 다르면 거부합니다.
- `export`: `.jsonl`, `.csv`, `.xlsx` 확장자를 지원합니다. 기존 지정 출력 파일은 갱신합니다.
- `verify`: SQLite 무결성·설정 해시·읽은/저장/중복/고유키누락 건수를 대조합니다. `--xlsx`는 복원한 셀과 저장 원문 전체를 대조합니다. 이 결과는 웹 사이트의 전체 데이터 수집 보증이 아닙니다.

기본값은 순차 1개 요청, 초당 최대 1회, **실행당** 최대 2페이지·50읽은항목입니다. `resume` 한 번마다 같은 한도를 새로 적용합니다. `max_items`는 중복과 고유키 누락도 포함한 읽은 항목 수입니다. 페이지 중간에서 한도에 도달하면 남은 원문을 같은 SQLite 트랜잭션에 보관합니다. 설정 변경 없이 다음 실행에서 이어갑니다.

HTTP 401·403·429, CAPTCHA/로그인 화면은 중단합니다. 자동 재시도·우회·로그인·프록시 전환을 하지 않습니다. 기타 HTTP 오류와 목록 선택자 불일치도 실패로 표시하며 정상 0건으로 처리하지 않습니다. 사용자가 원인을 해결한 다음 명시적으로 `resume`할 수 있습니다. 웹 내용 변경으로 이미 완료한 페이지를 자동 재수집하지 않습니다.

[계약과 제한](docs/contracts.md) · [검증](docs/verification.md) · [가상 상품 비교](examples/products/README.md) · [가상 교육 공지](examples/education/README.md) · [Books 수집 연습](examples/books/README.md) · [변경 이력](CHANGELOG.md).

## 읽기 쉬운 Excel과 수집 범위

Excel은 **Overview** 시트로 열립니다. 설정한 필드의 정규화값을 일반 텍스트로 표시하고 URL을 클릭할 수 있습니다. **Collection**에는 설정·저장/중복/누락 건수·부분수집 사유·다음 URL·내보낸 시각이 있습니다. 원문 복원용 **Data / _columns / _overflow**는 유지하며 `verify --xlsx`로 전체 대조합니다. 보기의 빈칸 사유와 긴 값 전체는 원문 시트에서 확인합니다.

## GitHub 설치와 이전 도구

```bash
git clone https://github.com/solid-hwan/sionlab-web-collector.git
cd sionlab-web-collector
python3 setup-lab.py
```

[전환 안내](docs/migration.md)에 기존 web-crawler와의 기능·설정 차이가 있습니다. 기존 사이트 프로필을 자동 변환하지 않으며 클릭·스크롤 자동화와 Windows 직접 실행은 지원하지 않습니다. 저장소와 GitHub 릴리스 ZIP으로 설치하며 PyPI 배포는 포함하지 않습니다.
