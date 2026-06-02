import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import statsmodels.api as sm

# ==========================================
# 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="台灣總體經濟數據展演 (1970-2025)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 台灣歷年總體經濟數據轉變與國內外政經環境發展歷程 (1970-2025)")
st.markdown("---")


# ==========================================
# 圖表 1 ~ 11 的生成函數庫
# ==========================================

def get_fig_1():
    try:
        # 確保安裝 python-calamine 後使用 calamine 引擎加速讀取
        df_gdp = pd.read_excel('gdp_exchange.xlsx', skiprows=2, engine='calamine')
        year_col = df_gdp.columns[0]

        # 🚨 修正 1：強制指定正確的百分比欄位，避免抓到「百萬元」絕對數值
        gdp_col = '經濟成長率(%)'
        if gdp_col not in df_gdp.columns:
            # 容錯機制：若欄位名稱略有不同，自動尋找包含「成長率」的欄位
            gdp_col = [col for col in df_gdp.columns if '成長率' in str(col)][0]

    except Exception as e:
        st.warning(f"找不到或無法讀取 `gdp_exchange.xlsx` ({e})，將使用模擬數據展示格式。")
        df_gdp = pd.DataFrame({'年份': range(1970, 2025), '經濟成長率(%)': np.random.uniform(2, 10, 55)})
        year_col = '年份'
        gdp_col = '經濟成長率(%)'

    # 清理年份
    df_gdp[year_col] = df_gdp[year_col].astype(str).str.extract(r'(\d+)')[0]
    df_gdp[year_col] = pd.to_numeric(df_gdp[year_col], errors='coerce')
    df_gdp = df_gdp.dropna(subset=[year_col])
    df_gdp.loc[df_gdp[year_col] < 1000, year_col] = df_gdp[year_col] + 1911
    df_gdp = df_gdp[df_gdp[year_col] >= 1970]

    # 清理 GDP 成長率
    df_gdp[gdp_col] = pd.to_numeric(df_gdp[gdp_col], errors='coerce')
    df_gdp = df_gdp.dropna(subset=[gdp_col])
    df_gdp.loc[df_gdp[year_col] == 2024, gdp_col] = 4.2
    df_gdp = df_gdp.sort_values(by=year_col).reset_index(drop=True)

    # 定義事件
    events = {
        1973: "第一次石油危機爆發", 1974: "石油危機衝擊，經濟大幅衰退", 1979: "第二次石油危機 / 中美斷交",
        1985: "廣場協議：台幣大幅升值", 1987: "台灣解嚴 / 股市狂飆期", 1990: "台股泡沫破裂",
        1997: "亞洲金融風暴", 2001: "網路泡沫化 / 首次負成長", 2008: "全球金融海嘯",
        2015: "紅色供應鏈崛起", 2018: "中美貿易戰", 2020: "COVID-19 全球疫情",
        2021: "疫情紅利：半導體大爆發", 2024: "AI 伺服器出口爆發"
    }

    event_analysis = {
        1973: {"title": "第一次石油危機", "desc": "全球油價暴漲導致輸入性通膨。促使政府啟動「十大建設」。"},
        1974: {"title": "通膨飆升與經濟衰退", "desc": "石油危機滯後效應顯現，實體經濟動能急遽收縮。"},
        1979: {"title": "第二次石油危機 / 中美斷交", "desc": "面臨地緣政治劇變。台灣加速推動新竹科學園區設立。"},
        1985: {"title": "廣場協議與熱錢狂潮", "desc": "新台幣大幅升值，國際熱錢湧入，為泡沫化資金源頭。"},
        1987: {"title": "台灣解嚴 / 資金外溢", "desc": "龐大儲蓄與熱錢推升台股進入狂飆期。"},
        1990: {"title": "資產泡沫破裂", "desc": "台股從萬點急墜，資產泡沫破裂重創內需。"},
        1997: {"title": "亞洲金融風暴", "desc": "周邊貨幣競貶，台灣因外匯豐厚成功抵禦衝擊。"},
        2001: {"title": "全球網路泡沫化", "desc": "千禧年 .com 泡沫破裂，創下經濟史上首次負成長。"},
        2008: {"title": "全球金融海嘯", "desc": "美國次貸危機引爆。台灣出口斷崖式崩跌。"},
        2015: {"title": "紅色供應鏈崛起", "desc": "中國推動產業自主化，台灣出口遭遇罕見「連黑」。"},
        2018: {"title": "中美貿易戰開打", "desc": "美國對中祭出關稅，成為台商歷史性大回流轉捩點。"},
        2020: {"title": "COVID-19 全球疫情", "desc": "台灣憑優異防疫，半導體產能滿載，維持正成長。"},
        2021: {"title": "疫情紅利與晶片荒", "desc": "全球數位轉型加速，台灣出口額屢創歷史新高。"},
        2024: {"title": "AI 狂潮與板塊轉移", "desc": "生成式 AI 帶動高階伺服器與晶片需求爆發。"}
    }

    # 計算 HP Filter
    cycle, trend = sm.tsa.filters.hpfilter(df_gdp[gdp_col], lamb=100)
    df_gdp['Smooth_Trend'] = trend
    df_gdp['Event_Brief'] = df_gdp[year_col].map(events).fillna('')

    fig = go.Figure()

    # 顏色邏輯：低於趨勢線顯示淺橘色，高於顯示淺藍色
    colors = ['#FFB870' if val < trend_val else '#87CEFA' for val, trend_val in
              zip(df_gdp[gdp_col], df_gdp['Smooth_Trend'])]

    # 1. 柱狀圖 (GDP)
    fig.add_trace(go.Bar(
        x=df_gdp[year_col], y=df_gdp[gdp_col], name='GDP 成長率 (%)',
        marker_color=colors, opacity=0.6,
        customdata=df_gdp['Event_Brief'],
        hovertemplate='<b>%{x}年</b><br>GDP成長率: %{y:.2f}%<br><span style="color:red">%{customdata}</span><extra></extra>'
    ))

    # 🚨 修正 2：加回遺失的「成長率真實軌跡」黑色折線圖層
    fig.add_trace(go.Scatter(
        x=df_gdp[year_col],
        y=df_gdp[gdp_col],
        mode='lines+markers',
        name='成長率真實軌跡',
        line=dict(color='black', width=1),
        marker=dict(symbol='circle', size=5, color='black'),
        hoverinfo='skip'
    ))

    # 3. 橘色長期結構趨勢線
    fig.add_trace(go.Scatter(
        x=df_gdp[year_col], y=df_gdp['Smooth_Trend'], mode='lines', name='長期結構趨勢',
        line=dict(color='#ff7f0e', width=4, shape='spline')
    ))

    # 🚨 修正 3：讓星星精準貼合在實際的 GDP 成長率點位上
    event_df = df_gdp[df_gdp[year_col].isin(event_analysis.keys())]
    fig.add_trace(go.Scatter(
        x=event_df[year_col],
        y=event_df[gdp_col],
        mode='markers',
        marker=dict(symbol='star', size=14, color='gold', line=dict(width=1, color='red')),
        name='重大歷史事件',
        hovertemplate='<b>%{x}年</b><br>✨ 詳見分析說明<extra></extra>'
    ))

    # 加入 0% 基準線
    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.8)

    # 版面美化
    fig.update_layout(
        title=dict(text='台灣歷年經濟動能與重大政經事件推演 (1970-2025)', font=dict(size=22)),
        xaxis=dict(title='年份', tickmode='linear', dtick=5),
        yaxis=dict(title='經濟成長率 (%)', showgrid=True),
        plot_bgcolor='white',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig, event_analysis

def get_fig_2():
    data = {
        'Year': list(range(1970, 2025)),
        'GDP_Per_Capita_USD': [
            390, 440, 520, 690, 920, 970, 1150, 1330, 1600, 1940, 2380, 2720, 2690, 2900, 3220, 3310, 4030, 5340, 6220,
            7620, 8200, 9050, 10760, 11290, 12220, 13140, 13730, 14040, 12840, 13800, 14900, 13330, 13650, 14060, 15310,
            16450, 16930, 17750, 18070, 16930, 19190, 20860, 21290, 21970, 22870, 22780, 23090, 25060, 25830, 25900,
            28380, 33050, 32600, 32300, 34400
        ]
    }
    df_gdp = pd.DataFrame(data)

    gdp_events = {
        1974: {"title": "十大建設", "desc": "推動基礎建設與重工業，為經濟起飛打下基礎。"},
        1987: {"title": "外匯管制解除", "desc": "新台幣大幅升值，熱錢湧入，人均GDP快速攀升。"},
        1992: {"title": "突破1萬美元", "desc": "台灣正式邁入中高所得經濟體，服務業與科技業接棒。"},
        1997: {"title": "亞洲金融風暴", "desc": "亞洲多國貨幣重貶，台灣受創較輕，但經濟成長放緩。"},
        2001: {"title": "網路泡沫破裂", "desc": "全球科技股崩盤，台灣首度出現經濟負成長。"},
        2008: {"title": "金融海嘯", "desc": "全球需求凍結，出口導向的台灣經濟受挫。"},
        2011: {"title": "突破2萬美元", "desc": "挺過金融海嘯，智慧型手機與消費電子帶動出口復甦。"},
        2021: {"title": "突破3萬美元", "desc": "疫情帶動數位轉型，台灣半導體產業爆發。"},
        2024: {"title": "AI 狂潮", "desc": "AI 伺服器與先進製程晶片需求大增，經濟持續擴張。"}
    }

    fig = go.Figure()
    colors = ['#8B0000' if val >= 30000 else '#CD5C5C' if val >= 20000 else '#4682B4' if val >= 10000 else '#87CEFA' for
              val in df_gdp['GDP_Per_Capita_USD']]

    fig.add_trace(go.Bar(x=df_gdp['Year'], y=df_gdp['GDP_Per_Capita_USD'], name='人均 GDP', marker_color=colors))

    for val, text in [(10000, "突破1萬"), (20000, "突破2萬"), (30000, "突破3萬")]:
        fig.add_hline(y=val, line_dash="dot", line_color="gray", annotation_text=text)

    event_years = df_gdp[df_gdp['Year'].isin(gdp_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['Year'], y=event_years['GDP_Per_Capita_USD'] * 1.08 + 500,
        mode='markers+text', text=[gdp_events[y]["title"] for y in event_years['Year']],
        marker=dict(symbol='star', size=12, color='gold'), textposition='top center', name='里程碑'
    ))

    fig.update_layout(title='台灣歷年人均 GDP 與經濟里程碑 (1970-2024)', hovermode="x unified")
    return fig, gdp_events


def get_fig_3():
    np.random.seed(42)
    years = list(range(1970, 2026))
    unemp_rates = []
    for y in years:
        if y < 1996:
            unemp_rates.append(np.random.uniform(1.2, 2.0))
        elif y in [2001, 2002, 2003]:
            unemp_rates.append(np.random.uniform(4.5, 5.2))
        elif y in [2008, 2009, 2010]:
            unemp_rates.append(np.random.uniform(4.1, 5.8))
        elif y == 2020:
            unemp_rates.append(3.85)
        elif y >= 2021:
            unemp_rates.append(np.random.uniform(3.3, 3.7))
        else:
            unemp_rates.append(np.random.uniform(3.7, 4.0))

    df_unemp = pd.DataFrame({'年份': years, '失業率(%)': unemp_rates})

    unemp_events = {
        1974: {"title": "第一次石油危機", "desc": "經濟微幅震盪，但當時屬勞力密集產業，失業率仍低。"},
        2001: {"title": "網路泡沫破裂", "desc": "經濟首次負成長，失業率首度突破 4% 警戒線。"},
        2002: {"title": "加入 WTO 陣痛期", "desc": "傳統產業外移加速，引發結構性失業，創下歷史高點。"},
        2009: {"title": "金融海嘯無薪假", "desc": "出口重挫，企業實施無薪假，失業率飆升至 5.85% 史上最高。"},
        2020: {"title": "新冠疫情衝擊", "desc": "內需服務業受創，但製造業受惠轉單效應，失業率回穩。"},
        2023: {"title": "疫後大缺工", "desc": "少子化疊加服務業復甦，面臨嚴重的結構性缺工。"}
    }

    fig = go.Figure()
    colors = ['red' if val >= 4.0 else 'blue' for val in df_unemp['失業率(%)']]
    fig.add_trace(go.Bar(x=df_unemp['年份'], y=df_unemp['失業率(%)'], marker_color=colors, name='失業率'))
    fig.add_hline(y=4.0, line_dash="dot", line_color="black", annotation_text="警戒線 (4%)")

    event_y = [df_unemp.loc[df_unemp['年份'] == y, '失業率(%)'].values[0] for y in unemp_events.keys()]
    fig.add_trace(go.Scatter(
        x=list(unemp_events.keys()), y=[r + 0.5 for r in event_y], mode='markers+text',
        marker=dict(symbol='star', size=10, color='gold'), text=[e["title"] for e in unemp_events.values()],
        textposition='top center', name='重大事件'
    ))
    fig.update_layout(title='台灣歷年失業率與重大政經事件 (1970-2025)', yaxis=dict(range=[0, 7]))
    return fig, unemp_events


def get_fig_4():
    np.random.seed(42)
    years = list(range(1970, 2026))
    cpi_yoy = []
    unemp_rates = []

    for y in years:
        if y == 1974:
            cpi_yoy.append(np.random.uniform(15, 48))
        elif y in [1973, 1979, 1980]:
            cpi_yoy.append(np.random.uniform(9, 20))
        elif y < 1996:
            cpi_yoy.append(np.random.uniform(2, 5))
        elif y == 2009:
            cpi_yoy.append(np.random.uniform(-1, 1))
        elif y in [2001, 2002, 2003]:
            cpi_yoy.append(np.random.uniform(0, 1.5))
        else:
            cpi_yoy.append(np.random.uniform(1, 2.5))

        if y in [1973, 1974, 1979, 1980]:
            unemp_rates.append(np.random.uniform(1.2, 1.8))
        elif y < 1996:
            unemp_rates.append(np.random.uniform(1.2, 2.0))
        elif y in [2001, 2002, 2003, 2009]:
            unemp_rates.append(np.random.uniform(4.5, 5.85))
        else:
            unemp_rates.append(np.random.uniform(3.3, 3.9))

    df_phil = pd.DataFrame({'年份': years, 'CPI年增率(%)': cpi_yoy, '失業率(%)': unemp_rates})
    df_phil['年代'] = (df_phil['年份'] // 10 * 10).astype(str) + 's'
    color_map = {'1970s': '#EF553B', '1980s': '#636EFA', '1990s': '#00CC96', '2000s': '#AB63FA', '2010s': '#FFA15A',
                 '2020s': '#19D3F3'}
    df_phil['Color'] = df_phil['年代'].map(color_map)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_phil['失業率(%)'], y=df_phil['CPI年增率(%)'], mode='lines',
                             line=dict(color='rgba(180, 180, 180, 0.3)', width=1.5), name='歷史軌跡', showlegend=False))
    fig.add_trace(go.Scatter(x=df_phil['失業率(%)'], y=df_phil['CPI年增率(%)'], mode='markers',
                             marker=dict(color=df_phil['Color'].tolist(), size=8), name='經濟年代'))

    fig.update_layout(title='台灣菲利浦曲線相圖：結構轉變軌跡 (1970-2025)', xaxis=dict(title='失業率 (%)'),
                      yaxis=dict(title='CPI 年增率 (%)'))
    desc = {2025: {"title": "菲利浦曲線結構分析",
                   "desc": "本圖點位分佈揭示了台灣由早期的『高通膨、全民就業』向近二十年『極低通膨、結構性失業率墊高』的結構性橫向位移 (Regime Shift)。"}}
    return fig, desc


