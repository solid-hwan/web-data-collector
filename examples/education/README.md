# 가상 교육 공지 정리

가상 입력은 [page1.html](page1.html)과 [page2.html](page2.html), 설정은 [config.json](config.json), 예상 집계는 [expected.json](expected.json)입니다. 고객자료·실제 판매가격·실제 교육 일정이 아닙니다.

제품 루트에서 실행합니다.

```bash
.venv/bin/python examples/run_examples.py --output /tmp/sionlab-example-new
```

로컬 서버를 임의 빈 포트로 띄우고 두 예제를 수집합니다. 결과는 지정 폴더의 `education/sample.jsonl`, `sample.csv`, `sample.xlsx`입니다. 서버는 종료되며 외부 사이트를 호출하지 않습니다. 첨부 [sample.xlsx](sample.xlsx)는 같은 가상 입력에서 생성한 3행 샘플입니다. 원문/정규화/누락사유 셀은 JSON 인코딩이며 금액은 정밀한 문자열로 유지합니다.

예상 결과는 3개 고유 항목, 2개 완료 페이지입니다. 상품 예제는 중복1개·누락가격1개, 교육 예제는 누락정원1개를 포함합니다. 누락값은 0으로 추정하지 않습니다. 가상 선택자 시험만 확인하며 실제 쇼핑몰·교육기관의 동적 구조나 접근권한은 검증하지 않습니다.
