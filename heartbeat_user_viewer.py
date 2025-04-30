import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import os

# 페이지 제목 설정
st.title('사용자 데이터 뷰어')
st.markdown('한국 사용자 데이터를 불러와 관리합니다.')

# 언어 선택
language = st.sidebar.radio("언어 선택:", ["한국어", "English"])

# 기본 CSV 파일 로드 (korean_test_data_1000.csv)
default_file_path = "korean_test_data_1000.csv"

# 파일 업로드 옵션 (선택적)
st.sidebar.markdown("### 다른 CSV 파일 업로드 (선택사항)")
uploaded_file = st.sidebar.file_uploader("다른 CSV 파일 업로드", type="csv")

# 데이터 로드
try:
    if uploaded_file is not None:
        # 사용자가 업로드한 파일 사용
        df = pd.read_csv(uploaded_file)
        st.success("업로드한 파일이 성공적으로 로드되었습니다!")
    elif os.path.exists(default_file_path):
        # 기본 파일 사용
        df = pd.read_csv(default_file_path)
        st.info(f"기본 데이터셋 '{default_file_path}'이(가) 로드되었습니다.")
    else:
        # 기본 파일이 없는 경우 예시 데이터 사용
        st.warning(f"'{default_file_path}' 파일을 찾을 수 없습니다. 샘플 데이터를 사용합니다.")
        sample_data = {
            'user_id': [1001, 1002, 1003, 1004, 1005],
            'name_kr': ['홍길동', '김철수', '이영희', '박민수', '정지영'],
            'name_en': ['Hong Gildong', 'Kim Chulsoo', 'Lee Younghee', 'Park Minsoo', 'Jung Jiyoung'],
            'age': [28, 35, 42, 25, 31],
            'gender_kr': ['남성', '남성', '여성', '남성', '여성'],
            'gender_en': ['Male', 'Male', 'Female', 'Male', 'Female'],
            'region_kr': ['서울', '부산', '대구', '인천', '광주'],
            'region_en': ['Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju'],
            'latitude': [37.5665, 35.1796, 35.8714, 37.4563, 35.1595],
            'longitude': [126.9780, 129.0756, 128.6014, 126.7052, 126.8526],
            'phone_number': ['010-1234-5678', '010-2345-6789', '010-3456-7890', 
                            '010-4567-8901', '010-5678-9012']
        }
        df = pd.DataFrame(sample_data)
        
    # 데이터프레임 정보 표시
    st.write(f"총 {len(df)} 개의 사용자 데이터가 로드되었습니다.")
    
    # 사이드바에 필터링 옵션 추가
    st.sidebar.header("필터링 옵션")
    
    # 이름(name_kr) 검색 기능 추가
    name_search = st.sidebar.text_input("이름으로 검색:" if language == "한국어" else "Search by name:")
    
    # 열 선택 (정렬용)
    if 'user_id' in df.columns:
        sort_default = 'user_id'
    else:
        sort_default = df.columns[0]
        
    sort_column = st.sidebar.selectbox(
        "정렬 기준:",
        options=df.columns,
        index=list(df.columns).index(sort_default) if sort_default in df.columns else 0
    )
    
    # 정렬 방향 선택
    sort_order = st.sidebar.radio(
        "정렬 방향:",
        options=["오름차순", "내림차순"]
    )
    
    # 필터링 옵션
    filter_options = st.sidebar.expander("고급 필터링", expanded=False)
    
    # 성별 필터링
    if 'gender_kr' in df.columns and language == "한국어":
        gender_options = ["전체"] + list(df['gender_kr'].unique())
        selected_gender = filter_options.selectbox("성별 필터:", gender_options)
    elif 'gender_en' in df.columns and language == "English":
        gender_options = ["All"] + list(df['gender_en'].unique())
        selected_gender = filter_options.selectbox("Gender filter:", gender_options)
    else:
        selected_gender = "전체" if language == "한국어" else "All"
    
    # 지역 필터링
    if 'region_kr' in df.columns and language == "한국어":
        region_options = ["전체"] + list(df['region_kr'].unique())
        selected_region = filter_options.selectbox("지역 필터:", region_options)
    elif 'region_en' in df.columns and language == "English":
        region_options = ["All"] + list(df['region_en'].unique())
        selected_region = filter_options.selectbox("Region filter:", region_options)
    else:
        selected_region = "전체" if language == "한국어" else "All"
    
    # 나이 범위 필터링
    if 'age' in df.columns:
        min_age = int(df['age'].min())
        max_age = int(df['age'].max())
        age_range = filter_options.slider(
            "나이 범위:" if language == "한국어" else "Age range:",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)
        )
    
    # 일반 검색 기능
    general_search = st.sidebar.text_input("전체 검색:" if language == "한국어" else "General search:")
    
    # 데이터 처리
    # 정렬 적용
    if sort_order == "오름차순":
        df_sorted = df.sort_values(by=sort_column)
    else:
        df_sorted = df.sort_values(by=sort_column, ascending=False)
    
    # 필터 적용
    filtered_df = df_sorted.copy()
    
    # 성별 필터
    if selected_gender != "전체" and selected_gender != "All":
        if language == "한국어" and 'gender_kr' in df.columns:
            filtered_df = filtered_df[filtered_df['gender_kr'] == selected_gender]
        elif language == "English" and 'gender_en' in df.columns:
            filtered_df = filtered_df[filtered_df['gender_en'] == selected_gender]
            
    # 지역 필터
    if selected_region != "전체" and selected_region != "All":
        if language == "한국어" and 'region_kr' in df.columns:
            filtered_df = filtered_df[filtered_df['region_kr'] == selected_region]
        elif language == "English" and 'region_en' in df.columns:
            filtered_df = filtered_df[filtered_df['region_en'] == selected_region]
    
    # 나이 범위 필터
    if 'age' in df.columns:
        filtered_df = filtered_df[(filtered_df['age'] >= age_range[0]) & 
                                  (filtered_df['age'] <= age_range[1])]
    
    # 이름 검색 필터 적용
    name_filtered_df = filtered_df.copy()
    if name_search:
        name_field = 'name_kr' if language == "한국어" else 'name_en'
        if name_field in filtered_df.columns:
            name_filtered_df = filtered_df[filtered_df[name_field].str.contains(name_search, case=False, na=False)]
            
            if len(name_filtered_df) == 0:
                st.warning(f"'{name_search}'을(를) 포함하는 이름이 없습니다.")
            else:
                st.subheader(f"이름 검색 결과: {len(name_filtered_df)}개 항목 발견")
                st.dataframe(name_filtered_df)
        else:
            st.error(f"'{name_field}' 열이 데이터에 존재하지 않습니다.")
    
    # 일반 검색 필터 적용
    if general_search:
        # 모든 열에서 검색어 찾기
        mask = pd.DataFrame(False, index=name_filtered_df.index, columns=[0])
        for col in name_filtered_df.columns:
            mask = mask | name_filtered_df[col].astype(str).str.contains(general_search, case=False, na=False)
        general_filtered_df = name_filtered_df[mask.iloc[:, 0]]
        
        if len(general_filtered_df) == 0:
            st.warning(f"'{general_search}'과(와) 일치하는 결과가 없습니다.")
            # 이름 검색만 적용된 데이터 표시
            if not name_search:
                st.subheader("사용자 데이터")
                st.dataframe(filtered_df)
        else:
            st.subheader(f"검색 결과: {len(general_filtered_df)}개 항목 발견")
            st.dataframe(general_filtered_df)
            
            # 필터링된 전체 데이터도 표시
            if name_search:
                with st.expander("이름 검색 결과 전체 보기"):
                    st.dataframe(name_filtered_df)
            else:
                with st.expander("필터링된 전체 데이터 보기"):
                    st.dataframe(filtered_df)
    else:
        # 일반 검색어 없고 이름 검색도 없을 때 필터링된 데이터 표시
        if not name_search:
            st.subheader("사용자 데이터")
            st.dataframe(filtered_df)
    
    # 현재 표시 중인 데이터 결정
    current_df = general_filtered_df if general_search and len(general_filtered_df) > 0 else (
        name_filtered_df if name_search and len(name_filtered_df) > 0 else filtered_df
    )
    
    # 데이터 시각화 탭
    st.subheader("데이터 시각화")
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["지도 보기", "통계 보기", "차트 보기"])
    
    with viz_tab1:
        # 지도 시각화 (위도/경도 데이터가 있는 경우)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            st.subheader("사용자 위치 지도")
            
            # 유효한 위도/경도 값만 필터링
            map_df = current_df.dropna(subset=['latitude', 'longitude'])
            
            if len(map_df) > 0:
                # 지도 중심 좌표 계산
                center_lat = map_df['latitude'].mean()
                center_lon = map_df['longitude'].mean()
                
                # folium 지도 생성
                m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
                
                # 각 사용자 위치에 마커 추가
                for idx, row in map_df.iterrows():
                    name_field = 'name_kr' if language == "한국어" else 'name_en'
                    region_field = 'region_kr' if language == "한국어" else 'region_en'
                    
                    popup_text = f"""
                    ID: {row['user_id']}<br>
                    이름: {row[name_field]}<br>
                    나이: {row['age']}<br>
                    지역: {row[region_field]}<br>
                    """
                    
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=f"ID: {row['user_id']} - {row[name_field]}"
                    ).add_to(m)
                
                # 지도 표시
                folium_static(m)
            else:
                st.warning("표시할 위치 데이터가 없습니다.")
        else:
            st.info("위도와 경도 정보가 없어 지도를 표시할 수 없습니다.")
    
    with viz_tab2:
        # 데이터 통계 표시
        st.write("데이터 요약 정보:")
        st.write(current_df.describe())
        
        # 성별 분포
        gender_field = 'gender_kr' if language == "한국어" else 'gender_en'
        if gender_field in current_df.columns:
            gender_counts = current_df[gender_field].value_counts()
            st.write("성별 분포:" if language == "한국어" else "Gender Distribution:")
            st.bar_chart(gender_counts)
        
        # 지역별 분포
        region_field = 'region_kr' if language == "한국어" else 'region_en'
        if region_field in current_df.columns:
            region_counts = current_df[region_field].value_counts()
            st.write("지역별 분포:" if language == "한국어" else "Region Distribution:")
            st.bar_chart(region_counts)
    
    with viz_tab3:
        # 추가 차트 및 시각화
        if 'age' in current_df.columns:
            # 연령 분포 히스토그램
            fig = px.histogram(
                current_df, 
                x='age', 
                title="연령 분포" if language == "한국어" else "Age Distribution",
                labels={'age': '나이' if language == "한국어" else 'Age'},
                nbins=20
            )
            st.plotly_chart(fig)
            
            # 지역별 평균 연령 (있는 경우)
            region_field = 'region_kr' if language == "한국어" else 'region_en'
            if region_field in current_df.columns and len(current_df) > 0:
                region_age = current_df.groupby(region_field)['age'].mean().reset_index()
                fig = px.bar(
                    region_age, 
                    x=region_field, 
                    y='age',
                    title="지역별 평균 연령" if language == "한국어" else "Average Age by Region",
                    labels={
                        region_field: '지역' if language == "한국어" else 'Region',
                        'age': '평균 연령' if language == "한국어" else 'Average Age'
                    }
                )
                st.plotly_chart(fig)

