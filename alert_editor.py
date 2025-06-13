def apply_alert_rules(symbol, df, rules):
    messages = []
    if symbol not in rules:
        return messages

    for rule in rules[symbol]:
        rule_type = rule["type"]

        if rule_type == "RSI":
            current_rsi = df["RSI"].iloc[-1]
            if rule["condition"] == ">" and current_rsi > rule["value"]:
                messages.append(rule["message"])
            elif rule["condition"] == "<" and current_rsi < rule["value"]:
                messages.append(rule["message"])

        elif rule_type == "MACD_CROSS":
            if "MACD_12_26_9" in df and "MACDs_12_26_9" in df:
                macd = df["MACD_12_26_9"]
                signal = df["MACDs_12_26_9"]
                if rule["direction"] == "bullish" and macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]:
                    messages.append(rule["message"])
                elif rule["direction"] == "bearish" and macd.iloc[-2] > signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]:
                    messages.append(rule["message"])

        elif rule_type == "EMA_CROSS":
            if "EMA20" in df and "EMA50" in df:
                ema_fast = df[f"EMA{rule['fast']}"]
                ema_slow = df[f"EMA{rule['slow']}"]
                if rule["direction"] == "bullish" and ema_fast.iloc[-2] < ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]:
                    messages.append(rule["message"])
                elif rule["direction"] == "bearish" and ema_fast.iloc[-2] > ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]:
                    messages.append(rule["message"])
    return messages
