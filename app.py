import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

st.set_page_config(page_title="Shilla Financial Dashboard", layout="wide")

# 엑셀 파일 읽기 함수 (좌표 정밀 매핑)
@st.cache_data
def load_excel_data():
    file_path = '경제성 평가.xlsx'
    # 1. Commercial Input 시트에서 엑셀이 계산한 원본 결과값 가져오기
    df_comm = pd.read_excel(file_path, sheet_name='Commercial Input', header=None)
    # 엑셀 시트의 위치에 맞춰 인덱스 조정 (C7=6,2 / F7=6,5 / F8=7,5)
    project_name = df_comm.iloc[6, 2]
    original_npv = df_comm.iloc[6, 5]
    original_irr = df_comm.iloc[7, 5]
    
    # 2. summary 시트에서 연도별 현금흐름 가져오기
    df_sum = pd.read_excel(file_path, sheet_name='summary', header=None)
    years = df_sum.iloc[6, 1:8].values  # 2028-2034
    cash_flow = df_sum.iloc[39, 1:8].values # Net Cash Flow 행 (40행)
    
    # 3. 투자비 가져오기 (초기 투자금)
    df_ass = pd.read_excel(file_path, sheet_name='AP 1. Assumption', header=None)
    investment = df_ass.iloc[13, 2] # 5.9억 원 내외
    
    return project_name, original_npv, original_irr, years, cash_flow, investment

try:
    p_name, o_npv, o_irr, years, cf, inv = load_excel_data()

    st.title(f"📊 {p_name} 경제성 분석 (원본 대조)")
    
    # 원본 수치 출력
    col1, col2 = st.columns(2)
    with col1:
        st.metric("원본 엑셀 IRR", f"{o_irr*100:.2f}%")
    with col2:
        st.metric("원본 엑셀 NPV", f"{o_npv:,.0f} KRW")

    st.divider()
    st.sidebar.header("🕹️ 시뮬레이션 변수")
    price_mod = st.sidebar.slider("판가 변동 (%)", -15, 15, 0)
    
    # 엑셀 로직과 동일하게 시뮬레이션 계산
    # (세후 현금흐름에 판가 변동 반영)
    tax_rate = 0.22
    vol = 800000 # 평균 물량
    base_price = 1200
    rev_change = (price_mod/100) * base_price * vol * (1 - tax_rate)
    
    sim_cf = cf + rev_change
    full_cf = np.insert(sim_cf, 0, -inv) # 0차년도 투자비 삽입
    sim_irr = npf.irr(full_cf)

    st.subheader("💡 변수 적용 시 시뮬레이션 결과")
    st.write(f"판가를 **{price_mod}%** 변경했을 때 예상 IRR: **{sim_irr*100:.2f}%**")

    # 현금흐름 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=sim_cf, mode='lines+markers', name='Simulated CF'))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"데이터 매핑 오류: {e}")