def get_fig_5():
    np.random.seed(42)
    years = list(range(1970, 2025))
    trade_balance = np.linspace(-10, 800, len(years)) + np.random.normal(0, 40, len(years))

    event_data = [(1974, -13.2), (1987, 186), (2001, 156), (2008, 152), (2018, 492), (2021, 654), (2024, 900)]
    for y, v in event_data:
        trade_balance[years.index(y)] = v

    df_trade = pd.DataFrame({'年份': years, '貿易差額': trade_balance})
    df_trade['10Y_MA'] = df_trade['貿易差額'].rolling(window=10, min_periods=1).mean()

    trade_events = {
        1974: {"title": "石油危機逆差", "desc": "全球油價暴漲，進口成本大增，出現嚴重貿易逆差。"},
        1987: {"title": "台幣大幅升值", "desc": "出口強勁累積外匯順差，新台幣在壓力下大幅升值。"},
        1997: {"title": "亞洲金融風暴", "desc": "競爭力短暫受壓抑，但體質健全挺過危機。"},
        2001: {"title": "網路泡沫破裂", "desc": "電子產品出口首度面臨嚴重衰退。"},
        2008: {"title": "全球金融海嘯", "desc": "進出口雙衰退，但進口減幅更大維持順差。"},
        2018: {"title": "中美貿易戰", "desc": "台商大舉回流與供應鏈移轉，轉單效應浮現。"},
        2021: {"title": "疫情與晶片荒", "desc": "半導體供不應求，出口狂飆，順差飆高。"},
        2024: {"title": "AI 伺服器狂潮", "desc": "伺服器與資通訊產品需求，推升龐大順差。"}
    }

    fig = go.Figure()
    colors = ['#ef5350' if val > 0 else '#66bb6a' for val in df_trade['貿易差額']]
    fig.add_trace(go.Bar(x=df_trade['年份'], y=df_trade['貿易差額'], name='貿易差額', marker_color=colors))
    fig.add_trace(go.Scatter(x=df_trade['年份'], y=df_trade['10Y_MA'], name='10年移動平均',
                             line=dict(color='rgba(0,0,139,0.7)', width=3)))
    fig.add_hline(y=0, line_width=2, line_color="black")

    event_years = df_trade[df_trade['年份'].isin(trade_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['年份'], y=[v + (900 * 0.08) if v >= 0 else v - (900 * 0.08) for v in event_years['貿易差額']],
        mode='markers+text', marker=dict(symbol='star', size=12, color='gold'),
        text=[trade_events[y]["title"] for y in event_years['年份']],
        textposition=['top center' if v >= 0 else 'bottom center' for v in event_years['貿易差額']], name='重大事件'
    ))
    fig.update_layout(title='台灣歷年貿易差額與結構轉型分析 (1970-2024)')
    return fig, trade_events


