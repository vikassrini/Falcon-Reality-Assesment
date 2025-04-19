
# strategy_module.py
import pandas as pd

def is_trending(window):
    highs = window['high'].values
    lows = window['low'].values
    hh_hl = all(highs[i] > highs[i - 1] and lows[i] > lows[i - 1] for i in range(1, len(highs)))
    ll_lh = all(highs[i] < highs[i - 1] and lows[i] < lows[i - 1] for i in range(1, len(highs)))
    return hh_hl or ll_lh

def is_strong_impulse(df, index, min_pct=0.015):
    if index < 2:
        return False
    window = df.iloc[index-2:index+1]
    move = abs(window['close'].iloc[-1] - window['open'].iloc[0]) / window['open'].iloc[0]
    bodies = abs(window['close'] - window['open'])
    body_ratio = bodies.sum() / (window['high'] - window['low']).sum()
    return move >= min_pct and body_ratio >= 0.6

def detect_and_extend_ranges(df, min_window=15, min_range_pct=0.015, max_range_pct=0.03, min_touches=2):
    extended_ranges, entries, i = [], [], 0

    while i <= len(df) - min_window:
        window = df.iloc[i:i + min_window]
        if is_trending(window):
            i += 1
            continue

        range_high, range_low = window['high'].max(), window['low'].min()
        range_width_pct = (range_high - range_low) / range_low

        if not (min_range_pct <= range_width_pct <= max_range_pct):
            i += 1
            continue

        top_touches = (abs(window['high'] - range_high) <= 0.01 * range_high).sum()
        bottom_touches = (abs(window['low'] - range_low) <= 0.01 * range_low).sum()

        if top_touches < min_touches or bottom_touches < min_touches:
            i += 1
            continue

        end = i + min_window
        while end < len(df) and not ((df.iloc[end]['close'] > range_high) or (df.iloc[end]['close'] < range_low)):
            end += 1

        mid_low = range_low + 0.35 * (range_high - range_low)
        mid_high = range_high - 0.35 * (range_high - range_low)

        recent_candle = df.iloc[end - 1]
        if recent_candle['low'] <= range_low + 0.01 * range_low and recent_candle['low'] <= mid_low:
            entries.append({
                'entry_time': recent_candle['timestamp'], 'type': 'long', 'entry_price': range_low,
                'stop_loss': window['low'].min() * 0.995, 'tp1': (range_high + range_low)/2, 'tp2': range_high
            })

        if recent_candle['high'] >= range_high - 0.01 * range_high and recent_candle['high'] >= mid_high:
            entries.append({
                'entry_time': recent_candle['timestamp'], 'type': 'short', 'entry_price': range_high,
                'stop_loss': window['high'].max() * 1.005, 'tp1': (range_high + range_low)/2, 'tp2': range_low
            })

        i = end

    return pd.DataFrame(entries)

def detect_bos(df, lookback=5):
    signals = []
    for i in range(lookback, len(df)):
        if df.iloc[i]['high'] > df.iloc[i - lookback:i]['high'].max():
            signals.append({'index': i, 'type': 'bullish'})
        elif df.iloc[i]['low'] < df.iloc[i - lookback:i]['low'].min():
            signals.append({'index': i, 'type': 'bearish'})
    return signals

def detect_in_price_entries(df):
    bos_signals, entries = detect_bos(df), []
    for signal in bos_signals:
        i, direction = signal['index'], signal['type']
        ob_zone = (df.iloc[i-1]['low'], df.iloc[i-1]['high'])
        for j in range(i+1, min(i+4, len(df))):
            row = df.iloc[j]
            entry_price = row['low'] if direction == 'bullish' else row['high']
            stop_loss = ob_zone[0] if direction == 'bullish' else ob_zone[1]
            tp_level = entry_price + 3 * (entry_price - stop_loss) if direction == 'bullish' else entry_price - 3 * (stop_loss - entry_price)

            rr = abs(tp_level - entry_price) / abs(entry_price - stop_loss)
            if rr < 3:
                continue

            entries.append({
                'entry_time': row['timestamp'], 'type': direction, 'entry_price': entry_price,
                'stop_loss': stop_loss, 'tp_level': tp_level
            })
            break
    return pd.DataFrame(entries)
