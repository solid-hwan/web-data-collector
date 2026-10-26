# 웹 데이터 수집기 — 에이전트 작업 안내

Codex·Claude Code 등 AI 코딩 도구와 사람이 같은 계약을 따르기 위한 지침이다. [CONTRIBUTING.md](CONTRIBUTING.md), [docs/contracts.md](docs/contracts.md), [docs/migration.md](docs/migration.md)를 함께 읽는다.

## 작업 전 확인

1. [README.md](README.md)에서 설치·지원 환경·제품 범위를 읽는다.
2. 현재 요청이 조사·설명인지 파일 수정인지 구분하고, 수정 전 `git status --short`와 관련 diff를 확인한다. 다른 사람의 변경·작업 DB·인증·실행 중 프로세스를 보존한다.
3. 관련 소스·호출부·시험과 입출력 계약을 필요한 범위만 읽는다. 변경 목적·영향·검증 방법을 정한다.
4. 실제 키·개인정보·고객 자료를 코드·시험·문서·로그에 넣지 않는다. 가상 HTML/JSON과 `.invalid` 도메인 등 분명한 예제를 사용한다.

이 문서는 공개 저장소의 작업 기준이다. 특정 편집기·AI 서비스·운영 MCP·개인 경로·전용 기록 도구가 필요하지 않다. 설치된 도구와 사용자의 명시 범위를 우선하며 새 전역 설정·자동화·외부 게시를 임의로 추가하지 않는다.

## 개발 환경과 시험

