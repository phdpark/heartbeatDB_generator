import pandas as pd
import numpy as np
import json
import time
import datetime
import argparse
import os
import random
import requests
from datetime import datetime, timedelta

API_ENDPOINT = "https://08din32tl2.execute-api.us-east-1.amazonaws.com"

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
            'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),  # ISO 형식으로 수정
            'heartbeat_max': heart_rate_max,
            'heartbeat_min': heart_rate_min,
            'heartbeat_avg': heart_rate,
            'is_risk': is_risk_period  # Boolean으로 변경
        })
    
    return heart_rates

#def send_data_to_api(data):
#    """데이터를 API로 전송합니다."""
#    try:
#        headers = {'Content-Type': 'application/json'}
#        response = requests.post(API_ENDPOINT, json=data, headers=headers)
#        
#        if response.status_code == 200:
#            return True, response.json() if response.text else {"message": "Success"}
#        else:
#            return False, f"API 오류: {response.status_code}, {response.text}"
#    
#    except Exception as e:
#        return False, f"요청 오류: {str(e)}"

import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_data_to_api(data):
    """데이터를 API로 전송합니다."""
    try:
        headers = {'Content-Type': 'application/json', 'x-api-key':'8jFsXcDsgW6XEG13oAUZbaoHsujHjDhL38LmrNJu'}
        logger.debug(f"API 연결 시도: {API_ENDPOINT}")
        response = requests.post(API_ENDPOINT, json=data, headers=headers, timeout=30)
        logger.debug(f"API 응답 상태 코드: {response.status_code}")
        logger.debug(f"API 응답 내용: {response.text}")
        
        if response.status_code == 200:
            return True, response.json() if response.text else {"message": "Success"}
        else:
            return False, f"API 오류: {response.status_code}, {response.text}"
    except requests.exceptions.Timeout:
        logger.error("API 요청 타임아웃")
        return False, "API 요청 타임아웃"
    except requests.exceptions.ConnectionError:
        logger.error("API 연결 오류")
        return False, "API 연결 오류"
    except Exception as e:
        logger.error(f"예외 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return False, f"예외 발생: {str(e)}"

def generate_heart_rate_data(user_data, duration_days=7, interval_seconds=30, output_dir='heart_rate_data',
                            risk_percentage=0.15, output_format=None, send_to_api=False):
    """
    모든 사용자의 심박수 데이터를 생성하고 저장합니다.
    """
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 출력 형식 설정
    if output_format is None:
        output_format = ['csv', 'json']  # 기본값: 모든 형식 저장
    elif isinstance(output_format, str):
        output_format = [output_format.lower()]  # 단일 문자열을 리스트로 변환
    else:
        output_format = [fmt.lower() for fmt in output_format]  # 모든 형식을 소문자로

    # 지원되지 않는 형식 확인
    valid_formats = ['csv', 'json']
    for fmt in output_format:
        if fmt not in valid_formats:
            print(f"경고: '{fmt}'은(는) 지원되지 않는 형식입니다. 유효한 형식은 {valid_formats}입니다.")
            output_format.remove(fmt)

    if not output_format:
        print("오류: 유효한 출력 형식이 지정되지 않았습니다. 기본값(csv, json)을 사용합니다.")
        output_format = ['csv', 'json']

    print(f"선택된 출력 형식: {', '.join(output_format)}")

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

    # 출력 파일 준비
    file_handles = {}

    # CSV 파일 준비
    if 'csv' in output_format:
        all_file_csv = os.path.join(output_dir, 'heart_rate_all_users.csv')
        csv_file = open(all_file_csv, 'w', encoding='utf-8')
        csv_file.write("user_id,timestamp,heartbeat_max,heartbeat_min,heartbeat_avg,is_risk\n")
        file_handles['csv'] = csv_file
        print(f"CSV 파일이 생성되었습니다: {all_file_csv}")

    # JSON 파일 준비
    if 'json' in output_format:
        all_file_json = os.path.join(output_dir, 'heart_rate_all_users.json')
        json_file = open(all_file_json, 'w', encoding='utf-8')
        json_file.write("[\n")  # JSON 배열 시작
        file_handles['json'] = json_file
        print(f"JSON 파일이 생성되었습니다: {all_file_json}")

    # 위험 이벤트 카운터 및 요약 정보
    risk_event_count = 0
    risk_events_summary = []
    first_json_record = True  # 첫 번째 JSON 레코드인지 확인 (쉼표 처리용)
    api_success_count = 0
    api_failure_count = 0

    try:
        # 각 사용자에 대한 심박수 데이터 생성
        for idx, user in user_data.iterrows():
            user_id = user['user_id']
            age = user['age']

            # 위험 상황 포함 여부 결정
            is_high_risk = user_id in risk_users

            print(f"사용자 {user_id} ({idx+1}/{len(user_data)}) - 나이: {age}세 - {'위험 상황 포함' if is_high_risk else '정상'}")

            # 심박수 데이터 생성
            heart_rates = generate_heart_rates(user_id, age, duration_days, interval_seconds, is_high_risk)

            # 생성된 데이터를 바로 파일에 쓰기
            for entry in heart_rates:
                entry['user_id'] = str(user_id)  # user_id를 문자열로 변환

                # CSV에 기록
                if 'csv' in file_handles:
                    file_handles['csv'].write(f"{entry['user_id']},{entry['timestamp']},{entry['heartbeat_max']},{entry['heartbeat_min']},{entry['heartbeat_avg']},{1 if entry['is_risk'] else 0}\n")

                # JSON에 기록
                if 'json' in file_handles:
                    if not first_json_record:
                        file_handles['json'].write(",\n")
                    else:
                        first_json_record = False

                    # is_risk를 1/0에서 boolean으로 변환
                    json_entry = entry.copy()
                    json_line = json.dumps(json_entry, ensure_ascii=False)
                    file_handles['json'].write(json_line)

                # API로 데이터 전송
                if send_to_api:
                    success, response = send_data_to_api(entry)
                    if success:
                        api_success_count += 1
                    else:
                        api_failure_count += 1
                        print(f"API 전송 실패: {response}")

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

    finally:
        # 열린 파일 정리
        for fmt, file_handle in file_handles.items():
            if fmt == 'json':
                file_handle.write("\n]")  # JSON 배열 닫기
            file_handle.close()

    # 위험 이벤트 요약 로그 출력
    if risk_event_count > 0:
        print(f"위험 이벤트 수: {risk_event_count}건 (위험 사용자: {len(risk_users)}명)")
        print("각 위험 이벤트 요약:")
        for event in risk_events_summary:
            print(f"  사용자 {event['user_id']} - {event['timestamp']} - 심박수: {event['heartbeat_avg']} bpm")
        if risk_event_count > 10:
            print(f"  ... 외 {risk_event_count-10}건")
    
    if send_to_api:
        print(f"API 전송 결과: 성공 {api_success_count}건, 실패 {api_failure_count}건")

    print(f"완료! 모든 사용자의 심박수 데이터가 {output_dir} 디렉토리에 저장되었습니다.")

def generate_realtime_data(user_data, interval_seconds=30, output_dir='realtime_heart_data', risk_percentage=0.15, send_to_api=True):
    """
    실시간으로 심박수 데이터를 생성하고 API로 전송합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    
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
    
    # 파일 생성 (날짜를 파일명에 포함)
    today = datetime.now().strftime("%Y%m%d")
    file_csv = os.path.join(output_dir, f'heart_rate_data_{today}.csv')
    file_json = os.path.join(output_dir, f'heart_rate_data_{today}.json')
    
    # 파일이 존재하지 않으면 헤더 작성
    if not os.path.exists(file_csv):
        with open(file_csv, 'w', encoding='utf-8') as f:
            f.write("user_id,timestamp,heartbeat_max,heartbeat_min,heartbeat_avg,is_risk\n")
    
    # JSON 파일에 대한 초기 구조 생성
    if not os.path.exists(file_json):
        with open(file_json, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    try:
        print("실시간 심박수 데이터 생성 및 API 전송을 시작합니다. 중단하려면 Ctrl+C를 누르세요.")
        
        # 각 사용자의 최근 심박수 값을 저장할 사전
        user_heart_rates = {}
        
        # 위험 상황 진행 상태 추적
        risk_progress = {user_id: 0.0 for user_id in risk_users}
        
        # API 전송 통계
        api_success_count = 0
        api_failure_count = 0
        
        while True:
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y-%m-%dT%H:%M:%S')  # ISO 형식으로 수정
            timestamp_log = current_time.strftime("%H-%M-%S")  # hh-mm-ss 형식의 타임스탬프
            
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
                
                # API로 데이터 전송
                if send_to_api:
                    success, response = send_data_to_api(record)
                    if success:
                        api_success_count += 1
                    else:
                        api_failure_count += 1
                        print(f"API 전송 실패: {response}")
            
            # CSV에 데이터 추가 (한 줄씩 추가)
            with open(file_csv, 'a', encoding='utf-8') as f:
                for record in all_records:
                    f.write(f"{record['user_id']},{record['timestamp']},{record['heartbeat_max']},{record['heartbeat_min']},{record['heartbeat_avg']},{1 if record['is_risk'] else 0}\n")
            
            # JSON 파일 업데이트 (기존 데이터 읽어서 추가)
            with open(file_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            json_data.extend(all_records)
            
            with open(file_json, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            # 위험 상황 알림
            if risk_detected:
                current_risks = [r for r in all_records if r['is_risk']]
                for risk in current_risks:
                    user_id = risk['user_id']
                    heart_rate = risk['heartbeat_avg']
                    print(f"⚠️ {timestamp_log} 위험 감지! 사용자 {user_id} - 심박수: {heart_rate} bpm")
            
            print(f"{timestamp_log} - {len(all_records)}명의 사용자 데이터가 기록됨, API 전송: 성공 {api_success_count}건, 실패 {api_failure_count}건")
            
            # 지정된 간격만큼 대기
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n실시간 데이터 생성을 중단합니다.")
        print(f"생성된 데이터는 {file_csv} 및 {file_json} 파일에 있습니다.")
        print(f"API 전송 통계: 성공 {api_success_count}건, 실패 {api_failure_count}건")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='사용자별 심박수 데이터 생성기 및 API 전송')
    parser.add_argument('--input', type=str, required=True, help='입력 사용자 데이터 파일 경로 (CSV 또는 JSON)')
    parser.add_argument('--interval', type=int, default=30, help='데이터 기록 및 전송 간격 (초)')
    parser.add_argument('--days', type=int, default=1, help='생성할 과거 데이터 기간 (일)')
    parser.add_argument('--realtime', action='store_true', help='실시간 데이터 생성 모드')
    parser.add_argument('--risk', type=float, default=0.15, help='위험 상황을 포함할 70세 이상 사용자의 비율 (0-1)')
    parser.add_argument('--output', type=str, default='heart_rate_data', help='출력 디렉토리 경로')
    parser.add_argument('--format', type=str, choices=['csv', 'json', 'both'], default='both',
                        help='출력 파일 형식: csv, json, both (기본값: both)')
    parser.add_argument('--api', action='store_true', help='API로 데이터 전송 활성화')
    parser.add_argument('--no-api', dest='api', action='store_false', help='API로 데이터 전송 비활성화')
    parser.set_defaults(api=True)  # 기본값: API 전송 활성화

    args = parser.parse_args()

    # 사용자 데이터 로드
    print(f"{args.input} 파일을 로드하는 중...")
    user_data = load_user_data(args.input)
    print(f"{len(user_data)}명의 사용자 데이터를 로드했습니다.")

    # 70세 이상 사용자 수 확인
    elderly_count = len(user_data[user_data['age'] >= 70])
    print(f"70세 이상 사용자: {elderly_count}명 (전체의 {elderly_count/len(user_data)*100:.1f}%)")

    # 출력 형식 설정
    if args.format == 'both':
        output_format = ['csv', 'json']
    else:
        output_format = [args.format]

    if args.realtime:
        # 실시간 데이터 생성 (하나의 파일에 지속적으로 기록)
        # 참고: realtime 모드에서는 아직 output_format 옵션이 구현되지 않았습니다.
        generate_realtime_data(user_data, args.interval, args.output, risk_percentage=args.risk)
    else:
        # 과거 데이터 생성
        generate_heart_rate_data(user_data, args.days, args.interval, args.output, risk_percentage=args.risk, output_format=output_format)

# 스크립트 실행 예제:
#
# 1. CSV 파일에서 사용자 데이터를 로드하고 심박수 데이터 생성:
# python heart_rate_generator.py --input korean_test_data_1000.csv
#
# 2. 위험 상황을 30%의 70세 이상 사용자에게 포함:
# python heart_rate_generator.py --input korean_test_data_1000.csv --risk 0.3
#
# 3. CSV 형식으로만 출력:
# python heart_rate_generator.py --input korean_test_data_1000.csv --format csv
#
# 4. JSON 형식으로만 출력:
# python heart_rate_generator.py --input korean_test_data_1000.csv --format json
#
# 5. 실시간 데이터 생성 (10초 간격):
# python heart_rate_generator.py --input korean_test_data_1000.csv --realtime --interval 10 --risk 0.2
#
# 6. 출력 디렉토리 지정:
# python heart_rate_generator.py --input korean_test_data_1000.csv --output custom_output_dir
