import random
import pandas as pd
import numpy as np
import json
from faker import Faker

# Initialize Faker with Korean settings
fake = Faker('ko_KR')

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

# Set data size
num_records = 1000

# Dictionary of major Korean regions with their English names and coordinates
regions_data = {
    '서울특별시': {'english': 'Seoul', 'lat': 37.5665, 'lng': 126.9780},
    '부산광역시': {'english': 'Busan', 'lat': 35.1796, 'lng': 129.0756},
    '인천광역시': {'english': 'Incheon', 'lat': 37.4563, 'lng': 126.7052},
    '대구광역시': {'english': 'Daegu', 'lat': 35.8714, 'lng': 128.6014},
    '대전광역시': {'english': 'Daejeon', 'lat': 36.3504, 'lng': 127.3845},
    '광주광역시': {'english': 'Gwangju', 'lat': 35.1595, 'lng': 126.8526},
    '울산광역시': {'english': 'Ulsan', 'lat': 35.5384, 'lng': 129.3114},
    '세종특별자치시': {'english': 'Sejong', 'lat': 36.4800, 'lng': 127.2890},
    '경기도 수원시': {'english': 'Suwon, Gyeonggi-do', 'lat': 37.2636, 'lng': 127.0286},
    '경기도 고양시': {'english': 'Goyang, Gyeonggi-do', 'lat': 37.6559, 'lng': 126.8350},
    '경기도 용인시': {'english': 'Yongin, Gyeonggi-do', 'lat': 37.2410, 'lng': 127.1775},
    '경기도 성남시': {'english': 'Seongnam, Gyeonggi-do', 'lat': 37.4449, 'lng': 127.1389},
    '경기도 부천시': {'english': 'Bucheon, Gyeonggi-do', 'lat': 37.5035, 'lng': 126.7882},
    '경기도 안산시': {'english': 'Ansan, Gyeonggi-do', 'lat': 37.3217, 'lng': 126.8309},
    '경기도 화성시': {'english': 'Hwaseong, Gyeonggi-do', 'lat': 37.1995, 'lng': 127.0969},
    '경기도 남양주시': {'english': 'Namyangju, Gyeonggi-do', 'lat': 37.6363, 'lng': 127.2165},
    '경기도 안양시': {'english': 'Anyang, Gyeonggi-do', 'lat': 37.3943, 'lng': 126.9568},
    '경기도 평택시': {'english': 'Pyeongtaek, Gyeonggi-do', 'lat': 36.9921, 'lng': 127.1129},
    '경기도 시흥시': {'english': 'Siheung, Gyeonggi-do', 'lat': 37.3799, 'lng': 126.8032},
    '경기도 파주시': {'english': 'Paju, Gyeonggi-do', 'lat': 37.7599, 'lng': 126.7730},
    '경기도 김포시': {'english': 'Gimpo, Gyeonggi-do', 'lat': 37.6155, 'lng': 126.7156},
    '경기도 의정부시': {'english': 'Uijeongbu, Gyeonggi-do', 'lat': 37.7380, 'lng': 127.0437},
    '경기도 광주시': {'english': 'Gwangju, Gyeonggi-do', 'lat': 37.4292, 'lng': 127.2550},
    '경기도 하남시': {'english': 'Hanam, Gyeonggi-do', 'lat': 37.5395, 'lng': 127.2149},
    '충청북도 청주시': {'english': 'Cheongju, Chungcheongbuk-do', 'lat': 36.6424, 'lng': 127.4890},
    '충청남도 천안시': {'english': 'Cheonan, Chungcheongnam-do', 'lat': 36.8151, 'lng': 127.1135},
    '충청남도 아산시': {'english': 'Asan, Chungcheongnam-do', 'lat': 36.7798, 'lng': 127.0046},
    '전라북도 전주시': {'english': 'Jeonju, Jeollabuk-do', 'lat': 35.8242, 'lng': 127.1480},
    '전라북도, 익산시': {'english': 'Iksan, Jeollabuk-do', 'lat': 35.9483, 'lng': 126.9576},
    '전라남도 여수시': {'english': 'Yeosu, Jeollanam-do', 'lat': 34.7604, 'lng': 127.6622},
    '전라남도 순천시': {'english': 'Suncheon, Jeollanam-do', 'lat': 34.9506, 'lng': 127.4872},
    '경상북도 포항시': {'english': 'Pohang, Gyeongsangbuk-do', 'lat': 36.0199, 'lng': 129.3436},
    '경상북도 구미시': {'english': 'Gumi, Gyeongsangbuk-do', 'lat': 36.1194, 'lng': 128.3445},
    '경상북도 경산시': {'english': 'Gyeongsan, Gyeongsangbuk-do', 'lat': 35.8250, 'lng': 128.7414},
    '경상남도 창원시': {'english': 'Changwon, Gyeongsangnam-do', 'lat': 35.2540, 'lng': 128.6420},
    '경상남도 김해시': {'english': 'Gimhae, Gyeongsangnam-do', 'lat': 35.2281, 'lng': 128.8892},
    '경상남도 양산시': {'english': 'Yangsan, Gyeongsangnam-do', 'lat': 35.3350, 'lng': 129.0386},
    '강원도 춘천시': {'english': 'Chuncheon, Gangwon-do', 'lat': 37.8747, 'lng': 127.7342},
    '강원도 원주시': {'english': 'Wonju, Gangwon-do', 'lat': 37.3447, 'lng': 127.9209},
    '강원도 강릉시': {'english': 'Gangneung, Gangwon-do', 'lat': 37.7519, 'lng': 128.8760},
    '제주특별자치도': {'english': 'Jeju Special Self-Governing Province', 'lat': 33.4996, 'lng': 126.5312}
}

