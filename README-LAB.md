# 독립 검증 실행

이 제품의 설치·명령은 [README.md](README.md)를 따릅니다.

```bash
python3 setup-lab.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python examples/run_examples.py --output /tmp/sionlab-collector-unique-output
```

시험은 로컬 가상 HTTP·가상 브라우저와 SQLite만 사용합니다. 외부 실수집은 자동 시험에 포함하지 않습니다. 두 XLSX 모드의 20,000행 재조회 시험을 포함하므로 공용 환경에서 실행할 때는 `AGENT_SERIAL=1 AGENT_CPU_QUOTA=200% agent-throttle`을 명령 앞에 붙입니다.
