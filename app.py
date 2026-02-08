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
    try: return float(val)
    except: return 0.0

@st.cache_data
def load_excel_data():
    file_path = '경제성 평가.xlsx'
    xl = pd.ExcelFile(file_path)
    
    # 1. Commercial Input에서 기본 지표 찾기
    df_comm = pd.read_excel(xl, 'Commercial Input', header=None)
    # 엑셀 구조상 B7~C8 근처에 이름과 고객사가 있음
    p_name = str(df_comm.iloc[6, 2]) if not pd.isna(df_comm.iloc[6, 2]) else "프로젝트"
    o_irr = safe_float(df_comm.iloc[7, 5])
    if o_irr > 1: o_irr /= 100

    # 2. summary 시트에서 현금흐름 '행' 자동 탐색
    df_sum = pd.read_excel(xl, 'summary', header=None)
    
    # 키워드로 행 찾기 (정확도 향상)
    cf_row_idx = 39 # 기본값
    vol_row_idx = 7 # 기본값
    for i, row in df_sum.iterrows():
        row_str = str(row[0])
        if 'Net cash flow' in row_str or '순현금흐름' in row_str: cf_row_idx = i
        if 'Sales' in row_str or '판매량' in row_str: vol_row_idx = i

    years = df_sum.iloc[6, 1:8].values
    cash_flow = np.array([safe_float(v) for v in df_sum.iloc[cf_row_idx, 1:8]])
    volumes = np.array([safe_float(v) for v in df_sum.iloc[vol_row_idx, 1:8]])
    
    # 3. 투자비 가져오기
    df_ass = pd.read_excel(xl, 'AP 1. Assumption', header=None)
    investment = safe_float(df_ass.iloc[13, 2])
    
    return p_name, o_irr, years, cash_flow, volumes, investment

try:
    p_name, o_irr, years, cf, vol, inv = load_excel_data()

    st.title(f"🚀 {p_name} 실시간 시뮬레이션 대시보드")
    
    # 사이드바: 4대 핵심 변수 배치
    st.sidebar.header("🕹️ 시나리오 변수 설정")
    s_price = st.sidebar.slider("1. 판가 변동 (%)", -20.0, 20.0, 0.0, 0.5)
    s_vol = st.sidebar.slider("2. 물량 변동 (%)", -30.0, 30.0, 0.0, 1.0)
    s_cost = st.sidebar.slider("3. 제조원가 변동 (%)", -20.0, 20.0, 0.0, 0.5)
    s_inv = st.sidebar.slider("4. 초기투자비 변동 (%)", -20.0, 20.0, 0.0, 1.0)

    # 시뮬레이션 계산 로직
    tax_rate = 0.22
    # 판가/물량/원가 변화에 따른 현금흐름 조정
    # 단순화된 민감도 로직: (매출변화 - 원가변화) * (1-법인세)
    price_impact = (s_price/100) * 1200 * vol * (1 - tax_rate)
    vol_impact = (s_vol/100) * cf # 물량은 현금흐름 전체에 비례한다고 가정
    cost_impact = (s_cost/100) * 800 * vol * (1 - tax_rate) # 800은 가정된 평균제조원가
    
    sim_cf = cf + price_impact + vol_impact - cost_impact
    sim_inv = inv * (1 + s_inv/100)
    
    full_cf = np.insert(sim_cf, 0, -sim_inv)
    sim_irr = npf.irr(full_cf)

    # 결과 대시보드
    m1, m2, m3 = st.columns(3)
    m1.metric("예상 IRR", f"{sim_irr*100:.2f}%", delta=f"{(sim_irr - o_irr)*100:.2f}%")
    m2.metric("원본 IRR (기준)", f"{o_irr*100:.1f}%")
    m3.metric("총 투자비", f"{sim_inv/1000000:,.0f}M KRW")

    # 차트
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=sim_cf, mode='lines+markers', name='시뮬레이션 현금흐름', line=dict(color='#1f77b4', width=4)))
    fig.add_trace(go.Scatter(x=years, y=cf, mode='lines', name='기존 현금흐름(Base)', line=dict(color='gray', dash='dash')))
    fig.update_layout(title="시나리오별 순현금흐름(Net Cash Flow) 추이", xaxis_title="연도", yaxis_title="KRW")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 데이터를 읽는 중 오류가 발생했습니다: {e}")
    st.info("엑셀 파일 내 'Net cash flow' 행을 찾을 수 없거나 시트 이름이 다를 수 있습니다.")
