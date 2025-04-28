import pandas as pd
import numpy as np
import json
import time
import datetime
import argparse
import os
import random
import boto3
from datetime import datetime, timedelta
import logging
import traceback

# 로깅 설정
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# DynamoDB 클라이언트 설정
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'heatbeat-record-table' # 사용할 DynamoDB 테이블 이름
table = dynamodb.Table(table_name)

def load_user_data(file_path):
    """사용자 데이터 파일(CSV 또는 JSON)을 로드합니다."""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):  # ID를 키로 사용하는 JSON 형식인 경우
                records = []
                for user_id, user_info in data.items():
                    user_info['user_id'] = int(user_id)
                    records.append(user_info)
                return pd.DataFrame(records)
            else:  # 배열 형식인 경우
                return pd.DataFrame(data)
    else:
        raise ValueError("지원되지 않는 파일 형식입니다. CSV 또는 JSON 파일을 제공해주세요.")

def generate_heart_rates(user_id, age, duration_days=7, interval_seconds=30, is_high_risk=False):
    """
    사용자의 나이에 기반하여 심박수 데이터를 생성합니다.
    - 정상 심박수 범위: 성인 60-100bpm, 운동 중 최대 220-나이
    - 야간에는 심박수가 낮아짐 (50-70bpm)
    - 활동에 따른 변동 추가
    - is_high_risk가 True인 경우, 위험 이벤트 발생 가능 (70세 이상)
    """
    # 현재 시간에서 주일 전으로 시작 시간 설정
    end_time = datetime.now()
    start_time = end_time - timedelta(days=duration_days)
    
    # 기간 동안의 모든 타임스탬프 생성 (30초 간격)
    timestamps = []
    current_time = start_time
    while current_time < end_time:
        timestamps.append(current_time)
        current_time += timedelta(seconds=interval_seconds)
    
    # 사용자 연령대에 따른 기본 심박수 범위 설정
    if age < 18:
        base_rate = 80
        variance = 20
        min_rate = 60
        max_exercise_rate = 200 - age
    elif age < 35:
        base_rate = 75
        variance = 15
        min_rate = 55
        max_exercise_rate = 190 - age
    elif age < 50:
        base_rate = 70
        variance = 15
        min_rate = 50
        max_exercise_rate = 180 - age
    else:
        base_rate = 65
        variance = 10
        min_rate = 45
        max_exercise_rate = 170 - age
    
    heart_rates = []
    
    # 위험 이벤트 설정 (70세 이상의 고위험군인 경우)
    risk_event = None
    if is_high_risk and age >= 70:
        # 1주일 중 랜덤 시점에 위험 이벤트 발생
        risk_day = random.randint(0, duration_days - 1)
        risk_hour = random.randint(0, 23)
        risk_minute = random.randint(0, 59)
        risk_time = start_time + timedelta(days=risk_day, hours=risk_hour, minutes=risk_minute)
        
        # 위험 지속 시간 (2-15분)
        risk_duration = random.randint(2, 15)
        risk_end_time = risk_time + timedelta(minutes=risk_duration)
        
        print(f"위험 감지: 사용자 {user_id} (나이: {age}세) - {risk_time.strftime('%Y-%m-%d %H:%M:%S')}부터 {risk_duration}분간 심박수 이상 발생")
        risk_event = (risk_time, risk_end_time)
    
    for timestamp in timestamps:
        hour = timestamp.hour
        minute = timestamp.minute
        day_of_week = timestamp.weekday()  # 0=월요일, 6=일요일
        
        # 위험 이벤트 체크
        is_risk_period = False
        if risk_event and risk_event[0] <= timestamp <= risk_event[1]:
            is_risk_period = True
        
        if is_risk_period:
            # 위험 상황: 심박수 급격히 감소 (0-10 bpm)
            # 점진적으로 감소하는 패턴 생성
            progress = (timestamp - risk_event[0]).total_seconds() / (risk_event[1] - risk_event[0]).total_seconds()
            
            if progress < 0.2:  # 초기 20%는 급격한 감소
                heart_rate = max(base_rate - int(base_rate * progress * 4), 25)
            elif progress < 0.7:  # 중간 50%는 매우 낮은 심박수
                heart_rate = random.randint(5, 10)
            else:  # 나머지 30%는 점진적 회복 시도 (실패 케이스)
                heart_rate = random.randint(5, 15)
            
            heart_rate_min = max(heart_rate - 2, 0)
            heart_rate_max = heart_rate + 2
            
        else:
            # 정상 상황
            # 시간대에 따른 기본 변동
            if 22 <= hour or hour < 6:  # 야간
                time_factor = 0.8  # 기본 심박수보다 낮음
            elif 6 <= hour < 9:  # 아침 활동
                time_factor = 1.1
            elif 17 <= hour < 19:  # 저녁 활동
                time_factor = 1.15
            else:  # 일반 활동 시간
                time_factor = 1.0
            
            # 요일에 따른 변동 (주말에는 활동량 감소)
            if day_of_week >= 5:  # 주말
                day_factor = 0.95
            else:  # 평일
                day_factor = 1.0
            
            # 무작위 활동 시간 생성 (평균 심박수 상승)
            # 아침 운동: 6-8시, 저녁 운동: 18-20시
            is_exercise = False
            if (6 <= hour < 8 or 18 <= hour < 20) and np.random.random() < 0.3:
                is_exercise = True
                exercise_intensity = np.random.uniform(0.6, 0.9)  # 운동 강도
                adjusted_rate = base_rate * time_factor * day_factor
                exercise_rate = adjusted_rate + (max_exercise_rate - adjusted_rate) * exercise_intensity
                heart_rate = int(np.clip(exercise_rate + np.random.normal(0, 5), min_rate, max_exercise_rate))
            else:
                adjusted_rate = base_rate * time_factor * day_factor
                random_factor = np.random.normal(0, variance / 3)
                heart_rate = int(np.clip(adjusted_rate + random_factor, min_rate, base_rate + variance))
            
            # 5분마다 작은 활동 변화 (상승 또는 하락)
            if minute % 5 == 0 and not is_exercise:
                heart_rate += int(np.random.normal(0, 5))
            
            # 최소/최대 심박수 계산
            heart_rate_min = max(heart_rate - int(np.random.uniform(1, 5)), min_rate)
            heart_rate_max = min(heart_rate + int(np.random.uniform(1, 5)), max_exercise_rate)
        
        # 결과 저장
        heart_rates.append({
            'user_id': str(user_id),
            'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),  # ISO 형식으로 수정
            'heartbeat_max': heart_rate_max,
            'heartbeat_min': heart_rate_min,
            'heartbeat_avg': heart_rate,
            'is_risk': is_risk_period  # Boolean으로 변경
        })
    
    return heart_rates