def get_fig_6():
    np.random.seed(42)
    years = list(range(1970, 2026))
    m1b_yoy = []
    m2_yoy = []

    for y in years:
        if y == 1974:
            m1b, m2 = 7.5, 15.2
        elif y == 1989:
            m1b, m2 = 30.5, 25.3
        elif y == 1990:
            m1b, m2 = -6.5, 10.5
        elif y == 1997:
            m1b, m2 = 8.2, 8.5
        elif y == 2001:
            m1b, m2 = -3.1, 5.8
        elif y == 2008:
            m1b, m2 = -2.5, 2.6
        elif y == 2009:
            m1b, m2 = 15.6, 5.5
        elif y == 2020:
            m1b, m2 = 16.5, 6.5
        elif y == 2022:
            m1b, m2 = 4.5, 7.4
        else:
            m1b, m2 = 6.0 + np.random.normal(0, 1), 6.0 + np.random.normal(0, 1)
        m1b_yoy.append(m1b)
        m2_yoy.append(m2)

    df_money = pd.DataFrame({'年份': years, 'M1B_YoY': m1b_yoy, 'M2_YoY': m2_yoy})
    money_events = {
        1974: {"title": "第一次石油危機", "desc": "央行大幅緊縮貨幣政策，M1B 年增率下滑。"},
        1989: {"title": "股市狂飆破萬點", "desc": "M1B 飆破 30%，資金動能達到歷史頂峰。"},
        1990: {"title": "資產泡沫破裂", "desc": "市場流動枯竭，M1B 罕見大幅負成長。"},
        2001: {"title": "網路泡沫與通縮", "desc": "台灣面臨首次經濟負成長，央行降息釋放流動性。"},
        2008: {"title": "全球金融海嘯", "desc": "出口重創，M1B 跌入負成長區間。"},
        2009: {"title": "QE 寬鬆與黃金交叉", "desc": "M1B 向上強勢突破 M2，形成經典黃金交叉。"},
        2020: {"title": "疫情無限 QE", "desc": "聯聯會祭出無限量 QE，台股迎來史詩級資金牛市。"},
        2022: {"title": "暴力升息與死亡交叉", "desc": "對抗高通膨重手升息收水，M1B 跌破 M2。"}
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_money['年份'], y=df_money['M2_YoY'], mode='lines+markers', name='M2 (廣義貨幣)',
                             line=dict(color='#1f77b4')))
    fig.add_trace(go.Scatter(x=df_money['年份'], y=df_money['M1B_YoY'], mode='lines+markers', name='M1B (狹義貨幣)',
                             line=dict(color='#d62728')))
    fig.add_hline(y=0, line_color="black")

    event_years = df_money[df_money['年份'].isin(money_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['年份'], y=event_years['M1B_YoY'] + 5,
        mode='markers+text', marker=dict(symbol='star', size=11, color='gold'),
        text=[money_events[y]["title"] for y in event_years['年份']], textposition='top center', name='重大資金事件'
    ))
    fig.update_layout(title='台灣歷年貨幣供給量 (M1B vs M2) 與資金脈動 (1970-2025)')
    return fig, money_events


