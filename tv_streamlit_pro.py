import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests
import json
from alert_editor import apply_alert_rules

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "REPLACE_WITH_YOUR_CHAT_ID")

def send_telegram_alert(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# --- LOAD ALERT RULES ---
def load_alert_rules():
    try:
        with open("alert_rules.json") as f:
            return json.load(f)
    except:
        return {}

# --- FETCH & PROCESS DATA ---
def fetch_data(symbol, interval, period, indicators):
    df = yf.download(symbol, interval=interval, period=period)
    if df.empty:
        return df

    if "EMA" in indicators:
        df["EMA20"] = ta.ema(df["Close"], 20)
        df["EMA50"] = ta.ema(df["Close"], 50)
    if "SMA" in indicators:
        df["SMA20"] = ta.sma(df["Close"], 20)
    if "RSI" in indicators:
        df["RSI"] = ta.rsi(df["Close"], 14)
    if "MACD" in indicators:
        macd = ta.macd(df["Close"])
        df = pd.concat([df, macd], axis=1)
    if "Bollinger" in indicators:
        bb = ta.bbands(df["Close"], 20)
        df = pd.concat([df, bb], axis=1)

    return df

# --- PLOTLY CHART ---
def plot_chart(df, symbol, indicators):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
                                 low=df["Low"], close=df["Close"], name="Candles"))

    if "EMA" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA20", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], name="EMA50", line=dict(color="cyan")))
    if "SMA" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA20", line=dict(color="orange")))
    if "Bollinger" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["BBL_20_2.0"], name="BB Lower", line=dict(dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["BBU_20_2.0"], name="BB Upper", line=dict(dash="dot")))

    fig.update_layout(title=f"{symbol} Chart", template="plotly_dark", height=600)
    return fig

# --- UI ---
st.set_page_config(layout="wide")
st.title("📊 TradingView Pro – Streamlit App")

symbols = st.text_input("Enter symbols (comma-separated)", value="AAPL,BTC-USD").upper().split(",")
interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], index=3)
period = st.selectbox("Period", ["1d", "5d", "7d", "1mo"], index=2)
indicators = st.multiselect("Indicators", ["EMA", "SMA", "MACD", "RSI", "Bollinger"], default=["EMA", "RSI"])
autorefresh = st.checkbox("🔁 Auto-refresh every 2 mins")

rules = load_alert_rules()

if st.button("📈 Run Analysis"):
    for symbol in symbols:
        df = fetch_data(symbol.strip(), interval, period, indicators)
        if df is None or df.empty:
            st.warning(f"No data for {symbol}")
            continue

        st.subheader(symbol.strip())
        st.plotly_chart(plot_chart(df, symbol, indicators), use_container_width=True)

        alerts = apply_alert_rules(symbol.strip(), df, rules)
        for alert_msg in alerts:
            st.success(alert_msg)
            send_telegram_alert(alert_msg)

if autorefresh:
    st.experimental_rerun()