def save_to_dynamodb(item):
    """DynamoDB에 데이터를 저장합니다."""
    try:
        # DynamoDB용 항목 형식 변환
        # 기본키는 user_id와 timestamp를 조합해 사용
        dynamodb_item = {
            'user_id': item['user_id'],
            'timestamp': item['timestamp'],
            'heartbeat_max': item['heartbeat_max'],
            'heartbeat_min': item['heartbeat_min'],
            'heartbeat_avg': item['heartbeat_avg'],
            'is_risk': item['is_risk']
        }
        
        response = table.put_item(Item=dynamodb_item)
        logger.debug(f"DynamoDB 저장 성공: {item['user_id']}, {item['timestamp']}")
        return True, response
    
    except Exception as e:
        logger.error(f"DynamoDB 저장 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def generate_heart_rate_data(user_data, duration_days=7, interval_seconds=30, 
                            risk_percentage=0.15):
    """모든 사용자의 심박수 데이터를 생성하고 DynamoDB에 저장합니다."""
    # 위험 사용자 목록 생성
    risk_users = []

    # 70세 이상 사용자 목록
    elderly_users = user_data[user_data['age'] >= 70]

    # 위험 상황이 발생할 노인 사용자 선택
    if len(elderly_users) > 0:
        risk_count = max(1, int(len(elderly_users) * risk_percentage))
        risk_indices = np.random.choice(elderly_users.index, size=risk_count, replace=False)
        risk_users = elderly_users.loc[risk_indices, 'user_id'].tolist()
        print(f"선택된 위험 사용자: {len(risk_users)}명 (70세 이상 사용자 중)")

    # 위험 이벤트 카운터 및 요약 정보
    risk_event_count = 0
    risk_events_summary = []
    db_success_count = 0
    db_failure_count = 0

    # 각 사용자에 대한 심박수 데이터 생성
    for idx, user in user_data.iterrows():
        user_id = user['user_id']
        age = user['age']

        # 위험 상황 포함 여부 결정
        is_high_risk = user_id in risk_users

        print(f"사용자 {user_id} ({idx+1}/{len(user_data)}) - 나이: {age}세 - {'위험 상황 포함' if is_high_risk else '정상'}")

        # 심박수 데이터 생성
        heart_rates = generate_heart_rates(user_id, age, duration_days, interval_seconds, is_high_risk)

        # 생성된 데이터를 DynamoDB에 저장
        for entry in heart_rates:
            # DynamoDB에 저장
            success, _ = save_to_dynamodb(entry)
            if success:
                db_success_count += 1
            else:
                db_failure_count += 1

            # 위험 이벤트 요약 정보 수집
            if entry['is_risk']:
                risk_event_count += 1
                # 최대 10개까지만 요약 정보 저장
                if len(risk_events_summary) < 10:
                    risk_events_summary.append({
                        'user_id': entry['user_id'],
                        'timestamp': entry['timestamp'],
                        'heartbeat_avg': entry['heartbeat_avg']
                    })

    # 위험 이벤트 요약 로그 출력
    if risk_event_count > 0:
        print(f"위험 이벤트 수: {risk_event_count}건 (위험 사용자: {len(risk_users)}명)")
        print("각 위험 이벤트 요약:")
        for event in risk_events_summary:
            print(f"  사용자 {event['user_id']} - {event['timestamp']} - 심박수: {event['heartbeat_avg']} bpm")
        if risk_event_count > 10:
            print(f"  ... 외 {risk_event_count-10}건")
    
    print(f"DynamoDB 저장 결과: 성공 {db_success_count}건, 실패 {db_failure_count}건")