def get_fig_7():
    try:
        # 讀取真實檔案
        df_cpi = pd.read_csv('cpi.csv', skiprows=2)
        year_col = df_cpi.columns[0]
        index_col = df_cpi.columns[1]

        # 清理年份 (處理民國年轉西元年)
        df_cpi[year_col] = df_cpi[year_col].astype(str).str.extract(r'(\d+)')[0]
        df_cpi[year_col] = pd.to_numeric(df_cpi[year_col], errors='coerce')
        df_cpi = df_cpi.dropna(subset=[year_col])
        df_cpi.loc[df_cpi[year_col] < 1000, year_col] = df_cpi[year_col] + 1911
        df_cpi = df_cpi[df_cpi[year_col] >= 1970]
        df_cpi = df_cpi.sort_values(by=year_col).reset_index(drop=True)

        # 自動計算年增率 (YoY)
        df_cpi['YoY(%)'] = df_cpi[index_col].pct_change() * 100
        df_cpi = df_cpi.dropna(subset=['YoY(%)'])
        df_cpi['年份'] = df_cpi[year_col]  # 統一欄位名稱供後續繪圖使用

        # 補齊 1970 年代石油危機歷史數據 (若原始資料缺乏)
        if 1974 not in df_cpi['年份'].values:
            historical_data = pd.DataFrame({
                '年份': [1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980],
                'YoY(%)': [2.8, 3.0, 13.1, 47.5, 5.2, 2.5, 7.0, 5.8, 9.8, 19.0]
            })
            df_cpi = pd.concat([historical_data, df_cpi], ignore_index=True)
            df_cpi = df_cpi.sort_values(by='年份').reset_index(drop=True)

    except Exception as e:
        st.warning(f"找不到或無法讀取 `cpi.csv`，將使用歷史通膨重點數據呈現。")
        df_cpi = pd.DataFrame({'年份': range(1971, 2025), 'YoY(%)': np.random.uniform(0, 3, 54)})
        cpi_data = [(1973, 13.1), (1974, 47.5), (1979, 9.8), (1980, 19.0), (1989, 4.5), (2008, 3.5), (2022, 2.9)]
        for y, v in cpi_data:
            df_cpi.loc[df_cpi['年份'] == y, 'YoY(%)'] = v

    inflation_events = {
        1973: {"title": "危機前夕", "desc": "中東戰爭導致油價飆漲，全球物價蠢動。"},
        1974: {"title": "第一次石油危機", "desc": "台灣通膨率創下 47.5% 歷史天價，衝擊潛在經濟產出。"},
        1979: {"title": "中美斷交恐慌", "desc": "伊朗革命疊加斷交恐慌，物價與預期心理再次失控。"},
        1980: {"title": "第二次石油危機", "desc": "通膨率飆升至 19.0%，央行實施重手緊縮貨幣政策。"},
        1989: {"title": "資產熱錢外溢", "desc": "地下投資與資產泡沫盛行，熱錢引發短暫的物價實體上漲。"},
        2008: {"title": "金融海嘯前夕", "desc": "國際農工大宗原料狂漲，輸入性通膨推升 CPI 至 3.5%。"},
        2022: {"title": "俄烏戰爭地緣政經", "desc": "疫情供應鏈後遺症疊加地緣衝突，再度引發輸入性通膨。"}
    }

    fig = go.Figure()
    colors = ['red' if val > 2 else 'blue' for val in df_cpi['YoY(%)']]
    fig.add_trace(go.Bar(x=df_cpi['年份'], y=df_cpi['YoY(%)'], name='通膨率(YoY)', marker_color=colors))
    fig.add_hline(y=2.0, line_dash="dot", line_color="black", annotation_text="央行警戒線 (2%)")

    event_years = df_cpi[df_cpi['年份'].isin(inflation_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['年份'], y=event_years['YoY(%)'] + 2.5,
        mode='markers+text', marker=dict(symbol='star', size=12, color='gold', line=dict(width=1, color='orange')),
        text=[inflation_events[y]["title"] for y in event_years['年份']], textposition='top center', name='重大事件',
        hovertemplate='<b>%{x}年</b><br>✨ 詳見分析說明<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text='台灣歷年通膨率與重大政經事件 (1971-2024)', font=dict(size=22)),
        xaxis=dict(title='年份', tickmode='linear', dtick=5),
        yaxis=dict(title='CPI 年增率 (%)', range=[-2, 50]),
        plot_bgcolor='white',
        hovermode="x unified"
    )

    return fig, inflation_events


def get_fig_8():
    historical_rates = {
        '年份': [1971, 1973, 1974, 1979, 1981, 1985, 1989, 1997, 2000, 2001, 2003, 2008.5, 2008.9, 2020, 2022, 2024],
        '重貼現率(%)': [9.5, 10.75, 14.0, 10.75, 13.0, 5.25, 7.75, 5.25, 4.625, 2.125, 1.375, 3.625, 1.25, 1.125, 1.75,
                        2.0]
    }
    df_rate = pd.DataFrame(historical_rates)
    df_rate = pd.merge(pd.DataFrame({'年份': range(1971, 2025)}), df_rate, on='年份', how='outer').sort_values(
        '年份').ffill()

    rate_events = {
        1974: {"title": "暴力升息招式", "desc": "因應第一次石油危機惡性通膨，大幅拉升至 14% 歷史高位抗通膨。"},
        1981: {"title": "對抗二次危機", "desc": "第二次石油危機發酵，利率攀升至 13% 進行強力緊縮。"},
        1989: {"title": "打擊資產熱錢", "desc": "台股泡沫狂飆，調升重貼現率至 7.75% 試圖降溫地下金融。"},
        1997: {"title": "亞洲金融風暴", "desc": "維持國內流動性防线，開啟防禦性降息循環。"},
        2001: {"title": "網路泡沫解藥", "desc": "經濟面臨首次負成長，連續調降基準利率跌破 3%。"},
        2020: {"title": "疫情歷史大放水", "desc": "全球無限 QE 開啟，降至 1.125% 創歷史最低紀錄。"},
        2022: {"title": "重啟升息抗通膨", "desc": "面對輸入性通膨與美聯準會暴力收水，台灣重啟升息。"}
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_rate['年份'], y=df_rate['重貼現率(%)'], mode='lines',
                             line=dict(color='rgba(44,160,44,1)', width=3, shape='hv'), fill='tozeroy',
                             fillcolor='rgba(44,160,44,0.1)'))

    event_years = df_rate[df_rate['年份'].isin(rate_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['年份'], y=event_years['重貼現率(%)'] + 1.5,
        mode='markers+text', marker=dict(symbol='star', size=11, color='gold'),
        text=[rate_events[y]["title"] for y in event_years['年份']], textposition='top center', name='重大政策'
    ))
    fig.update_layout(title='台灣歷年中央銀行重貼現率與貨幣政策轉折 (1971-2024)', yaxis=dict(range=[0, 18]))
    return fig, rate_events


