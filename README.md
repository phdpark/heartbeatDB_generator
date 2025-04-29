# heartbeatDB_generator

## user_heartbeat_gen

```
 python3 user_heartbeat_gen.py --input korean_test_data_1000.csv --days 5 --output ~/s3/
```

Help
```
user_heartbeat_gen.py [-h] --input INPUT [--interval INTERVAL] [--days DAYS] [--realtime] [--risk RISK]
                             [--output OUTPUT]
사용자별 심박수 데이터 생성기

options:
  -h, --help           show this help message and exit
  --input INPUT        입력 사용자 데이터 파일 경로 (CSV 또는 JSON)
  --interval INTERVAL  데이터 기록 간격 (초)
  --days DAYS          생성할 과거 데이터 기간 (일)
  --realtime           실시간 데이터 생성 모드
  --risk RISK          위험 상황을 포함할 70세 이상 사용자의 비율 (0-1)
  --output OUTPUT      출력 디렉토리 경로

```

## heartbeat_user_viewr.py

```
 pip install streamlit streamlit_folium folium
```
