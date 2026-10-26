# 기존 수집 도구에서 전환

## 0.3.0 명칭 변경과 호환

공개 제품명은 **웹 데이터 수집기 — 웹 목록 수집과 Excel 저장**, 저장소·패키지·명령은 `web-data-collector`, 모듈 실행은 `python -m web_data_collector`입니다. 기존 `sionlab-web-collector` 명령과 `python -m sionlab_web_collector`는 같은 처리를 사용합니다.

0.2.0에서 생성한 SQLite 작업과 Excel Data/_columns/_overflow 형식, `@sionlab-overflow:` 원문 복원 표식을 유지합니다. 새 명령의 resume/export/verify에 기존 작업 경로를 지정하면 됩니다. 기존 Python 내부 모듈 경로도 유지합니다. 패키지 배포명 변경으로 파일이 겹칠 수 있으므로 새 가상환경에 설치하고 기존 작업 파일을 지정하세요.

이 패키지는 독립 구현입니다. 기존 byungjunjang/web-crawler의 포크나 모든 기능의 호환 대체판으로 표시하지 않습니다. 해당 저장소·프로필·진행 기록은 자동 변경하지 않습니다.

| 기존 사용 흐름 | 새 제품의 대응 | 차이 |
|---|---|---|
| 사이트 프로필·에이전트가 수집 코드 작성 | JSON CSS 선택자 설정 | 프로필 자동 이식 없음; 알려진 반복 목록에 적합 |
| export_to_excel(data, path) | export_rows(records, output) 또는 CLI export | 입력 구조가 다름. raw/normalized/missing_reason을 유지 |
| ProgressTracker 진행 파일 | SQLite 작업 + CLI resume | 기존 progress.json을 직접 읽지 않음 |
| 원문 JSONL 별도 보존 | 원문 DB + Data/_columns/_overflow | Excel 재읽기로 전체 객체 대조 가능 |
| 브라우저 상호작용·클릭·스크롤 | 선택 Playwright 목록 로딩 | 클릭·스크롤·로그인 자동화 없음 |
| 기존 실행 환경 | Linux/macOS 파일잠금, Windows는 WSL | Windows 네이티브 미지원 |

새 작업은 다른 SQLite 경로로 시작합니다. 기존 설정·결과를 삭제하지 말고, `examples/books/config.json`처럼 필드·고유키·다음페이지 선택자를 지정하세요. max_pages는 실행당 한도이므로 1페이지로 지정하면 crawl 이후 resume이 다음 페이지부터 같은 한도로 이어집니다. 설정은 작업 생성 후 불변이며 변경하려면 새 작업을 시작합니다.

```bash
.venv/bin/web-data-collector crawl --config my-config.json --job /tmp/new-job.sqlite
.venv/bin/web-data-collector resume --job /tmp/new-job.sqlite
.venv/bin/web-data-collector export --job /tmp/new-job.sqlite --output /tmp/new-result.xlsx
.venv/bin/web-data-collector verify --job /tmp/new-job.sqlite --xlsx /tmp/new-result.xlsx
```

0.1.0에서 만든 SQLite 및 Excel 복원 형식은 유지합니다. 0.2.0 Excel에는 Overview·Collection이 추가됩니다. `read_xlsx()`는 _columns의 헤더와 맞는 데이터 시트를 찾아, 이전 파일의 데이터 시트 이름이 Overview여도 복원합니다. 보조 시트를 삭제하면 복원할 수 없습니다.

대량 export는 현재 DB 전체 레코드를 메모리에 읽습니다. write-only는 워크시트 작성 모드이며 모든 메모리 사용이 일정하다는 뜻은 아닙니다. 대용량 데이터·임의 사이트 전체 호환은 별도 검증 대상입니다.