except Exception as e:
    st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
    st.info("에러가 발생했습니다. CSV 파일의 형식을 확인해주세요.")

# 푸터 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 사용자 데이터 뷰어")
st.sidebar.markdown("한국 사용자 정보를 관리하는 도구입니다.")

# 앱 실행 방법 안내
st.sidebar.markdown("---")
st.sidebar.markdown("### 앱 실행 방법")
st.sidebar.code("""
# 필요한 라이브러리 설치
pip install streamlit pandas folium streamlit-folium plotly

# 앱 실행
streamlit run app.py
""")

# 데이터 예시 다운로드
if st.sidebar.button("샘플 데이터 다운로드"):
    sample_data = {
        'user_id': [1001, 1002, 1003, 1004, 1005],
        'name_kr': ['홍길동', '김철수', '이영희', '박민수', '정지영'],
        'name_en': ['Hong Gildong', 'Kim Chulsoo', 'Lee Younghee', 'Park Minsoo', 'Jung Jiyoung'],
        'age': [28, 35, 42, 25, 31],
        'gender_kr': ['남성', '남성', '여성', '남성', '여성'],
        'gender_en': ['Male', 'Male', 'Female', 'Male', 'Female'],
        'region_kr': ['서울', '부산', '대구', '인천', '광주'],
        'region_en': ['Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju'],
        'latitude': [37.5665, 35.1796, 35.8714, 37.4563, 35.1595],
        'longitude': [126.9780, 129.0756, 128.6014, 126.7052, 126.8526],
        'phone_number': ['010-1234-5678', '010-2345-6789', '010-3456-7890', 
                        '010-4567-8901', '010-5678-9012']
    }
    sample_df = pd.DataFrame(sample_data)
    
    # CSV 파일로 변환
    csv = sample_df.to_csv(index=False)
    
    st.sidebar.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name="sample_user_data.csv",
        mime="text/csv"
    )
