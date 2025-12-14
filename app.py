import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="천체 관측 데이터 분석",
    page_icon="🔭",
    layout="wide"
)

# ============================================================
# 데이터 로드 및 전처리
# ============================================================
@st.cache_data
def load_and_process_data():
    """데이터 로드 및 전처리"""
    
    # 수정된 데이터 로드
    df = pd.read_csv('messier_fixed.csv', encoding='utf-8-sig')
    
    # 천체 종류 대분류 매핑
    def categorize_object(obj_type):
        if pd.isna(obj_type):
            return '기타', '기타'
        obj_type = str(obj_type).lower()
        
        if 'globular cluster' in obj_type:
            return '성단', '구상성단'
        elif 'open cluster' in obj_type:
            return '성단', '산개성단'
        elif 'barred spiral' in obj_type:
            return '은하', '막대나선은하'
        elif 'spiral galaxy' in obj_type:
            return '은하', '나선은하'
        elif 'elliptical galaxy' in obj_type or 'dwarf elliptical' in obj_type:
            return '은하', '타원은하'
        elif 'lenticular galaxy' in obj_type:
            return '은하', '렌즈형은하'
        elif 'starburst galaxy' in obj_type:
            return '은하', '폭발적항성생성은하'
        elif 'planetary nebula' in obj_type:
            return '성운', '행성상성운'
        elif 'h ii region' in obj_type or 'nebula' in obj_type:
            return '성운', '발광성운'
        elif 'supernova' in obj_type or 'nova' in obj_type:
            return '성운', '초신성잔해'
        elif 'diffuse nebula' in obj_type:
            return '성운', '산광성운'
        elif 'asterism' in obj_type:
            return '기타', '성군'
        elif 'milky way' in obj_type or 'star cloud' in obj_type:
            return '기타', '은하수영역'
        elif 'double' in obj_type:
            return '기타', '이중성'
        else:
            return '기타', '기타'
    
    # 분류 적용
    df[['category', 'sub_category']] = df['object_type'].apply(
        lambda x: pd.Series(categorize_object(x))
    )
    
    # 밝기(등급) 숫자 변환
    df['magnitude_num'] = pd.to_numeric(df['magnitude'], errors='coerce')
    
    # 거리 숫자 변환
    def parse_distance(dist):
        if pd.isna(dist):
            return None
        dist = str(dist).replace(',', '').replace('~', '')
        if '–' in dist or '-' in dist:
            parts = re.split(r'[–-]', dist)
            try:
                nums = [float(re.sub(r'[^\d.]', '', p)) for p in parts if re.sub(r'[^\d.]', '', p)]
                return np.mean(nums) if nums else None
            except:
                return None
        try:
            return float(re.sub(r'[^\d.]', '', dist))
        except:
            return None
    
    df['distance_kly'] = df['distance'].apply(parse_distance)
    
    return df

# 데이터 로드
try:
    df = load_and_process_data()
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# ============================================================
# 사이드바
# ============================================================
st.sidebar.title("🔭 분석 옵션")

# 천체 종류 필터
categories = ['전체'] + list(df['category'].unique())
selected_category = st.sidebar.selectbox("천체 대분류 선택", categories)

if selected_category != '전체':
    filtered_df = df[df['category'] == selected_category]
else:
    filtered_df = df

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 데이터 요약")
st.sidebar.markdown(f"- **전체 천체 수**: {len(df)}개")
st.sidebar.markdown(f"- **선택된 천체 수**: {len(filtered_df)}개")

# ============================================================
# 메인 콘텐츠
# ============================================================

# 타이틀
st.title("🔭 천체의 종류에 따른 관측 데이터 차이 분석")
st.markdown("**연구 목적**: 천체의 물리적 성질 차이가 관측 데이터(밝기, 분포 등)에 어떻게 반영되는지를 비교한다.")

# ============================================================
# 탭 구성
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 데이터 설명", 
    "📊 밝기 분석", 
    "📈 거리 분석", 
    "🗺️ 분포 분석",
    "📉 종합 비교"
])