# List of Korean regions for selection
regions = list(regions_data.keys())

# Dictionary for Korean to English surname mapping
surname_mapping = {
    '김': 'Kim', '이': 'Lee', '박': 'Park', '최': 'Choi', '정': 'Jung', 
    '강': 'Kang', '조': 'Jo', '윤': 'Yoon', '장': 'Jang', '임': 'Lim',
    '한': 'Han', '오': 'Oh', '서': 'Seo', '신': 'Shin', '권': 'Kwon', 
    '황': 'Hwang', '안': 'Ahn', '송': 'Song', '류': 'Ryu', '전': 'Jeon',
    '홍': 'Hong', '고': 'Ko', '문': 'Moon', '양': 'Yang', '손': 'Son', 
    '배': 'Bae', '백': 'Baek', '허': 'Heo', '유': 'Yoo', '남': 'Nam',
    '심': 'Shim', '노': 'Noh', '하': 'Ha', '곽': 'Kwak', '성': 'Sung', 
    '차': 'Cha', '주': 'Joo', '우': 'Woo', '구': 'Koo', '민': 'Min'
}

# Korean surnames with population weights
surnames = [
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', 
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',  
    '홍', '고', '문', '양', '손', '배', '조', '백', '허', '유',
    '남', '심', '노', '정', '하', '곽', '성', '차', '주', '우',
    '구', '신', '임', '전', '민', '유', '류', '손', '백', '허'
]

# Surname weights (approximate population ratio)
surname_weights = [
    0.2156, 0.1468, 0.0973, 0.0462, 0.0438, 0.0260, 0.0246, 0.0185, 0.0184, 0.0179,
    0.0151, 0.0142, 0.0134, 0.0125, 0.0111, 0.0102, 0.0091, 0.0088, 0.0084, 0.0083,
    0.0080, 0.0070, 0.0067, 0.0064, 0.0063, 0.0062, 0.0060, 0.0056, 0.0055, 0.0053,
    0.0051, 0.0049, 0.0048, 0.0047, 0.0046, 0.0045, 0.0044, 0.0043, 0.0042, 0.0041,
    0.0040, 0.0039, 0.0038, 0.0037, 0.0036, 0.0035, 0.0034, 0.0033, 0.0032, 0.0031
]

# Characters frequently used in male names
male_chars = [
    '준', '민', '현', '수', '우', '진', '재', '석', '영', '기',
    '태', '형', '선', '호', '성', '찬', '동', '혁', '훈', '상',
    '원', '철', '정', '인', '환', '용', '한', '규', '연', '중',
    '광', '명', '종', '학', '범', '빈', '석', '근', '상', '균'
]

# English equivalents for male name characters (approximate romanization)
male_chars_eng = [
    'Jun', 'Min', 'Hyun', 'Su', 'Woo', 'Jin', 'Jae', 'Seok', 'Young', 'Ki',
    'Tae', 'Hyung', 'Sun', 'Ho', 'Sung', 'Chan', 'Dong', 'Hyuk', 'Hoon', 'Sang',
    'Won', 'Chul', 'Jung', 'In', 'Hwan', 'Yong', 'Han', 'Kyu', 'Yeon', 'Jung',
    'Kwang', 'Myung', 'Jong', 'Hak', 'Beom', 'Bin', 'Seok', 'Keun', 'Sang', 'Kyun'
]

