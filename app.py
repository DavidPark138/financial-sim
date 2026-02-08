import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

st.set_page_config(page_title="Shilla Global Strategy Dashboard", layout="wide")

def safe_float(val):
    if pd.isna(val): return 0.0
    if isinstance(val, str):
        val = val.replace(',', '').replace('%', '').replace('KRW', '').strip()
    try:
        f_val = float(val)
        # 만약 값이 너무 크면(예: 10억 이상) 백만 단위로 조정하는 로직을 넣을 수 있으나 
        # 여기서는 일단 순수 숫자만 반환합니다.
        return f_val
    except: return 0.0

@st.cache_data
def load_excel_data():
    file_path = '경제성 평가.xlsx'
    xl = pd.ExcelFile(file_path)
    
    # 1. Commercial Input
    df_comm = pd.read_excel(xl, 'Commercial Input', header=None)
    p_name = str(df_comm.iloc[6, 2])
    # 원본 IRR이 44.3%라면 0.443으로 읽혀야 함. 
    o_irr = safe_float(df_comm.iloc[7, 5])
    if o_irr > 1: o_irr /= 100 # 44.3으로 읽히면 0.443으로 보정

    # 2. summary 시트 (데이터 위치 정밀 고정)
    df_sum = pd.read_excel(xl, 'summary', header=None)
    years = df_sum.iloc[6, 1:8].values
    # 40행(index 39)이 Net Cash Flow인지 다시 확인
    cash_flow = np.array([safe_float(v) for v in df_sum.iloc[39, 1:8]])
    # 8행(index 7)이 판매량(Sales Volume)
    volumes = np.array([safe_float(v) for v in df_sum.iloc[7, 1:8]])
    
    # 3. 투자비 (AP 1. Assumption 시트 14행)
    df_ass = pd.read_excel(xl, 'AP 1. Assumption', header=None)
    investment = safe_float(df_ass.iloc[13, 2])
    
    # 💡 단위 보정: 투자비가 '원'이고 수익이 '백만'이면 수치가 폭발함
    # 만약 투자비가 1억(100,000,000) 이상인데 현금흐름이 1000 미만이면 단위를 맞춤
    if investment > 1000000 and np.mean(cash_flow) < 1000000:
        investment = investment / 1000000 # 투자비를 백만 단위로 절삭
    
    return p_name, o_irr, years, cash_flow, volumes, investment

try:
    p_name, o_irr, years, cf, vol, inv = load_excel_data()

    st.title(f"🚀 {p_name} 실시간 전략 시뮬레이터")
    
    # 사이드바 변수 (가격, 물량, 원가, 투자비)
    st.sidebar.header("🕹️ 시나리오 변수")
    s_price = st.sidebar.slider("1. 판가 변동 (%)", -20.0, 20.0, 0.0, 0.1)
    s_vol = st.sidebar.slider("2. 물량 변동 (%)", -30.0, 30.0, 0.0, 1.0)
    s_cost = st.sidebar.slider("3. 원가 변동 (%)", -20.0, 20.0, 0.0, 0.1)
    s_inv = st.sidebar.slider("4. 투자비 변동 (%)", -20.0, 20.0, 0.0, 1.0)

    # 시뮬레이션 계산
    tax_rate = 0.22
    # 판가 영향: (변동률 * 기준판가1200 * 물량) * 세후
    price_impact = (s_price/100) * 1200 * vol * (1 - tax_rate)
    # 원가 영향: (변동률 * 예상원가800 * 물량) * 세후 (원가는 마이너스)
    cost_impact = (s_cost/100) * 800 * vol * (1 - tax_rate)
    
    # 시뮬레이션 CF = (기존CF * 물량변동) + 가격영향 - 원가영향
    sim_cf = (cf * (1 + s_vol/100)) + price_impact - cost_impact
    sim_inv = inv * (1 + s_inv/100)
    
    # 최종 IRR 계산
    full_cf = np.insert(sim_cf, 0, -sim_inv)
    sim_irr = npf.irr(full_cf)

    # 메트릭 출력
    c1, c2, c3 = st.columns(3)
    c1.metric("예상 IRR", f"{sim_irr*100:.2f}%", delta=f"{(sim_irr - o_irr)*100:.2f}%")
    c2.metric("기준 IRR", f"{o_irr*100:.2f}%")
    c3.metric("시뮬레이션 투자비", f"{sim_inv:,.0f} (Unit)")

    # 차트
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=sim_cf, mode='lines+markers', name='Simulation'))
    fig.add_trace(go.Scatter(x=years, y=cf, mode='lines', name='Base Case', line=dict(dash='dash')))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"오류 발생: {e}")