# ------------------------------------------------------------
# 탭 1: 데이터 설명
# ------------------------------------------------------------
with tab1:
    st.header("📋 데이터에 대한 설명")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("데이터 수집 방법")
        st.markdown("""
        - **수집 방법**: BeautifulSoup을 이용한 웹 스크래핑
        - **데이터 출처**: Wikipedia Messier Objects 목록
        - **수집 데이터**: Messier 천체 카탈로그 (110개 천체)
        """)
        
        st.subheader("수집된 변수")
        st.markdown("""
        | 변수명 | 설명 |
        |--------|------|
        | messier | Messier 번호 (M1~M110) |
        | ngc | NGC 카탈로그 번호 |
        | common_name | 일반적인 명칭 |
        | object_type | 천체 종류 |
        | distance | 지구로부터의 거리 (천 광년) |
        | constellation | 소속 별자리 |
        | magnitude | 겉보기 등급 (밝기) |
        """)
    
    with col2:
        st.subheader("천체 종류별 분류")
        
        # 분류별 개수
        category_counts = df['category'].value_counts()
        fig_pie = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="천체 대분류별 비율",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # 세부 분류
    st.subheader("천체 세부 분류별 개수")
    sub_counts = df.groupby(['category', 'sub_category']).size().reset_index(name='count')
    fig_bar = px.bar(
        sub_counts, 
        x='sub_category', 
        y='count', 
        color='category',
        title="세부 천체 종류별 개수",
        labels={'sub_category': '세부 분류', 'count': '개수', 'category': '대분류'}
    )
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # 데이터 테이블
    st.subheader("📄 원본 데이터")
    st.dataframe(
        filtered_df[['messier', 'common_name', 'object_type', 'category', 'magnitude', 'distance', 'constellation']],
        use_container_width=True,
        height=400
    )