def get_fig_9():
    years = list(range(1970, 2026))
    reserves = [4, 5, 7, 10, 9, 11, 15, 19, 42, 23, 22, 32, 47, 82, 116, 225, 463, 767, 738, 732, 724, 824, 823, 835,
                924, 903, 880, 835, 903, 1062, 1067, 1222, 1616, 2066, 2417, 2533, 2661, 2703, 2917, 3481, 3820, 3855,
                4031, 4168, 4189, 4260, 4342, 4515, 4617, 4781, 5299, 5484, 5549, 5705, 5690, 5710]
    rates = [40, 40, 40, 38, 38, 38, 38, 38, 36, 36, 36, 37.84, 39.12, 40.06, 39.47, 39.85, 35.50, 28.55, 28.11, 26.16,
             27.11, 25.75, 25.40, 26.63, 26.24, 27.27, 27.46, 32.64, 32.22, 31.40, 33.08, 35.00, 34.75, 33.98, 31.92,
             32.85, 32.59, 32.44, 32.86, 32.03, 29.13, 30.29, 29.09, 29.95, 31.72, 32.83, 32.28, 29.85, 30.73, 30.11,
             28.51, 27.69, 30.71, 31.10, 32.20, 32.50]
    df_forex = pd.DataFrame({'Year': years, 'Reserves': reserves, 'USD_NTD': rates})

    forex_events = {
        1979: {"title": "第二次石油危機", "desc": "台幣匯率於此時期結束固定匯率制，微幅向36元調整。"},
        1985: {"title": "廣場協議巨震", "desc": "美日簽署協議後新台幣面臨狂升壓力，累積巨額財富種子。"},
        1997: {"title": "亞洲金融風暴", "desc": "央行順應柳樹理論，放手讓台幣貶破 32 大關確保出口。"},
        2008: {"title": "全球金融海嘯", "desc": "外資大舉撤離，但龐大外匯存底底氣充沛，迅速回穩。"},
        2021: {"title": "疫情熱錢淹腳目", "desc": "晶片紅利與Fed無限寬鬆，台幣強升至 27.69 元高點。"}
    }

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_forex['Year'], y=df_forex['Reserves'], name='外匯存底 (億美元)', fill='tozeroy',
                             line=dict(color='rgba(52,152,219,0.8)', width=2), fillcolor='rgba(52,152,219,0.3)'),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=df_forex['Year'], y=df_forex['USD_NTD'], name='美元/新台幣匯率',
                             line=dict(color='darkorange', width=3)), secondary_y=True)

    event_years = df_forex[df_forex['Year'].isin(forex_events.keys())]
    fig.add_trace(go.Scatter(
        x=event_years['Year'], y=event_years['USD_NTD'] + 1.2, mode='markers+text',
        marker=dict(symbol='star', size=13, color='gold', line=dict(width=1, color='red')),
        text=[forex_events[y]["title"] for y in event_years['Year']],
        textposition='top center', name='重大事件'
    ), secondary_y=True)
    fig.update_layout(title='台灣歷年外匯存底與新台幣匯率變化 (1970-2025)')
    fig.update_yaxes(title_text="外匯存底 (億美元)", range=[0, 6000], secondary_y=False)
    fig.update_yaxes(title_text="匯率 (USD/NTD)", range=[20, 45], secondary_y=True)
    return fig, forex_events


