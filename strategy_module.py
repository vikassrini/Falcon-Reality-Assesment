import pandas as pd


def is_trending(window):
    highs = window['high'].values
    lows = window['low'].values
    hh_hl = all(highs[i] > highs[i - 1] and lows[i] > lows[i - 1] for i in range(1, len(highs)))
    ll_lh = all(highs[i] < highs[i - 1] and lows[i] < lows[i - 1] for i in range(1, len(highs)))
    return hh_hl or ll_lh


def detect_and_extend_ranges(df, min_window=15, min_range_pct=0.015, max_range_pct=0.03,
                              touch_tolerance_ratio=0.01, min_touches=2):
    extended_ranges = []
    entries = []
    i = 0

    while i <= len(df) - min_window:
        window = df.iloc[i:i + min_window]
        if is_trending(window):
            i += 1
            continue

        range_high = window['high'].max()
        range_low = window['low'].min()
        range_width_pct = (range_high - range_low) / range_low

        if not (min_range_pct <= range_width_pct <= max_range_pct):
            i += 1
            continue

        top_tolerance = 0.01 * range_high
        bottom_tolerance = 0.01 * range_low
        top_touches = (abs(window['high'] - range_high) <= top_tolerance).sum()
        bottom_touches = (abs(window['low'] - range_low) <= bottom_tolerance).sum()

        if top_touches < min_touches or bottom_touches < min_touches:
            i += 1
            continue

        end = i + min_window
        while end < len(df):
            extended_window = df.iloc[i:end + 1]
            if (extended_window['close'] > range_high).any() or (extended_window['close'] < range_low).any():
                break
            end += 1

        start_time = df.iloc[i]['timestamp']
        end_time = df.iloc[end - 1]['timestamp']
        range_mid = round((range_high + range_low) / 2, 2)

        extended_ranges.append({
            'start_time': start_time,
            'end_time': end_time,
            'range_high': range_high,
            'range_low': range_low,
            'range_mid': range_mid,
            'range_width_%': round(range_width_pct * 100, 2),
            'duration_candles': end - i,
            'top_touches': top_touches,
            'bottom_touches': bottom_touches
        })

        recent_candle = df.iloc[end - 1]
        if abs(recent_candle['low'] - range_low) <= bottom_tolerance:
            entries.append({
                'entry_time': recent_candle['timestamp'],
                'type': 'long',
                'entry_price': range_low,
                'stop_loss': range_low - 0.001 * range_low,
                'tp1': range_mid,
                'tp2': range_high
            })

        if abs(recent_candle['high'] - range_high) <= top_tolerance:
            entries.append({
                'entry_time': recent_candle['timestamp'],
                'type': 'short',
                'entry_price': range_high,
                'stop_loss': range_high + 0.001 * range_high,
                'tp1': range_mid,
                'tp2': range_low
            })

        i = end

    return pd.DataFrame(extended_ranges), pd.DataFrame(entries)


def is_wick_cluster(df, index, direction):
    wick_values = []
    for i in range(index - 5, index + 1):
        if i < 0 or i >= len(df):
            continue
        row = df.iloc[i]
        wick = row['high'] - max(row['open'], row['close']) if direction == 'bearish' else min(row['open'], row['close']) - row['low']
        wick_values.append(wick)

    for i in range(len(wick_values)):
        group = [w for w in wick_values if abs(w - wick_values[i]) / (df.iloc[index]['close']) <= 0.0025]
        if len(group) >= 3:
            return True
    return False


def is_candle_base(df, index):
    base = df.iloc[index - 4:index]
    if len(base) < 2:
        return False
    opens = base['open']
    closes = base['close']
    ref = closes.iloc[-1]
    tolerance = 0.01 * ref
    overlap = all(abs(o - ref) <= tolerance and abs(c - ref) <= tolerance for o, c in zip(opens, closes))
    return overlap


def detect_bos(df, lookback=5):
    bos_signals = []
    for i in range(lookback, len(df)):
        prev_high = df.iloc[i - lookback:i]['high'].max()
        prev_low = df.iloc[i - lookback:i]['low'].min()
        if df.iloc[i]['high'] > prev_high:
            bos_signals.append({'index': i, 'type': 'bullish'})
        elif df.iloc[i]['low'] < prev_low:
            bos_signals.append({'index': i, 'type': 'bearish'})
    return bos_signals


def detect_orderblock(df, index, direction):
    search_range = range(index - 1, max(index - 6, 0), -1)
    for i in search_range:
        row = df.iloc[i]
        if direction == 'bullish' and row['close'] < row['open']:
            return row
        elif direction == 'bearish' and row['close'] > row['open']:
            return row
    return None


def detect_in_price_entries(df):
    bos_signals = detect_bos(df)
    entries = []

    for signal in bos_signals:
        i = signal['index']
        direction = signal['type']
        zone_check_window = df.iloc[i+1:i+10]
        if zone_check_window.empty:
            continue
        valid_zone_detected = False
        ob_zone = None

        ob_candle = detect_orderblock(df, i, direction)
        if ob_candle is not None:
            ob_zone = (min(ob_candle['open'], ob_candle['close']), max(ob_candle['open'], ob_candle['close']))
            valid_zone_detected = True
        elif is_wick_cluster(df, i, direction):
            ob_zone = (df.iloc[i]['low'], df.iloc[i]['high'])
            valid_zone_detected = True
        elif is_candle_base(df, i):
            base_candles = df.iloc[i - 4:i]
            ob_zone = (base_candles['low'].min(), base_candles['high'].max())
            valid_zone_detected = True

        if not valid_zone_detected:
            continue

        for j in range(zone_check_window.index[0], zone_check_window.index[-1] + 1):
            if j >= len(df):
                break
            row = df.iloc[j]
            if direction == 'bullish' and ob_zone[0] <= row['low'] <= ob_zone[1]:
                entries.append({
                    'entry_time': row['timestamp'],
                    'type': 'bullish',
                    'entry_basis': 'OB/Wick/Base',
                    'entry_price': row['low'],
                    'stop_loss': ob_zone[0],
                    'tp_level': df.iloc[i]['high'] + (df.iloc[i]['high'] - ob_zone[0]) * 3
                })
                break
            elif direction == 'bearish' and ob_zone[0] <= row['high'] <= ob_zone[1]:
                entries.append({
                    'entry_time': row['timestamp'],
                    'type': 'bearish',
                    'entry_basis': 'OB/Wick/Base',
                    'entry_price': row['high'],
                    'stop_loss': ob_zone[1],
                    'tp_level': df.iloc[i]['low'] - (ob_zone[1] - df.iloc[i]['low']) * 3
                })
                break

    return pd.DataFrame(entries)
