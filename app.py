import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

st.set_page_config(page_title="Shilla Financial Dashboard", layout="wide")

# 문자열 데이터를 숫자로 안전하게 변환하는 함수
def safe_float(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, str):
        # 콤마, 공백, %, KRW 등 특수문자 제거
        val = val.replace(',', '').replace('%', '').replace('KRW', '').strip()
    try:
        return float(val)
    except:
        return 0.0

@st.cache_data
def load_excel_data():
    file_path = '경제성 평가.xlsx'
    # Commercial Input 시트
    df_comm = pd.read_excel(file_path, sheet_name='Commercial Input', header=None)
    
    # safe_float 함수를 사용하여 데이터 추출
    project_name = str(df_comm.iloc[6, 2])
    original_npv = safe_float(df_comm.iloc[6, 5])
    original_irr = safe_float(df_comm.iloc[7, 5])
    
    # 엑셀의 IRR이 38.4 등으로 적혀있을 경우 0.384로 변환 (백분율 보정)
    if original_irr > 1:
        original_irr = original_irr / 100
        
    # summary 시트
    df_sum = pd.read_excel(file_path, sheet_name='summary', header=None)
    years = df_sum.iloc[6, 1:8].values
    raw_cf = df_sum.iloc[39, 1:8].values
    cash_flow = np.array([safe_float(v) for v in raw_cf])
    
    # AP 1. Assumption 시트 (투자비)
    df_ass = pd.read_excel(file_path, sheet_name='AP 1. Assumption', header=None)
    investment = safe_float(df_ass.iloc[13, 2])
    
    return project_name, original_npv, original_irr, years, cash_flow, investment

try:
    p_name, o_npv, o_irr, years, cf, inv = load_excel_data()

    st.title(f"📊 {p_name} 경제성 분석 리포트")
    
    # KPI 지표 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric("원본 엑셀 IRR", f"{o_irr*100:.2f}%")
    with col2:
        st.metric("원본 엑셀 NPV", f"{o_npv:,.0f} KRW")

    st.divider()

    # 시뮬레이션 사이드바
    st.sidebar.header("🕹️ 시뮬레이션 변수")
    price_mod = st.sidebar.slider("판가 변동률 (%)", -15, 15, 0)
    
    # 시뮬레이션 계산 (세후 수익 반영)
    tax_rate = 0.22
    vol = 800000 
    base_price = 1200
    rev_change = (price_mod/100) * base_price * vol * (1 - tax_rate)
    
    sim_cf = cf + rev_change
    full_cf = np.insert(sim_cf, 0, -inv) 
    sim_irr = npf.irr(full_cf)

    st.subheader(f"💡 시나리오 결과: 판가 {price_mod}% 변동 시")
    st.write(f"예상 IRR: **{sim_irr*100:.2f}%**")

    # 현금흐름 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=sim_cf, mode='lines+markers', name='시뮬레이션 CF', line=dict(color='royalblue', width=3)))
    fig.update_layout(title="연도별 예상 순현금흐름", xaxis_title="연도", yaxis_title="Cash Flow (KRW)")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 대시보드 로딩 중 오류 발생: {e}")
    st.info("엑셀 파일의 시트 이름이나 데이터 위치가 변경되었는지 확인해 주세요.")