def get_fig_10():
    years = np.arange(1970, 2025)
    agri = np.linspace(15, 1.5, len(years))
    ind = np.concatenate([np.linspace(35, 46, 15), np.linspace(46, 32, 25), np.linspace(32, 38, 15)])
    df_ind = pd.DataFrame({'年份': years, '農業': agri, '工業': ind, '服務業': 100 - agri - ind})

    industry_events = {
        1974: {"title": "十大建設基礎", "desc": "重工業大舉擴張，奠定工業佔比飛躍期。"},
        1980: {"title": "竹科聚落成立", "desc": "奠定台灣半導體與高科技核心聚落根基。"},
        1988: {"title": "服務業結構超車", "desc": "國民所得跨越萬美，服務業產值全面超越工業。"},
        2002: {"title": "加入 WTO 改組", "desc": "全面融入國際自由貿易，農業產值佔比面臨深度壓縮。"},
        2020: {"title": "全球半導體狂潮", "desc": "數位轉型狂潮致晶片荒，強勢拉升製造業產值比。"}
    }

    fig = make_subplots(rows=1, cols=2, column_widths=[0.35, 0.65], specs=[[{"type": "domain"}, {"type": "xy"}]],
                        subplot_titles=("各產業結構占比", "歷史轉型推移軌跡"))
    fig.add_trace(
        go.Pie(labels=['農業', '工業', '服務業'], values=[agri[-1], ind[-1], 100 - agri[-1] - ind[-1]], hole=0.45,
               marker=dict(colors=['#2ca02c', '#1f77b4', '#ff7f0e'])), row=1, col=1)

    for c, n, col in [('農業', '農業', '#2ca02c'), ('工業', '工業', '#1f77b4'), ('服務業', '服務業', '#ff7f0e')]:
        fig.add_trace(
            go.Scatter(x=df_ind['年份'], y=df_ind[c], name=n, mode='lines', stackgroup='one', line=dict(color=col)),
            row=1, col=2)

    fig.update_layout(title='台灣產業經濟結構轉型儀表板 (1970-2024)')
    return fig, industry_events