# Characters frequently used in female names
female_chars = [
    '지', '수', '현', '민', '영', '서', '주', '혜', '은', '유',
    '미', '아', '연', '희', '진', '선', '정', '다', '예', '채',
    '윤', '나', '원', '소', '하', '경', '인', '승', '유', '빈',
    '가', '율', '리', '보', '은', '설', '화', '양', '애', '성'
]

# English equivalents for female name characters (approximate romanization)
female_chars_eng = [
    'Ji', 'Su', 'Hyun', 'Min', 'Young', 'Seo', 'Ju', 'Hye', 'Eun', 'Yu',
    'Mi', 'A', 'Yeon', 'Hee', 'Jin', 'Sun', 'Jung', 'Da', 'Ye', 'Chae',
    'Yoon', 'Na', 'Won', 'So', 'Ha', 'Kyung', 'In', 'Seung', 'Yu', 'Bin',
    'Ga', 'Yul', 'Ri', 'Bo', 'Eun', 'Seol', 'Hwa', 'Yang', 'Ae', 'Sung'
]

# Create mapping dictionaries for name translation
male_char_map = dict(zip(male_chars, male_chars_eng))
female_char_map = dict(zip(female_chars, female_chars_eng))

# Generate phone number function
def generate_phone_number():
    # Create 11-digit Korean mobile number starting with 010
    middle = random.randint(1000, 9999)
    last = random.randint(1000, 9999)
    return f"010{middle}{last}"

# Data generation function
def generate_test_data(n):
    data = []
    
    for i in range(n):
        # Generate user_id (9-digit number to accommodate up to 100 million users)
        user_id = random.randint(100000000, 999999999)
        
        # Select gender
        gender_kr = random.choice(['남', '여'])
        gender_en = 'Male' if gender_kr == '남' else 'Female'
        
        # Select surname (with weights applied)
        surname_kr = random.choices(surnames, weights=surname_weights, k=1)[0]
        surname_en = surname_mapping.get(surname_kr, surname_kr)  # Get English equivalent
        
        # Generate given name (2 characters)
        if gender_kr == '남':
            name_length = 2
            given_name_kr_chars = random.choices(male_chars, k=name_length)
            given_name_en_parts = [male_char_map.get(char, char) for char in given_name_kr_chars]
        else:
            name_length = 2
            given_name_kr_chars = random.choices(female_chars, k=name_length)
            given_name_en_parts = [female_char_map.get(char, char) for char in given_name_kr_chars]
        
        given_name_kr = ''.join(given_name_kr_chars)
        given_name_en = ''.join(given_name_en_parts)
        
        full_name_kr = surname_kr + given_name_kr
        full_name_en = surname_en + ' ' + given_name_en
        
        # Select region
        region_kr = random.choice(regions)
        region_data = regions_data[region_kr]
        region_en = region_data['english']
        latitude = region_data['lat']
        longitude = region_data['lng']
        
        # Generate age (60-99)
        age = random.randint(60, 99)
        
        # Generate phone number
        phone_number = generate_phone_number()
        
        data.append({
            'user_id': user_id,
            'name_kr': full_name_kr,
            'name_en': full_name_en,
            'age': age,
            'gender_kr': gender_kr,
            'gender_en': gender_en,
            'region_kr': region_kr,
            'region_en': region_en,
            'latitude': latitude,
            'longitude': longitude,
            'phone_number': phone_number
        })
    
    return data

# Generate test data
data = generate_test_data(num_records)

# Convert to DataFrame
df = pd.DataFrame(data)

# Check results
print(df.head())
print(f"\nTotal records: {len(df)}")
print(f"Gender distribution:\n{df['gender_en'].value_counts()}")
print(f"Top 10 regions distribution:\n{df['region_en'].value_counts().head(10)}")

# Save to CSV file
csv_filename = 'korean_test_data_1000.csv'
df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
print(f"\nData saved to '{csv_filename}'")

# Save to JSON file
json_filename = 'korean_test_data_1000.json'

# 1. Save in basic JSON format
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Data saved to '{json_filename}'")

# 2. Save in different JSON structure (with user_id as key)
json_filename_by_id = 'korean_test_data_by_id_1000.json'
data_by_id = {item['user_id']: {k: v for k, v in item.items() if k != 'user_id'} for item in data}
with open(json_filename_by_id, 'w', encoding='utf-8') as f:
    json.dump(data_by_id, f, ensure_ascii=False, indent=2)
print(f"Data saved to '{json_filename_by_id}'")