def generate_realtime_data(user_data, interval_seconds=30, risk_percentage=0.15):
    """실시간으로 심박수 데이터를 생성하고 DynamoDB에 저장합니다."""
    # 70세 이상 사용자 목록
    elderly_users = user_data[user_data['age'] >= 70]
    
    # 위험 상황이 발생할 노인 사용자 선택
    risk_users = []
    if len(elderly_users) > 0:
        risk_count = max(1, int(len(elderly_users) * risk_percentage))
        risk_indices = np.random.choice(elderly_users.index, size=risk_count, replace=False)
        risk_users = elderly_users.loc[risk_indices, 'user_id'].tolist()
        print(f"선택된 위험 사용자: {len(risk_users)}명 (70세 이상 사용자 중)")
    
    # 각 위험 사용자에 대한 위험 발생 시간 설정 (현재부터 5-30분 사이)
    risk_times = {}
    for user_id in risk_users:
        # 5-30분 후에 위험 상황 발생
        minutes_from_now = random.randint(5, 30)
        risk_start = datetime.now() + timedelta(minutes=minutes_from_now)
        # 위험 지속 시간 2-10분
        risk_duration = random.randint(2, 10)
        risk_end = risk_start + timedelta(minutes=risk_duration)
        risk_times[user_id] = (risk_start, risk_end)
        
        print(f"위험 예정: 사용자 {user_id} - {minutes_from_now}분 후 시작, {risk_duration}분간 지속")
    
    try:
        print("실시간 심박수 데이터 생성 및 DynamoDB 저장을 시작합니다. 중단하려면 Ctrl+C를 누르세요.")
        
        # 각 사용자의 최근 심박수 값을 저장할 사전
        user_heart_rates = {}
        
        # 위험 상황 진행 상태 추적
        risk_progress = {user_id: 0.0 for user_id in risk_users}
        
        # DynamoDB 저장 통계
        db_success_count = 0
        db_failure_count = 0
        
        while True:
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y-%m-%dT%H:%M:%S')  # ISO 형식으로 수정
            timestamp_log = current_time.strftime("%H:%M:%S")  # hh:mm:ss 형식의 타임스탬프
            
            all_records = []
            risk_detected = False
            
            for idx, user in user_data.iterrows():
                user_id = str(user['user_id'])  # user_id를 문자열로 변환
                age = user['age']
                
                # 위험 상황 체크
                is_risk_period = False
                risk_progress_value = 0.0
                
                if int(user_id) in risk_times:
                    risk_start, risk_end = risk_times[int(user_id)]
                    if risk_start <= current_time <= risk_end:
                        is_risk_period = True
                        # 위험 진행 정도 계산 (0.0-1.0)
                        total_seconds = (risk_end - risk_start).total_seconds()
                        elapsed_seconds = (current_time - risk_start).total_seconds()
                        risk_progress_value = min(1.0, elapsed_seconds / total_seconds)
                        risk_progress[int(user_id)] = risk_progress_value
                        risk_detected = True
                
                # 심박수 계산
                if is_risk_period:
                    # 위험 상황: 심박수 급격히 감소 (0-10 bpm)
                    if risk_progress_value < 0.2:  # 초기 20%는 급격한 감소
                        base_heart_rate = 70 if age >= 70 else 80
                        heart_rate = max(base_heart_rate - int(base_heart_rate * risk_progress_value * 4), 25)
                    elif risk_progress_value < 0.7:  # 중간 50%는 매우 낮은 심박수
                        heart_rate = random.randint(5, 10)
                    else:  # 나머지 30%는 점진적 회복 시도 (실패 케이스)
                        heart_rate = random.randint(5, 15)
                    
                    heart_rate_min = max(heart_rate - 2, 0)
                    heart_rate_max = heart_rate + 2
                    
                else:
                    # 정상 상태
                    # 이전 심박수가 있으면 그 근처에서 변동, 없으면 새로 생성
                    if user_id in user_heart_rates:
                        prev_rate = user_heart_rates[user_id]
                        # 약간의 변동 추가
                        variation = np.random.normal(0, 2)
                        base_rate = prev_rate + variation
                    else:
                        # 나이에 기반한 초기 심박수 설정
                        if age < 18:
                            base_rate = np.random.uniform(70, 90)
                        elif age < 35:
                            base_rate = np.random.uniform(65, 85)
                        elif age < 50:
                            base_rate = np.random.uniform(60, 80)
                        else:
                            base_rate = np.random.uniform(55, 75)
                    
                    # 시간대에 따른 조정
                    hour = current_time.hour
                    if 22 <= hour or hour < 6:  # 야간
                        base_rate *= 0.85
                    elif 6 <= hour < 9 or 17 <= hour < 19:  # 활동 시간
                        base_rate *= 1.1
                    
                    # 최종 심박수 계산
                    heart_rate = int(base_rate)
                    heart_rate_min = max(heart_rate - int(np.random.uniform(1, 4)), 40)
                    heart_rate_max = min(heart_rate + int(np.random.uniform(1, 4)), 220 - age)
                
                # 값 저장
                user_heart_rates[user_id] = heart_rate
                
                # 레코드 생성
                record = {
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'heartbeat_max': heart_rate_max,
                    'heartbeat_min': heart_rate_min,
                    'heartbeat_avg': heart_rate,
                    'is_risk': is_risk_period  # Boolean으로 저장
                }
                
                all_records.append(record)
                
                # DynamoDB에 데이터 저장
                success, _ = save_to_dynamodb(record)
                if success:
                    db_success_count += 1
                else:
                    db_failure_count += 1
            
            # 위험 상황 알림
            if risk_detected:
                current_risks = [r for r in all_records if r['is_risk']]
                for risk in current_risks:
                    user_id = risk['user_id']
                    heart_rate = risk['heartbeat_avg']
                    print(f"⚠️ {timestamp_log} 위험 감지! 사용자 {user_id} - 심박수: {heart_rate} bpm")
            
            print(f"{timestamp_log} - {len(all_records)}명의 사용자 데이터가 기록됨, DynamoDB 저장: 성공 {db_success_count}건, 실패 {db_failure_count}건")
            
            # 지정된 간격만큼 대기
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n실시간 데이터 생성을 중단합니다.")
        print(f"DynamoDB 저장 통계: 성공 {db_success_count}건, 실패 {db_failure_count}건")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='사용자별 심박수 데이터 생성기 및 DynamoDB 저장')
    parser.add_argument('--input', type=str, required=True, help='입력 사용자 데이터 파일 경로 (CSV 또는 JSON)')
    parser.add_argument('--interval', type=int, default=30, help='데이터 기록 및 전송 간격 (초)')
    parser.add_argument('--days', type=int, default=1, help='생성할 과거 데이터 기간 (일)')
    parser.add_argument('--realtime', action='store_true', help='실시간 데이터 생성 모드')
    parser.add_argument('--risk', type=float, default=0.15, help='위험 상황을 포함할 70세 이상 사용자의 비율 (0-1)')
    parser.add_argument('--table', type=str, default='heatbeat-record-table', help='DynamoDB 테이블 이름')

    args = parser.parse_args()

    # DynamoDB 테이블 이름 업데이트
    table_name = args.table
    table = dynamodb.Table(table_name)

    # 사용자 데이터 로드
    print(f"{args.input} 파일을 로드하는 중...")
    user_data = load_user_data(args.input)
    print(f"{len(user_data)}명의 사용자 데이터를 로드했습니다.")

    # 70세 이상 사용자 수 확인
    elderly_count = len(user_data[user_data['age'] >= 70])
    print(f"70세 이상 사용자: {elderly_count}명 (전체의 {elderly_count/len(user_data)*100:.1f}%)")

    if args.realtime:
        # 실시간 데이터 생성 및 DynamoDB 저장
        generate_realtime_data(user_data, args.interval, risk_percentage=args.risk)
    else:
        # 과거 데이터 생성 및 DynamoDB 저장
        generate_heart_rate_data(user_data, args.days, args.interval, risk_percentage=args.risk)

# 스크립트 실행 예제:
#
# 1. CSV 파일에서 사용자 데이터를 로드하고 심박수 데이터 생성 후 DynamoDB에 저장:
# python heart_rate_generator.py --input korean_test_data_1000.csv
#
# 2. 위험 상황을 30%의 70세 이상 사용자에게 포함:
# python heart_rate_generator.py --input korean_test_data_1000.csv --risk 0.3
#
# 3. 실시간 데이터 생성 (10초 간격):
# python heart_rate_generator.py --input korean_test_data_1000.csv --realtime --interval 10 --risk 0.2
#
# 4. 특정 DynamoDB 테이블에 저장:
# python heart_rate_generator.py --input korean_test_data_1000.csv --table CustomHeartRateTable