# ------------------------------------------------------------
# 탭 2: 밝기 분석 (RQ1)
# ------------------------------------------------------------
with tab2:
    st.header("📊 천체 종류별 밝기 분석")
    
    st.markdown("""
    > **겉보기 등급(Apparent Magnitude)**: 지구에서 관측했을 때 천체의 밝기를 나타내는 값.
    > 숫자가 **작을수록 더 밝음** (예: 1등급이 5등급보다 밝음)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 히스토그램
        st.subheader("천체 종류별 밝기 분포 (히스토그램)")
        fig_hist = px.histogram(
            df[df['magnitude_num'].notna()],
            x='magnitude_num',
            color='category',
            nbins=15,
            barmode='overlay',
            opacity=0.7,
            title="천체 종류별 겉보기 등급 분포",
            labels={'magnitude_num': '겉보기 등급', 'category': '천체 종류'},
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_hist.update_layout(xaxis_title="겉보기 등급 (작을수록 밝음)")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # 박스플롯
        st.subheader("천체 종류별 밝기 비교 (박스플롯)")
        fig_box = px.box(
            df[df['magnitude_num'].notna()],
            x='category',
            y='magnitude_num',
            color='category',
            title="천체 종류별 겉보기 등급 비교",
            labels={'magnitude_num': '겉보기 등급', 'category': '천체 종류'},
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # 통계 요약
    st.subheader("📈 밝기 통계 요약")
    
    mag_stats = df.groupby('category')['magnitude_num'].agg(['mean', 'median', 'std', 'min', 'max']).round(2)
    mag_stats.columns = ['평균', '중앙값', '표준편차', '최소(가장 밝음)', '최대(가장 어두움)']
    st.dataframe(mag_stats, use_container_width=True)
    
    # 분석 결과
    st.subheader("🔍 분석 결과")
    
    brightest_cat = mag_stats['평균'].idxmin()
    dimmest_cat = mag_stats['평균'].idxmax()
    
    st.success(f"""
    **주요 발견:**
    - **가장 밝은 천체 종류**: {brightest_cat} (평균 등급: {mag_stats.loc[brightest_cat, '평균']})
    - **가장 어두운 천체 종류**: {dimmest_cat} (평균 등급: {mag_stats.loc[dimmest_cat, '평균']})
    - 성단은 상대적으로 밝고, 은하는 멀리 있어 어둡게 관측됨
    """)

# ------------------------------------------------------------
# 탭 3: 거리 분석
# ------------------------------------------------------------
with tab3:
    st.header("📈 천체 종류별 거리 분석")
    
    st.markdown("""
    > **거리**: 지구로부터 천체까지의 거리 (단위: 천 광년, kly)
    """)
    
    # 거리 데이터가 있는 것만 필터
    dist_df = df[df['distance_kly'].notna() & (df['distance_kly'] > 0)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 거리 분포
        st.subheader("천체 종류별 거리 분포")
        fig_dist = px.box(
            dist_df,
            x='category',
            y='distance_kly',
            color='category',
            title="천체 종류별 거리 비교 (로그 스케일)",
            labels={'distance_kly': '거리 (천 광년)', 'category': '천체 종류'},
            log_y=True,
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # 밝기 vs 거리
        st.subheader("밝기와 거리의 관계")
        scatter_df = dist_df[dist_df['magnitude_num'].notna()]
        fig_scatter = px.scatter(
            scatter_df,
            x='distance_kly',
            y='magnitude_num',
            color='category',
            hover_data=['messier', 'common_name'],
            title="거리 vs 겉보기 등급",
            labels={'distance_kly': '거리 (천 광년)', 'magnitude_num': '겉보기 등급', 'category': '천체 종류'},
            log_x=True,
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # 통계 요약
    st.subheader("📈 거리 통계 요약")
    
    dist_stats = dist_df.groupby('category')['distance_kly'].agg(['mean', 'median', 'min', 'max']).round(1)
    dist_stats.columns = ['평균 (kly)', '중앙값 (kly)', '최소 (kly)', '최대 (kly)']
    st.dataframe(dist_stats, use_container_width=True)
    
    st.subheader("🔍 분석 결과")
    st.success("""
    **주요 발견:**
    - **은하**: 평균적으로 가장 멀리 위치 (수만 광년 이상, 외부 은하)
    - **성단**: 상대적으로 가까이 위치 (수천~수만 광년, 우리 은하 내)
    - **성운**: 대부분 우리 은하 내에 위치하여 가장 가까움
    - 거리와 밝기는 양의 상관관계를 보임 (멀수록 어둡게 보임)
    """)

# ------------------------------------------------------------
# 탭 4: 분포 분석 (RQ3)
# ------------------------------------------------------------
with tab4:
    st.header("🗺️ 천체 종류별 하늘 분포 (별자리)") 
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("별자리별 천체 분포")
        const_counts = df['constellation'].value_counts().head(15)
        fig_const = px.bar(
            x=const_counts.index,
            y=const_counts.values,
            title="별자리별 Messier 천체 수 (상위 15개)",
            labels={'x': '별자리', 'y': '천체 수'},
            color=const_counts.values,
            color_continuous_scale='Blues'
        )
        fig_const.update_xaxes(tickangle=45)
        st.plotly_chart(fig_const, use_container_width=True)
    
    with col2:
        st.subheader("별자리별 천체 종류 분포")
        const_category = df.groupby(['constellation', 'category']).size().reset_index(name='count')
        pivot_df = const_category.pivot_table(
            index='constellation', 
            columns='category', 
            values='count', 
            fill_value=0
        )
        # 상위 15개 별자리만
        top_const = df['constellation'].value_counts().head(15).index
        pivot_df = pivot_df.loc[pivot_df.index.isin(top_const)]
        
        fig_heatmap = px.imshow(
            pivot_df.T,
            title="별자리 × 천체 종류 히트맵",
            labels={'x': '별자리', 'y': '천체 종류', 'color': '개수'},
            aspect='auto',
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 천체 종류별 주요 별자리
    st.subheader("📊 천체 종류별 주요 별자리")
    
    col1, col2, col3 = st.columns(3)
    
    for i, cat in enumerate(['성단', '은하', '성운']):
        cat_df = df[df['category'] == cat]
        top_const = cat_df['constellation'].value_counts().head(5)
        
        with [col1, col2, col3][i]:
            st.markdown(f"**{cat}**")
            for c, n in top_const.items():
                st.markdown(f"- {c}: {n}개")
    
    st.subheader("🔍 분석 결과")
    st.success("""
    **주요 발견:**
    - **은하**: 처녀자리(Virgo)와 머리털자리(Coma Berenices)에 집중 → **처녀자리 은하단** 영향
    - **성단**: 궁수자리(Sagittarius)에 집중 → **은하 중심** 방향
    - **성운**: 오리온자리(Orion), 궁수자리 등 **별 탄생 영역**에 분포
    - 특정 천체 종류가 특정 하늘 영역에 집중되는 경향이 명확히 확인됨
    """)

# ------------------------------------------------------------
# 탭 5: 종합 비교
# ------------------------------------------------------------
with tab5:
    st.header("📉 천체 종류별 종합 비교")
    
    # 관측 빈도 (RQ2)
    st.subheader("천체 종류별 관측 빈도")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cat_counts = df['category'].value_counts()
        fig_freq = px.bar(
            x=cat_counts.index,
            y=cat_counts.values,
            color=cat_counts.index,
            title="천체 대분류별 개수",
            labels={'x': '천체 종류', 'y': '개수'},
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_freq, use_container_width=True)
    
    with col2:
        sub_counts = df['sub_category'].value_counts()
        fig_sub = px.bar(
            x=sub_counts.index,
            y=sub_counts.values,
            title="천체 세부분류별 개수",
            labels={'x': '세부 분류', 'y': '개수'},
            color=sub_counts.values,
            color_continuous_scale='Viridis'
        )
        fig_sub.update_xaxes(tickangle=45)
        st.plotly_chart(fig_sub, use_container_width=True)
    
    # 종합 통계
    st.subheader("📊 천체 종류별 종합 통계")
    
    summary = df.groupby('category').agg({
        'messier': 'count',
        'magnitude_num': ['mean', 'std'],
        'distance_kly': 'mean'
    }).round(2)
    summary.columns = ['개수', '평균 등급', '등급 표준편차', '평균 거리(kly)']
    st.dataframe(summary, use_container_width=True)
    
    # 레이더 차트
    st.subheader("천체 종류별 특성 비교 (레이더 차트)")
    
    radar_data = summary.copy()
    radar_data['개수_norm'] = radar_data['개수'] / radar_data['개수'].max()
    radar_data['밝기_norm'] = 1 - (radar_data['평균 등급'] - radar_data['평균 등급'].min()) / (radar_data['평균 등급'].max() - radar_data['평균 등급'].min() + 0.01)
    radar_data['거리_norm'] = radar_data['평균 거리(kly)'].fillna(0) / (radar_data['평균 거리(kly)'].max() + 0.01)
    
    fig_radar = go.Figure()
    
    colors = {'성단': '#1f77b4', '은하': '#ff7f0e', '성운': '#2ca02c', '기타': '#d62728'}
    
    for cat in radar_data.index:
        if cat != '기타':
            fig_radar.add_trace(go.Scatterpolar(
                r=[
                    radar_data.loc[cat, '개수_norm'],
                    radar_data.loc[cat, '밝기_norm'],
                    radar_data.loc[cat, '거리_norm'],
                    radar_data.loc[cat, '개수_norm']  # 닫기
                ],
                theta=['관측 빈도', '밝기', '거리', '관측 빈도'],
                fill='toself',
                name=cat,
                line_color=colors.get(cat, '#333')
            ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="천체 종류별 특성 비교 (정규화)"
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # 최종 결론
    st.subheader("🎯 최종 결론")
    st.info("""
    ### 연구 결과 요약
    
    **RQ1. 천체 종류에 따라 밝기 분포는 다른가?**
    - ✅ **예**: 성단은 평균적으로 가장 밝고(평균 ~6등급), 은하는 가장 어둡게 관측됨(평균 ~9등급)
    
    **RQ2. 천체 종류에 따라 관측 빈도는 다른가?**
    - ✅ **예**: Messier 카탈로그에서 성단(~50%)이 가장 많고, 은하(~36%), 성운(~10%) 순
    
    **RQ3. 천체 종류에 따라 하늘 분포는 다른가?**
    - ✅ **예**: 은하는 처녀자리에, 성단은 궁수자리 방향(은하 중심)에, 성운은 별 탄생 영역에 집중
    
    ---
    
    ### 결론
    천체의 물리적 특성(크기, 거리, 광도)에 따라 관측 데이터에서 **명확한 차이**가 나타남.
    이는 천문학 연구 및 아마추어 관측 계획 수립에 유용한 정보를 제공함.
    """)

# ============================================================
# 푸터
# ============================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    🔭 천체 관측 데이터 분석 프로젝트 | BeautifulSoup 웹 스크래핑 활용<br>
    데이터 출처: Wikipedia Messier Objects
</div>
""", unsafe_allow_html=True)
