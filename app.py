import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

st.set_page_config(page_title="재무 시뮬레이션 대시보드", layout="wide")

st.title("📊 해외 프로젝트 경제성 시뮬레이터")
st.sidebar.header("⚙️ 시나리오 변수 설정")

# 1. 시뮬레이션 변수 (슬라이더)
price_change = st.sidebar.slider("판가 변동률 (%)", -20, 20, 0)
cost_change = st.sidebar.slider("원재료비 변동률 (%)", -20, 20, 0)
vol_change = st.sidebar.slider("판매물량 변동률 (%)", -20, 20, 0)
inv_change = st.sidebar.slider("투자비 변동률 (%)", -20, 20, 0)

# 2. 데이터 로드 (고정 로직)
@st.cache_data
def get_base_data():
    # 질문자님이 주신 엑셀의 핵심 수치들을 기본값으로 설정
    base_investment = 590000000 
    base_years = np.array([2028, 2029, 2030, 2031, 2032, 2033, 2034])
    base_volume = np.array([800000] * 7)
    base_cashflow = np.array([33326857, 198276334, 221412363, 200041262, 191477949, 195703597, 173161394])
    return base_investment, base_volume, base_cashflow, base_years

inv, vol, cf, years = get_base_data()

# 3. 실시간 시뮬레이션 로직
# 판가 및 물량 변동에 따른 현금흐름 재계산 (간이 로직)
sim_inv = inv * (1 + inv_change/100)
sim_vol_factor = (1 + vol_change/100)
sim_price_factor = (1 + price_change/100)
# 세후 이익 변화율 반영 (판가 변동은 이익에 직접적 영향)
sim_cf = cf * sim_vol_factor * sim_price_factor * (1 - cost_change/200) 

# IRR 계산
full_cf = np.insert(sim_cf, 0, -sim_inv)
sim_irr = npf.irr(full_cf)

# 4. 화면 출력
col1, col2 = st.columns(2)
with col1:
    st.metric("예상 IRR", f"{sim_irr*100:.2f}%", delta=f"{(sim_irr-0.3839)*100:.2f}%")
with col2:
    st.metric("총 투자비", f"{sim_inv/1000000:,.0f} 백만원")

# 그래프
fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=sim_cf, mode='lines+markers', name='시뮬레이션 현금흐름'))
fig.update_layout(title="연도별 예상 현금흐름 추이", xaxis_title="연도", yaxis_title="Cash Flow (KRW)")
st.plotly_chart(fig, use_container_width=True)
