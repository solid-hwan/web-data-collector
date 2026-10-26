# 웹 데이터 수집기 — 개발자용 상세 흐름

[처음 사용하는 분을 위한 안내](../README.md#한눈에-보는-사용-흐름)에서는 네 단계로 사용 방법을 설명합니다. 아래 도표는 코드를 연결하거나 수정할 때 참고하는 처리 순서입니다.

## 한눈에 보는 사용 흐름

상품·교육 공지·문서 목록에 맞게 CSS 설정을 작성하면 수집·재개·Excel 검증을 같은 명령으로 처리합니다. AI 서비스나 브라우저 자동화는 기본 실행에 필요하지 않습니다.

```mermaid
flowchart TD
    A["상품 비교 · 교육 공지 · 공개 문서 목록"] --> B["JSON 설정: 목록 CSS · 필드 · 고유키 · 다음 링크"]
    B --> C["crawl: 새 작업 시작"]
    C --> D["공개 페이지를 순차 수집"]
    D --> E["SQLite: 원문 · 정규화값 · 남은 항목 저장"]
    E --> F["resume: 같은 설정으로 이어가기"]
    F --> E
    E --> G["export: 저장 결과 내보내기"]
    G --> H["Excel: 목록 검토 · 원문 링크"]
    G --> I["CSV / JSONL: 집계 · 다른 도구 연결"]
    H --> J["verify: Excel 복원값과 DB 원문 대조"]
    E --> J
```

### 수집·중단·재개·원문 확인 순서

```mermaid
sequenceDiagram
    autonumber
    actor U as 사용자 / 실행 스크립트
    participant T as 웹 데이터 수집기
    participant W as 공개 웹 페이지
    participant D as SQLite 작업 DB
    participant X as Excel 파일
    U->>T: crawl(config, 새 작업 경로)
    T->>D: 설정 해시 · 새 작업 초기화
    T->>W: HTTP GET 또는 선택 Playwright 목록 읽기
    W-->>T: HTML 또는 접근 제한 응답
    alt 차단 · 로그인 · CAPTCHA 신호
        T->>D: 중단 상태 · 사유 저장
        T-->>U: blocked 또는 failed · 자동 우회 없음
    else 읽을 수 있는 목록
        T->>T: CSS 필드 추출 · 정규화 · 고유키 확인
        T->>D: 원문 · 카운터 · 다음 URL · 잔여 큐 함께 저장
        T-->>U: 저장 건수 · partial · 다음 위치
    end
    opt 사용자가 재개 요청
        U->>T: resume(같은 작업 경로)
        T->>D: 저장된 설정 · 잔여 큐 · 다음 URL 읽기
        Note over T,D: 저장한 잔여 항목부터 처리 · 실행당 한도 다시 적용
        opt 다음 페이지가 필요한 경우
            T->>W: 다음 페이지를 순차 요청
            W-->>T: HTML 또는 오류
        end
        T->>D: 이어 처리한 결과와 체크포인트 저장
    end
    U->>T: export --output 결과.xlsx
    T->>D: 저장 원문 · 수집 상태 읽기
    T->>X: Overview · Collection · 원문 복원 시트 생성
    U->>T: verify --xlsx 결과.xlsx
    T->>X: 장문 조각을 결합해 원문 복원
    T->>D: 저장 원문과 전체 대조
    T-->>U: valid · xlsx_matches
```

저장된 잔여 항목만 처리하면 재개 중 새 웹 요청은 필요하지 않습니다. `verify`는 저장·내보내기의 일치를 확인하며 사이트 전체 수집을 보증하지 않습니다. 새 시점 조사는 새 작업 DB로 시작합니다. [시나리오별 활용](recipes.md)에서 설정과 실행 예를 확인하세요.

