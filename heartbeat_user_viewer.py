import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import boto3
from datetime import datetime, timedelta
import json
from decimal import Decimal
import time
from zoneinfo import ZoneInfo

from qa_module import render_qa_section

kst = ZoneInfo("Asia/Seoul")

# 페이지 제목 설정
st.title('고령자 심박수 모니터링 시스템')
st.markdown('고령자 심박 데이터를 불러와 관리합니다.')

# 언어 선택
language = st.sidebar.radio("언어 선택:", ["한국어", "English"])

# 기본 CSV 파일 로드 (korean_test_data_1000.csv)
default_file_path = "korean_test_data_1000.csv"

# 파일 업로드 옵션 (선택적)
#st.sidebar.markdown("### 다른 CSV 파일 업로드 (선택사항)")
#uploaded_file = st.sidebar.file_uploader("다른 CSV 파일 업로드", type="csv")

# 데이터 로드
try:
#    if uploaded_file is not None:
#        # 사용자가 업로드한 파일 사용
#        df = pd.read_csv(uploaded_file)
#        st.success("업로드한 파일이 성공적으로 로드되었습니다!")
#    elif os.path.exists(default_file_path):
    if os.path.exists(default_file_path):
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
    
    # AWS DynamoDB에서 심박수 데이터를 가져오는 함수
    def get_heartbeat_data(user_id, last_timestamp=None):
        try:
            # AWS DynamoDB 연결 설정
            dynamodb = boto3.resource(
                'dynamodb',
                region_name='us-east-1',
                #aws_access_key_id=st.secrets.get("AWS_ACCESS_KEY_ID", "dummy_access_key"),
                #aws_secret_access_key=st.secrets.get("AWS_SECRET_ACCESS_KEY", "dummy_secret_key")
            )
            
            # 테이블 연결
            table = dynamodb.Table('heatbeat-dynamodb-table')
            
            # 쿼리 파라미터 설정
            query_params = {
                'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_id').eq(str(user_id))
            }
            
            # 마지막 타임스탬프 이후의 데이터만 가져오도록 설정
            if last_timestamp:
                query_params['FilterExpression'] = boto3.dynamodb.conditions.Attr('timestamp').gt(last_timestamp)
            
            # 해당 user_id의 데이터 쿼리
            response = table.query(**query_params)
            
            # 결과가 있으면 데이터프레임으로 변환
            if 'Items' in response and response['Items']:
                # DynamoDB에서 Decimal 타입을 float로 변환하는 함수
                def decimal_to_float(obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return obj
                
                # JSON으로 변환 후 다시 파싱하여 Decimal 문제 해결
                items_str = json.dumps(response['Items'], default=decimal_to_float)
                items = json.loads(items_str)
                
                # 데이터프레임으로 변환
                df_heartbeat = pd.DataFrame(items)
                
                # 타임스탬프를 datetime 형식으로 변환
                df_heartbeat['timestamp'] = pd.to_datetime(df_heartbeat['timestamp'])
                
                # 시간순으로 정렬
                df_heartbeat = df_heartbeat.sort_values('timestamp')
                
                return df_heartbeat
            else:
                return None
        except Exception as e:
            st.error(f"심박수 데이터 가져오기 오류: {e}")
            return None
    
    # 세션 상태 초기화
    if 'heartbeat_data' not in st.session_state:
        st.session_state.heartbeat_data = {}
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = {}
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 10  # 기본값 10초
    
    # 실시간 업데이트 설정
    st.sidebar.header("실시간 업데이트 설정")
    st.session_state.auto_refresh = st.sidebar.checkbox("자동 새로고침 사용", st.session_state.auto_refresh)
    
    if st.session_state.auto_refresh:
        st.session_state.refresh_interval = st.sidebar.slider(
            "새로고침 간격 (초)",
            min_value=5,
            max_value=60,
            value=st.session_state.refresh_interval,
            step=5
        )
    
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
                
                # 정확히 하나의 사용자가 선택된 경우 심박수 데이터 표시
                if len(name_filtered_df) == 1:
                    user_id = name_filtered_df['user_id'].iloc[0]
                    user_name = name_filtered_df[name_field].iloc[0]
                    
                    st.subheader(f"{user_name}님의 심박수 데이터")
                    
                    # 실시간 업데이트 컨테이너 생성
                    heartbeat_container = st.container()
                    
                    # 수동 새로고침 버튼
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("데이터 새로고침"):
                            # 캐시된 데이터 초기화
                            if user_id in st.session_state.heartbeat_data:
                                del st.session_state.heartbeat_data[user_id]
                            if user_id in st.session_state.last_update_time:
                                del st.session_state.last_update_time[user_id]
                    
                    with col2:
                        # 자동 새로고침 상태 표시
                        if st.session_state.auto_refresh:
                            st.info(f"자동 새로고침: {st.session_state.refresh_interval}초마다 업데이트")
                        else:
                            st.info("자동 새로고침: 꺼짐 (사이드바에서 활성화 가능)")
                    
                    # 최근 데이터 표시 범위 선택
                    time_range = st.selectbox(
                        "시간 범위:",
                        options=["모든 데이터", "최근 1시간", "최근 1일", "최근 1주일"],
                        index=0
                    )
                    
                    # 시간 범위에 따른 필터링 함수
                    def filter_by_time_range(df, time_range):
                        if df is None or df.empty or time_range == "모든 데이터":
                            return df
                        
                        now = datetime.now(tz=kst)
                        if time_range == "최근 1시간":
                            start_time = now - timedelta(hours=1)
                        elif time_range == "최근 1일":
                            start_time = now - timedelta(days=1)
                        elif time_range == "최근 1주일":
                            start_time = now - timedelta(weeks=1)
                        else:
                            return df
                        
                        return df[df['timestamp'] >= start_time]
                    
                    # 심박수 데이터 업데이트 함수
                    def update_heartbeat_data(user_id):
                        last_timestamp = None
                        if user_id in st.session_state.heartbeat_data and not st.session_state.heartbeat_data[user_id].empty:
                            # 마지막 업데이트 타임스탬프 가져오기
                            last_timestamp = st.session_state.heartbeat_data[user_id]['timestamp'].max().strftime('%Y-%m-%dT%H:%M:%S')
                        
                        # 새 데이터 가져오기
                        new_data = get_heartbeat_data(user_id, last_timestamp)
                        
                        # 기존 데이터와 병합
                        if new_data is not None and not new_data.empty:
                            if user_id in st.session_state.heartbeat_data and not st.session_state.heartbeat_data[user_id].empty:
                                # 새 데이터 추가
                                st.session_state.heartbeat_data[user_id] = pd.concat([
                                    st.session_state.heartbeat_data[user_id],
                                    new_data
                                ]).drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                            else:
                                # 첫 데이터 설정
                                st.session_state.heartbeat_data[user_id] = new_data
                        
                        # 업데이트 시간 기록
                        st.session_state.last_update_time[user_id] = datetime.now(tz=kst)
                        
                        # 선택된 시간 범위로 필터링
                        filtered_data = filter_by_time_range(
                            st.session_state.heartbeat_data.get(user_id, None), 
                            time_range
                        )
                        
                        return filtered_data
                    
                    # 자동 새로고침 설정에 따른 처리
                    if st.session_state.auto_refresh:
                        # 마지막 업데이트 이후 시간 계산
                        last_update = st.session_state.last_update_time.get(user_id, datetime.min)
                        time_since_update = (datetime.now(tz=kst) - last_update).total_seconds()
                        
                        # 설정된 간격보다 오래되었으면 업데이트
                        if time_since_update >= st.session_state.refresh_interval:
                            heartbeat_data = update_heartbeat_data(user_id)
                        else:
                            # 기존 데이터 사용하고 시간 범위 필터링
                            heartbeat_data = filter_by_time_range(
                                st.session_state.heartbeat_data.get(user_id, None), 
                                time_range
                            )
                            
                            # 남은 시간 계산 및 표시
                            remaining_time = st.session_state.refresh_interval - time_since_update
                            st.info(f"다음 자동 업데이트까지 {remaining_time:.1f}초 남았습니다.")
                    else:
                        # 데이터가 없거나 수동 새로고침 버튼을 누른 경우
                        if user_id not in st.session_state.heartbeat_data:
                            heartbeat_data = update_heartbeat_data(user_id)
                        else:
                            # 기존 데이터 사용하고 시간 범위 필터링
                            heartbeat_data = filter_by_time_range(
                                st.session_state.heartbeat_data.get(user_id, None), 
                                time_range
                            )
                    
                    # 마지막 업데이트 시간 표시
                    if user_id in st.session_state.last_update_time:
                        last_update_str = st.session_state.last_update_time[user_id].strftime('%Y-%m-%d %H:%M:%S')
                        st.write(f"마지막 업데이트: {last_update_str}")
                    
                    # 심박수 그래프 표시
                    with heartbeat_container:
                        if heartbeat_data is not None and not heartbeat_data.empty:
                            # 심박수 그래프 그리기
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            
                            # 최대 심박수
                            fig.add_trace(
                                go.Scatter(
                                    x=heartbeat_data['timestamp'],
                                    y=heartbeat_data['heartbeat_max'],
                                    mode='lines',
                                    name='최대 심박수'
                                )
                            )
                            
                            # 평균 심박수
                            fig.add_trace(
                                go.Scatter(
                                    x=heartbeat_data['timestamp'],
                                    y=heartbeat_data['heartbeat_avg'],
                                    mode='lines',
                                    name='평균 심박수'
                                )
                            )
                            
                            # 최소 심박수
                            fig.add_trace(
                                go.Scatter(
                                    x=heartbeat_data['timestamp'],
                                    y=heartbeat_data['heartbeat_min'],
                                    mode='lines',
                                    name='최소 심박수'
                                )
                            )
                            
                            # 위험 상태 강조 표시
                            if 'is_risk' in heartbeat_data.columns:
                                risk_data = heartbeat_data[heartbeat_data['is_risk'] == True]
                                if not risk_data.empty:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=risk_data['timestamp'],
                                            y=risk_data['heartbeat_avg'],
                                            mode='markers',
                                            marker=dict(
                                                size=10,
                                                color='red',
                                                symbol='x'
                                            ),
                                            name='위험 상태'
                                        )
                                    )
                            
                            # 실시간 그래프 표시 (마지막 업데이트 시간 추가)
                            last_update = st.session_state.last_update_time.get(user_id, datetime.now(tz=kst))
                            last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 그래프 레이아웃 설정
                            fig.update_layout(
                                title=f"{user_name}님의 심박수 추이 (마지막 업데이트: {last_update_str})",
                                xaxis_title="시간",
                                yaxis_title="심박수 (BPM)",
                                hovermode="x unified",
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                height=500
                            )
                            
                            # 그래프 표시
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 실시간 알림 컨테이너
                            alert_container = st.container()
                            
                            # 최근 위험 상태 알림
                            if 'is_risk' in heartbeat_data.columns:
                                recent_data = heartbeat_data.sort_values('timestamp', ascending=False).head(3)
                                recent_risks = recent_data[recent_data['is_risk'] == True]
                                
                                if not recent_risks.empty:
                                    with alert_container:
                                        st.error(f"⚠️ 주의: {user_name}님이 최근 위험 심박수 상태를 보이고 있습니다!")
                                        for _, risk in recent_risks.iterrows():
                                            risk_time = risk['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                                            st.warning(f"시간: {risk_time}, 심박수: {risk['heartbeat_avg']} BPM")
                            
                            # 데이터 테이블로도 표시
                            with st.expander("심박수 상세 데이터"):
                                st.dataframe(heartbeat_data.sort_values('timestamp', ascending=False))
                                
                                # 데이터 요약 통계
                                if not heartbeat_data.empty:
                                    st.write("심박수 통계:")
                                    stats = pd.DataFrame({
                                        '통계': ['평균', '최대', '최소', '표준편차', '데이터 포인트 수'],
                                        '평균 심박수': [
                                            f"{heartbeat_data['heartbeat_avg'].mean():.1f}",
                                            f"{heartbeat_data['heartbeat_avg'].max():.1f}",
                                            f"{heartbeat_data['heartbeat_avg'].min():.1f}",
                                            f"{heartbeat_data['heartbeat_avg'].std():.1f}",
                                            f"{len(heartbeat_data)}"
                                        ]
                                    })
                                    st.table(stats)
                                
                        else:
                            st.info(f"{user_name}님의 심박수 데이터가 없습니다.")
                            
                    # 자동 새로고침 설정되어 있으면 다음 업데이트 예약
                    if st.session_state.auto_refresh:
                        # 비동기 실행을 위한 placeholder
                        refresh_placeholder = st.empty()
                        
                        # 자동 업데이트를 위한 타이머 기능 추가 (Streamlit 한계 내에서의 구현)
                        def set_auto_refresh():
                            # 남은 시간 계산
                            last_update = st.session_state.last_update_time.get(user_id, datetime.min)
                            time_since_update = (datetime.now(tz=kst) - last_update).total_seconds()
                            remaining_time = max(0.1, st.session_state.refresh_interval - time_since_update)
                            
                            # 남은 시간이 거의 없으면 페이지 새로고침
                            if remaining_time < 0.5:
                                st.experimental_rerun()
                                
                        # 자동 새로고침 타이머 설정
                        set_auto_refresh()
                
                # 여러 사용자가 검색된 경우 선택 옵션 제공
                elif len(name_filtered_df) > 1:
                    st.info("특정 사용자의 심박수 데이터를 보려면 검색어를 더 구체적으로 입력하세요.")
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
    current_df = general_filtered_df if general_search and 'general_filtered_df' in locals() and len(general_filtered_df) > 0 else (
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
#st.sidebar.markdown("---")
#st.sidebar.markdown("### 사용자 데이터 뷰어")
#st.sidebar.markdown("한국 사용자 정보와 심박수 데이터를 관리하는 도구입니다.")

#render_qa_section()
html_code = """
<iframe src="https://bivxdf3zxd.execute-api.us-east-1.amazonaws.com/prod/"
        width="400"
        height="600"
        style="border: none;">
</iframe>
"""
st.sidebar.markdown(html_code, unsafe_allow_html=True)
