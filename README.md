# 가위바위보 담합 실험

`test.py`는 기존 게임 실행 코드로 유지하고, 통계 실험은 `simulate.py`에서 수행합니다.

```powershell
python simulate.py
```

참가자 수와 실험 조건은 `simulate.py` 상단의 후보 상수를 수정합니다. 후보들의 모든 조합 중 문서의 제약을 만족하는 조건이 자동으로 생성됩니다.

```python
TRIALS = 1_00000
TOTAL_PLAYER_OPTIONS = (4, 6)
COLLUDER_OPTIONS = (2, 3, 4)
TARGET_CATCHER_OPTIONS = (1, 2)
```

- `TOTAL_PLAYER_OPTIONS`: 전체 참가자 후보
- `COLLUDER_OPTIONS`: 담합자 수 후보
- `TARGET_CATCHER_OPTIONS`: 목표 술래 수 후보

실행하면 다음 파일이 생성됩니다.

- `results.json`: 원자료 요약 통계
- `report.html`: 브라우저에서 열어 보는 통계 리포트

각 조건은 실험군과 대조군을 각각 `TRIALS`회 실행합니다. 생성된 `report.html`에서 조건을 선택해 결과를 볼 수 있습니다.
