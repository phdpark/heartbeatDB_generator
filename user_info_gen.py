import random
import pandas as pd
import numpy as np
import json
from faker import Faker

# 한국어 설정으로 Faker 초기화
fake = Faker('ko_KR')

# 시드 설정으로 재현성 보장
random.seed(42)
np.random.seed(42)

# 데이터 크기 설정
num_records = 1000

# 한국 주요 지역 목록 (인구 100만 이상 지역 포함)
regions = [
    '서울특별시', '부산광역시', '인천광역시', '대구광역시', '대전광역시', 
    '광주광역시', '울산광역시', '세종특별자치시',
    '경기도 수원시', '경기도 고양시', '경기도 용인시', '경기도 성남시', 
    '경기도 부천시', '경기도 안산시', '경기도 화성시', '경기도 남양주시',
    '경기도 안양시', '경기도 평택시', '경기도 시흥시', '경기도 파주시',
    '경기도 김포시', '경기도 의정부시', '경기도 광주시', '경기도 하남시',
    '충청북도 청주시', '충청남도 천안시', '충청남도 아산시',
    '전라북도 전주시', '전라북도, 익산시', '전라남도 여수시', '전라남도 순천시',
    '경상북도 포항시', '경상북도 구미시', '경상북도 경산시',
    '경상남도 창원시', '경상남도 김해시', '경상남도 양산시',
    '강원도 춘천시', '강원도 원주시', '강원도 강릉시',
    '제주특별자치도'
]

# 성씨 목록 (인구 비율에 맞게 가중치 부여)
surnames = [
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', 
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',  
    '홍', '고', '문', '양', '손', '배', '조', '백', '허', '유',
    '남', '심', '노', '정', '하', '곽', '성', '차', '주', '우',
    '구', '신', '임', '전', '민', '유', '류', '손', '백', '허'
]

# 성씨 가중치 (인구 비율 근사값)
surname_weights = [
    0.2156, 0.1468, 0.0973, 0.0462, 0.0438, 0.0260, 0.0246, 0.0185, 0.0184, 0.0179,
    0.0151, 0.0142, 0.0134, 0.0125, 0.0111, 0.0102, 0.0091, 0.0088, 0.0084, 0.0083,
    0.0080, 0.0070, 0.0067, 0.0064, 0.0063, 0.0062, 0.0060, 0.0056, 0.0055, 0.0053,
    0.0051, 0.0049, 0.0048, 0.0047, 0.0046, 0.0045, 0.0044, 0.0043, 0.0042, 0.0041,
    0.0040, 0.0039, 0.0038, 0.0037, 0.0036, 0.0035, 0.0034, 0.0033, 0.0032, 0.0031
]

# 남자 이름에 자주 사용되는 글자들
male_chars = [
    '준', '민', '현', '수', '우', '진', '재', '석', '영', '기',
    '태', '형', '선', '호', '성', '찬', '동', '혁', '훈', '상',
    '원', '철', '정', '인', '환', '용', '한', '규', '연', '중',
    '광', '명', '종', '학', '범', '빈', '석', '근', '상', '균'
]

# 여자 이름에 자주 사용되는 글자들
female_chars = [
    '지', '수', '현', '민', '영', '서', '주', '혜', '은', '유',
    '미', '아', '연', '희', '진', '선', '정', '다', '예', '채',
    '윤', '나', '원', '소', '하', '경', '인', '승', '유', '빈',
    '가', '율', '리', '보', '은', '설', '화', '양', '애', '성'
]

# 데이터 생성 함수
def generate_test_data(n):
    data = []
    
    for i in range(n):
        # user_id 생성 (1억명까지 수용 가능한 9자리 숫자)
        user_id = random.randint(100000000, 999999999)
        
        # 성별 선택
        gender = random.choice(['남', '여'])
        
        # 성씨 선택 (가중치 적용)
        surname = random.choices(surnames, weights=surname_weights, k=1)[0]
        
        # 이름 생성 (1-2글자)
        if gender == '남':
            name_length = random.choice([2])
            given_name = ''.join(random.choices(male_chars, k=name_length))
        else:
            name_length = random.choice([2])
            given_name = ''.join(random.choices(female_chars, k=name_length))
        
        full_name = surname + given_name
        
        # 지역 선택
        region = random.choice(regions)
        
        # 나이 생성 (10-80세)
        age = random.randint(60, 99)
        
        data.append({
            'user_id': user_id,
            'name': full_name,
            'age': age,
            'gender': gender,
            'region': region
        })
    
    return data

# 테스트 데이터 생성
data = generate_test_data(num_records)

# 데이터프레임으로 변환
df = pd.DataFrame(data)

# 결과 확인
print(df.head())
print(f"\n총 레코드 수: {len(df)}")
print(f"성별 분포:\n{df['gender'].value_counts()}")
print(f"지역 상위 10개 분포:\n{df['region'].value_counts().head(10)}")

# CSV 파일로 저장
csv_filename = 'korean_test_data_1000.csv'
df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
print(f"\n데이터가 '{csv_filename}' 파일로 저장되었습니다.")

# JSON 파일로 저장
json_filename = 'korean_test_data_1000.json'

# 1. 기본 JSON 형식으로 저장
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"데이터가 '{json_filename}' 파일로 저장되었습니다.")

# 2. 다른 JSON 구조로 저장 (사용자 ID를 키로 사용)
json_filename_by_id = 'korean_test_data_by_id_1000.json'
data_by_id = {item['user_id']: {k: v for k, v in item.items() if k != 'user_id'} for item in data}
with open(json_filename_by_id, 'w', encoding='utf-8') as f:
    json.dump(data_by_id, f, ensure_ascii=False, indent=2)
print(f"데이터가 '{json_filename_by_id}' 파일로 저장되었습니다.")