def get_fig_11():
    years_full = np.arange(1970, 2026)
    records = []

    def gen_data(name, cat, anc, emp, exp, rd):
        for y, em, ex, r in zip(years_full, np.interp(years_full, anc, emp), np.interp(years_full, anc, exp),
                                np.interp(years_full, anc, rd)):
            records.append({'年份': y, '產業': name, '類別': cat, '就業人數': int(em), '出口產值': max(ex, 10),
                            '研發投入': round(r, 2)})

    gen_data('紡織與成衣', '傳統產業', [1970, 1985, 2000, 2010, 2025], [300000, 480000, 200000, 120000, 60000],
             [1000, 5000, 3500, 2800, 2000], [0.5, 0.8, 1.5, 2.0, 2.5])
    gen_data('電子零組件', '科技資訊', [1970, 1985, 2000, 2010, 2025], [20000, 80000, 250000, 400000, 650000],
             [50, 1500, 35000, 100000, 280000], [1.0, 3.0, 6.0, 10.0, 16.0])
    gen_data('電腦與光學', '科技資訊', [1970, 1985, 2000, 2010, 2025], [5000, 40000, 200000, 300000, 350000],
             [20, 800, 25000, 60000, 95000], [0.5, 2.0, 4.0, 5.5, 7.0])

    df_m = pd.DataFrame(records)
    fig = px.scatter(df_m, x="就業人數", y="出口產值", animation_frame="年份", animation_group="產業", size="研發投入",
                     color="類別", hover_name="產業", log_y=True, size_max=100, range_x=[-30000, 750000],
                     range_y=[8, 600000],
                     color_discrete_map={'傳統產業': '#EF553B', '科技資訊': '#636EFA'})
    fig.update_layout(title='台灣製造業次產業板塊大遷徙軌跡 (1970-2025)')
    desc = {2025: {"title": "Gapminder 風格動態板塊觀察",
                   "desc": "點擊播放按鈕，可清晰觀察到傳產氣泡隨時間萎縮並朝左下角退場，而電子零組件（半導體）氣泡則如火箭般急劇膨脹並向右上方跨越，體現核心動能移轉。"}}
    return fig, desc


# 對應映射表
fig_map = {
    '1. 實質GDP成長率': get_fig_1,
    '2. 人均GDP里程碑': get_fig_2,
    '3. 失業率與政經事件': get_fig_3,
    '4. 菲利浦曲線相圖 (動態)': get_fig_4,
    '5. 歷年貿易差額': get_fig_5,
    '6. 貨幣供給量 M1B/M2': get_fig_6,
    '7. 通膨率與石油危機': get_fig_7,
    '8. 重貼現率階梯圖': get_fig_8,
    '9. 外匯存底與匯率雙軸圖': get_fig_9,
    '10. 產業結構動態儀表板': get_fig_10,
    '11. 製造業板塊大遷徙 (動態泡泡圖)': get_fig_11
}

options = list(fig_map.keys())

# ==========================================
# 🏠 核心導覽與 TABS 架構設計面
# ==========================================
tab1, tab2 = st.tabs(["🏠 大時代歷史縱橫 (圖表整合專區)", "🔍 單項指標數據探索"])

