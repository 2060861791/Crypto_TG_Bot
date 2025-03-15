"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
import logging
from config import *

logger = logging.getLogger(__name__)

def calculate_rsi(df, period=RSI_PERIOD):
    """计算RSI指标"""
    try:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        logger.error(f"计算RSI失败: {e}")
        return pd.Series(index=df.index)

def calculate_macd(df, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    """计算MACD指标"""
    try:
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    except Exception as e:
        logger.error(f"计算MACD失败: {e}")
        empty = pd.Series(index=df.index)
        return empty, empty, empty

def calculate_bollinger_bands(df, period=BOLLINGER_PERIOD, std_dev=BOLLINGER_STD):
    """计算布林带指标"""
    try:
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return sma, upper_band, lower_band
    except Exception as e:
        logger.error(f"计算布林带失败: {e}")
        empty = pd.Series(index=df.index)
        return empty, empty, empty

def calculate_ema(df, period):
    """计算EMA指标"""
    try:
        return df['close'].ewm(span=period, adjust=False).mean()
    except Exception as e:
        logger.error(f"计算EMA失败: {e}")
        return pd.Series(index=df.index)

def calculate_atr(df, period=ATR_PERIOD):
    """计算ATR指标"""
    try:
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=period).mean()
        return atr
    except Exception as e:
        logger.error(f"计算ATR失败: {e}")
        return pd.Series(index=df.index)

def get_market_type(df):
    """确定市场类型（趋势、震荡等）"""
    try:
        # 价格变化百分比
        price_change = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        
        # 波动率 (标准差)
        volatility = df['close'].pct_change().std() * 100
        
        # EMA指标判断趋势
        ema_short = calculate_ema(df, EMA_SHORT)
        ema_long = calculate_ema(df, EMA_LONG)
        
        # 趋势判断
        if ema_short.iloc[-1] > ema_long.iloc[-1] and price_change > 5:
            if volatility > 5:
                return "强上升趋势-高波动"
            else:
                return "强上升趋势"
        elif ema_short.iloc[-1] < ema_long.iloc[-1] and price_change < -5:
            if volatility > 5:
                return "强下降趋势-高波动"
            else:
                return "强下降趋势"
        elif abs(price_change) < 2 and volatility > 3:
            return "震荡市场-高波动"
        elif abs(price_change) < 2:
            return "震荡市场"
        elif ema_short.iloc[-1] > ema_long.iloc[-1]:
            return "弱上升趋势"
        elif ema_short.iloc[-1] < ema_long.iloc[-1]:
            return "弱下降趋势"
        else:
            return "不确定"
            
    except Exception as e:
        logger.error(f"分析市场类型失败: {e}")
        return "分析失败" 