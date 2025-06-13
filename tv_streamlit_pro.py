import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objs as go
import requests
from datetime import datetime
import time

# Telegram Setup
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# ----------- Functions -----------

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

def get_data(symbol, interval, period, indicators):
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if df.empty:
        return None

    if "EMA" in indicators:
        df["EMA20"] = ta.ema(df["Close"], length=20)
    if "SMA" in indicators:
        df["SMA20"] = ta.sma(df["Close"], length=20)
    if "RSI" in indicators:
        df["RSI"] = ta.rsi(df["Close"], length=14)
    if "MACD" in indicators:
        macd = ta.macd(df["Close"])
        df = pd.concat([df, macd], axis=1)
    if "Bollinger" in indicators:
        bb = ta.bbands(df["Close"], length=20)
        df = pd.concat([df, bb], axis=1)

    return df

def plot_chart(df, symbol, indicators):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Candles"))

    if "EMA" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA 20", line=dict(color='blue')))
    if "SMA" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20", line=dict(color='orange')))
    if "Bollinger" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["BBL_20_2.0"], name="BB Lower", line=dict(color='gray', dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["BBU_20_2.0"], name="BB Upper", line=dict(color='gray', dash="dot")))

    fig.update_layout(
        title=f"{symbol} Chart",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=600
    )
    return fig

def check_alerts(df, symbol):
    alerts = []
    # MACD crossover
    if "MACD_12_26_9" in df and "MACDs_12_26_9" in df:
        macd = df["MACD_12_26_9"]
        signal = df["MACDs_12_26_9"]
        if macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]:
            msg = f"📈 MACD Bullish Crossover on {symbol}"
            send_telegram_alert(msg)
            alerts.append(msg)
        elif macd.iloc[-2] > signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]:
            msg = f"📉 MACD Bearish Crossover on {symbol}"
            send_telegram_alert(msg)
            alerts.append(msg)
    # RSI levels
    if "RSI" in df:
        rsi = df["RSI"].iloc[-1]
        if rsi > 70:
            msg = f"📊 {symbol} RSI is Overbought ({rsi:.2f})"
            send_telegram_alert(msg)
            alerts.append(msg)
        elif rsi < 30:
            msg = f"📉 {symbol} RSI is Oversold ({rsi:.2f})"
            send_telegram_alert(msg)
            alerts.append(msg)
    return alerts

# ----------- Streamlit UI -----------

st.set_page_config(layout="wide", page_title="TradingView Pro App")
st.title("📊 TradingView Pro - Streamlit Edition")

symbols = st.text_input("Enter symbols (comma-separated)", value="AAPL, BTC-USD").upper().split(",")
interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], index=3)
period = st.selectbox("Period", ["1d", "5d", "7d", "1mo"], index=2)
indicators = st.multiselect("Indicators", ["EMA", "SMA", "MACD", "RSI", "Bollinger"], default=["EMA", "MACD", "RSI"])
refresh = st.checkbox("Auto Refresh Every 2 Minutes")
chart_to_send = st.selectbox("Send chart via Telegram for:", symbols)

if st.button("🔄 Update Charts & Check Alerts"):
    for sym in symbols:
        df = get_data(sym.strip(), interval, period, indicators)
        if df is not None:
            st.subheader(f"{sym.strip()}")
            st.plotly_chart(plot_chart(df, sym, indicators), use_container_width=True)
            alerts = check_alerts(df, sym)
            for alert in alerts:
                st.success(alert)
        else:
            st.warning(f"⚠️ Data not found for {sym}")

if st.button("📤 Send Chart to Telegram"):
    send_telegram_alert(f"📸 Chart requested for {chart_to_send.strip()} (manual button)")
    st.success("Chart request sent to Telegram!")

# Auto-refresh loop
if refresh:
    st.experimental_rerun()