```bash
python3 setup-lab.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

설치는 프로젝트 `.venv`에 한정한다. 코드 변경 후 설치된 패키지로 시험하려면 `setup-lab.py`를 다시 실행하거나 다음과 같이 로컬 소스를 재설치한다. 전역 패키지는 변경하지 않는다.

```bash
.venv/bin/python -m pip install --no-build-isolation --no-deps .
```

pip가 없는 uv 환경은 `uv pip install --python .venv/bin/python --no-build-isolation --no-deps .`을 사용한다. `.venv`에 이전 복사본이 설치된 채 소스만 수정하면 옛 코드를 시험할 수 있으므로 import 경로·버전을 확인한다. 리소스가 제한된 환경에서는 시험을 직렬로 실행하고 불필요하게 중복 실행하지 않는다.

자동 시험은 외부 실서비스를 호출하지 않는다. 실조회가 요청되었을 때만 대상·입력·최대 호출수·저장 위치를 명확히 한 뒤 수행한다. 인증·차단·할당량 문제를 우회하거나 0건으로 숨기지 않는다.

## 공통 변경 원칙

- 변경한 동작을 재현하는 회귀시험을 먼저 좁혀 실행하고 관련 전체 시험을 마친다. 문구 수정은 내용·링크·명령을 검증한다.
- 수집 결과와 상태가 다르면 원문·카운터·checkpoint의 관계부터 확인한다. 없는 값은 null과 사유로 표시하고 추정값으로 메우지 않는다.
- 저장 형식·공개 호출·종료코드 변경은 호환 영향·전환 경로·회귀시험을 함께 설계한다. 오래된 태그·검증 기록을 새 결과처럼 고치지 않는다.
- 실패 응답은 통제된 reason으로 반환한다. 요청 URL·헤더·키·쿠키가 예외·로그·stdout에 노출되지 않게 한다.
- 불필요한 의존성·코드 재정렬·광범위한 리팩터링을 섞지 않는다. 의존성을 바꿀 경우 pyproject와 lock 및 NOTICE의 실제 일치를 확인한다.
- 사용자 요청 없이 커밋·push·릴리스·업로드·운영 데이터 변경을 하지 않는다. 승인된 범위는 중복 확인 없이 수행한다.

## 완료 보고와 공개 점검

구체적인 변경·수행한 명령과 결과·미실행 범위를 간결하게 보고한다. 설치 성공, 로컬 회귀 통과, 외부 서비스 동작을 구분한다. 새 환경에서 소스 설치·CLI 도움말·가상 예제를 검증하며 라이선스·필수 고지를 포함한다. `.env`·작업 DB·실제 수집 원문·가상환경·개인 설정을 릴리스에 넣지 않는다. 공개 작업이 요청되면 태그·원격 커밋·CI·첨부 파일을 재조회한다.

## 코드 지도

| 경로 | 역할·변경 시 함께 볼 부분 |
|---|---|
| src/web_data_collector/ | 새 모듈 실행 진입점 |
| src/sionlab_web_collector/core.py | 설정·HTTP/Playwright·선택자·정규화·잠금·SQLite·재개 |
| src/sionlab_web_collector/exporting.py | JSONL/CSV/XLSX·열 경로·장문 조각·원문 재읽기 |
| src/sionlab_web_collector/cli.py | crawl/resume/export/verify·JSON 출력·종료코드 |
| config.template.json | 공개 설정 양식 |
| tests/test_collector.py | 로컬 HTTP·중단복구·차단·정규화·대량 내보내기 |
| tests/test_release.py / test_naming.py | 보기·기존 Excel·신구 명령·저장 큐 재개 |
| examples/products/ / education/ | 가상 HTML·설정·기대값·샘플 |
| examples/check_browser.py | 선택 브라우저의 로컬 동적 목록 확인 |

## 반드시 유지할 계약

- 공개명은 웹 데이터 수집기, 명령은 `web-data-collector`, 모듈은 `web_data_collector`다. 제작자·저작권 SIONLAB과 기존 내부 모듈·`sionlab-web-collector` 명령을 유지한다.
- 기본 순차1개·초당 최대1회·실행당2페이지/50읽은항목 한도를 유지한다. `max_items`는 중복·고유키 누락을 포함한다.
- 설정 전체 해시를 고정하고 기존 DB의 설정 변경을 거부한다. 새 작업은 crawl, 기존 작업은 resume이다. 명시적인 새 시점 조사 없이 완료 페이지를 재수집하지 않는다.
- 원문 잔여 큐·레코드·카운터·다음 URL을 같은 트랜잭션으로 저장한다. 저장 전후 강제 종료·재개 시험을 유지한다.
- 고유키 누락을 임의 ID로 채우거나 오류를 정상0건으로 표시하지 않는다. 사이트 전체수는 검증된 계약이 없으면 null과 사유다.
- HTTP 401/403/429, CAPTCHA·로그인 신호, 검토가 필요한 redirect를 자동 재시도·우회하지 않는다. 프록시·쿠키·은폐·인증 자동화를 추가하지 않는다.
- Playwright는 선택 의존성이다. 기본 설치·시험에 브라우저 다운로드를 요구하지 않는다. 선택자 대기와 모든 비동기 처리 완료를 혼동하지 않는다.
- Data/_columns/_overflow 및 `@sionlab-overflow:` 원문 표식은 저장 호환 계약이다. 숫자·장문·중첩값·제어문자·수식 모양 문자열을 손실 없이 복원한다.
- normal/write-only는 Excel 작성 모드다. 전체 DB를 메모리로 읽는 현재 구현을 무제한 스트리밍이라고 설명하지 않는다.
- Linux/macOS fcntl 의존을 명시한다. Windows 직접 실행 지원은 실제 구현·시험 없이 주장하지 않는다.

## 자주 하는 수정의 검증 범위

| 수정 | 필요한 검증 |
|---|---|
| 명령·모듈 이름 | test_naming.py의 신구 도움말·재개·export·verify |
| CSS·정규화 | 가상 HTML의 정상·누락·중복·금액·URL 회귀 |
| 수집·SQLite | 페이지/항목 한도·잔여 큐·설정 해시·중단 전후 재개 |
| HTTP·브라우저 | 로컬 차단·redirect·반복목록·동적 선택자·속도 제한 |
| Excel | 원문 재읽기·장문·수식·보조 시트·두 모드·기존 형식 |
| 안내·설정 | JSON 파싱·상대 링크·새 환경 설치·가상 예제 |

새 사이트 예제는 공개 가능한 가상 HTML과 기대 결과를 사용한다. 외부 사이트 성공 사례로 쓰려면 별도 승인된 실제 조회의 시각·범위·한계를 기록한다.