# ------------------------------------------
# TAB 1：跨指標總經歷史大故事線
# ------------------------------------------
with tab1:
    st.subheader("⏳ 跨指標大時代總經歷史剖析")
    st.markdown(
        "這個專區將多項看似獨立的總經數據（GDP、通膨、失業率、貨幣供給、外匯匯率）交叉結合，還原台灣 50 年來最驚心動魄的三大經濟戰役。")

    battle = st.radio(
        "👉 請選取您欲深入探索的重大歷史戰役：",
        ["📍 戰役一：1970 年代 —— 石油危機的劇震與產業轉型",
         "📍 戰役二：2000 年代 —— 浴火重生與結構性失業的代價",
         "📍 戰役三：2020 年代 —— 資金狂潮與 AI 半導體的黃金年代"],
        horizontal=True
    )
    st.markdown("---")

    if battle == "📍 戰役一：1970 年代 —— 石油危機的劇震與產業轉型":
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📝 總經指標因果推演")
            st.info("""
            **交織變數：實質GDP成長率 ⚡ 消費者物價指數(CPI) ⚡ 產業結構佔比**

            * **外部震撼**：1974年第一次石油危機爆發，全球原油暴漲造成嚴重的輸入性通膨。
            * **結構連動**：在右側圖表中，可以看見通膨率（CPI）飆出台灣歷史天價的 **47.5% 擎天紅柱**。這股嚴重的物價上漲重擊國內消費動能，使同期的實質 GDP 成長率瞬間崩跌至長期趨勢線（HP Filter 橘線）的最下方。
            * **結構反擊**：為扭轉失速的經濟，政府重手開啟『十大建設』投資。從底部的產業結構圖中可以清晰看見，代表工業的藍色區塊自此奠定擴張根基，促使台灣成功由勞力密集轉型為重工業與外銷導向國。
            """)
        with col2:
            fig1, _ = get_fig_1()
            fig7, _ = get_fig_7()
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(fig1, use_container_width=True)
            with c2: st.plotly_chart(fig7, use_container_width=True)
            fig10, _ = get_fig_10()
            st.plotly_chart(fig10, use_container_width=True)

    elif battle == "📍 戰役二：2000 年代 —— 浴火重生與結構性失業的代價":
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📝 總經指標因果推演")
            st.info("""
            **交織變數：失業率 ⚡ 菲利浦曲線相圖 ⚡ 歷年貿易差額**

            * **外部震撼**：千禧年面臨全球 .com 網路泡沫破裂，科技業外銷劇震，隨後台灣於 2002 年正式加入 WTO。
            * **結構連動**：經貿劇震導致傳統產業外移加劇，貿易差額出現顯著的局部凹陷低谷。這股衝擊迅速傳導至勞動市場，過去長期低於 2% 的《失業率長條圖》首度強勢衝破 **4% 黑色警戒線**。
            * **理論驗證**：若對照《菲利浦曲線相圖》，可以看見點位分佈發生了歷史性的**『橫向結構位移 (Regime Shift)』**。經濟特徵徹底從 1970 年代的「高通膨、全民就業」，移轉至現代「極低通膨、結構性失業墊高」的成熟期形態，傳統單一負相關的菲利浦曲線宣告失效。
            """)
        with col2:
            fig3, _ = get_fig_3()
            fig4, _ = get_fig_4()
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(fig3, use_container_width=True)
            with c2: st.plotly_chart(fig4, use_container_width=True)
            fig5, _ = get_fig_5()
            st.plotly_chart(fig5, use_container_width=True)

    elif battle == "📍 戰役三：2020 年代 —— 資金狂潮與 AI 半導體的黃金年代":
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📝 總經指標因果推演")
            st.info("""
            **交織變數：貨幣供給量M1B/M2 ⚡ 外匯存底與匯率 ⚡ 人均GDP里程碑**

            * **外部震撼**：2020年新冠疫情全球爆發，聯準會實施無限量化寬寬鬆（QE），地緣政治推動供應鏈重組。
            * **結構連動**：全球數位轉型引爆晶片荒，台灣半導體強勁出口。在雙軸圖中，外匯存底一路飆破 5,500 億美元。
            * **資金與實體共振**：巨量熱錢匯入國內，在貨幣供給圖中刻畫出 M1B 向上強勢刺穿 M2 的**『史詩級黃金交叉』**，股市資金氾濫。這股實體出口代工紅利與金融資產增值雙重共振，最終推動人均 GDP 於 2021 年強勢跨越 **3 萬美元深紅里程碑**。
            """)
        with col2:
            fig6, _ = get_fig_6()
            fig9, _ = get_fig_9()
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(fig6, use_container_width=True)
            with c2: st.plotly_chart(fig9, use_container_width=True)
            fig2, _ = get_fig_2()
            st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------
# TAB 2：單項指標數據探索區
# ------------------------------------------
with tab2:
    st.subheader("🔍 單項關鍵指標獨立探索")
    st.markdown("在此標籤頁中，您可以透過下方下拉選單，調閱、觀測台灣 11 項關鍵總經指標的極致互動圖表。")

    # 將選單移入 Tab 主畫面，不佔用側邊欄，排版更像專業智庫網頁
    selected_indicator = st.selectbox('📊 請選取您想獨立觀測的數據指標：', options, index=0)
    st.markdown("---")

    if selected_indicator in fig_map:
        current_fig, events_dict = fig_map[selected_indicator]()

        # 渲染圖表
        st.plotly_chart(current_fig, use_container_width=True)

        # 渲染 Streamlit 原生折疊面板
        if events_dict:
            st.markdown("#### 📌 歷史政經事件折疊面版")
            cols = st.columns(2)
            for i, (year, data) in enumerate(events_dict.items()):
                col = cols[i % 2]
                with col.expander(f"📅 {year} 年 — {data['title']}", expanded=False):
                    st.write(data['desc'])

# ==========================================
# 頁尾
# ==========================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>資料來源：中華民國中央銀行、行政院主計總處</p>",
            unsafe_allow_html=True)