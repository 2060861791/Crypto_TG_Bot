import pandas as pd
import numpy as np
import logging
from config import *

logger = logging.getLogger(__name__)

def calculate_stop_loss(df, side="buy", method="atr"):
    """
    计算建议止损位
    
    参数:
    - df: 包含价格数据的DataFrame
    - side: 交易方向 ("buy" 或 "sell")
    - method: 止损计算方法 ("atr", "bollinger", "swing")
    
    返回:
    - 止损价格
    """
    try:
        current_price = df['close'].iloc[-1]
        
        if method == "atr":
            # 使用ATR计算止损
            high_low = df["high"] - df["low"]
            high_close = abs(df["high"] - df["close"].shift())
            low_close = abs(df["low"] - df["close"].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=ATR_PERIOD).mean().iloc[-1]
            
            # ATR倍数根据市场波动率动态调整
            volatility = df['close'].pct_change().std() * 100
            atr_multiplier = 1.0
            
            if volatility > 5:  # 高波动率
                atr_multiplier = 2.0
            elif volatility > 3:  # 中波动率
                atr_multiplier = 1.5
                
            if side == "buy":
                stop_loss = current_price - (atr * atr_multiplier)
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                
        elif method == "bollinger":
            # 使用布林带计算止损
            window = BOLLINGER_PERIOD
            std = df['close'].rolling(window=window).std()
            sma = df['close'].rolling(window=window).mean()
            lower_band = sma - (std * BOLLINGER_STD)
            upper_band = sma + (std * BOLLINGER_STD)
            
            if side == "buy":
                stop_loss = lower_band.iloc[-1]
            else:
                stop_loss = upper_band.iloc[-1]
                
        elif method == "swing":
            # 使用近期波动区间的低点/高点
            periods = 20  # 看过去20个周期
            
            if side == "buy":
                recent_lows = df['low'].iloc[-periods:].nsmallest(3)
                stop_loss = recent_lows.mean() * 0.99  # 给予一点缓冲
            else:
                recent_highs = df['high'].iloc[-periods:].nlargest(3)
                stop_loss = recent_highs.mean() * 1.01  # 给予一点缓冲
        
        # 确保止损合理（不会太远或太近）
        max_stop_percent = 0.10  # 最大止损比例10%
        min_stop_percent = 0.005  # 最小止损比例0.5%
        
        if side == "buy":
            max_stop = current_price * (1 - max_stop_percent)
            min_stop = current_price * (1 - min_stop_percent)
            
            if stop_loss < max_stop:
                stop_loss = max_stop
            elif stop_loss > min_stop:
                stop_loss = min_stop
        else:
            max_stop = current_price * (1 + max_stop_percent)
            min_stop = current_price * (1 + min_stop_percent)
            
            if stop_loss > max_stop:
                stop_loss = max_stop
            elif stop_loss < min_stop:
                stop_loss = min_stop
                
        return stop_loss
        
    except Exception as e:
        logger.error(f"计算止损失败: {e}")
        # 返回默认止损（2%）
        if side == "buy":
            return current_price * 0.98
        else:
            return current_price * 1.02

def calculate_take_profit(df, side="buy", risk_level="medium"):
    """
    计算建议止盈位，使用斐波那契扩展位
    
    参数:
    - df: 包含价格数据的DataFrame
    - side: 交易方向 ("buy" 或 "sell")
    - risk_level: 风险等级 ("low", "medium", "high")
    
    返回:
    - 止盈价格
    """
    try:
        current_price = df['close'].iloc[-1]
        
        # 计算近期高低点
        periods = 30  # 过去30个周期
        recent_high = df['high'].iloc[-periods:].max()
        recent_low = df['low'].iloc[-periods:].min()
        price_range = recent_high - recent_low
        
        # 根据风险等级设置斐波那契扩展位
        if risk_level == "low":
            fib_level = 1.618  # 保守目标
        elif risk_level == "medium":
            fib_level = 2.618  # 标准目标
        else:
            fib_level = 3.618  # 激进目标
            
        # 计算斐波那契扩展位
        if side == "buy":
            # 从低点到高点的扩展
            take_profit = recent_low + (price_range * fib_level)
            
            # 确保目标价不会太离谱
            max_tp_percent = 0.50  # 最大50%上涨
            if take_profit > current_price * (1 + max_tp_percent):
                take_profit = current_price * (1 + max_tp_percent)
        else:
            # 从高点到低点的扩展
            take_profit = recent_high - (price_range * fib_level)
            
            # 确保目标价不会太离谱
            max_tp_percent = 0.50  # 最大50%下跌
            if take_profit < current_price * (1 - max_tp_percent):
                take_profit = current_price * (1 - max_tp_percent)
                
        return take_profit
        
    except Exception as e:
        logger.error(f"计算止盈失败: {e}")
        # 返回默认止盈（5%）
        if side == "buy":
            return current_price * 1.05
        else:
            return current_price * 0.95

def calculate_position_size(df, risk_level="medium"):
    """
    计算建议仓位大小
    
    参数:
    - df: 包含价格数据的DataFrame
    - risk_level: 风险等级 ("low", "medium", "high")
    
    返回:
    - 建议仓位比例(0-1之间)
    """
    try:
        # 计算价格波动率 (过去20天标准差)
        volatility = df['close'].pct_change().rolling(window=20).std().iloc[-1] * 100
        
        # 基础仓位大小
        if risk_level == "low":
            base_position = 0.3  # 保守仓位30%
        elif risk_level == "medium":
            base_position = 0.5  # 标准仓位50%
        else:
            base_position = 0.1  # 高风险情况下轻仓10%
            
        # 根据波动率调整
        if volatility > 5:  # 高波动
            vol_factor = 0.5  # 减半
        elif volatility > 3:  # 中等波动
            vol_factor = 0.7  # 减少30%
        else:  # 低波动
            vol_factor = 1.0  # 不变
            
        position_size = base_position * vol_factor
        
        # 确保仓位在合理范围
        position_size = max(0.05, min(position_size, 1.0))
        
        return position_size
        
    except Exception as e:
        logger.error(f"计算仓位失败: {e}")
        return 0.1  # 出错时返回10%的保守仓位

def evaluate_risk_level(probability, market_type, rr_ratio):
    """
    评估风险等级
    
    参数:
    - probability: 上涨概率(0-100)
    - market_type: 市场类型
    - rr_ratio: 风险收益比
    
    返回:
    - 风险等级 ("low", "medium", "high")
    - 风险评级说明
    """
    try:
        # 初始风险分数(0-100)
        risk_score = 0
        
        # 基于概率评分 (0-50分)
        # 概率越接近50%，风险越高；越接近0%或100%，风险越低
        probability_risk = 50 - abs(probability - 50)
        risk_score += probability_risk
        
        # 基于市场类型评分 (0-30分)
        market_risk = 15  # 默认中等风险
        
        if "强上升趋势" in market_type:
            market_risk = 5  # 低风险
        elif "强下降趋势" in market_type:
            market_risk = 5  # 低风险
        elif "震荡" in market_type:
            market_risk = 25  # 高风险
            
        risk_score += market_risk
        
        # 基于风险收益比评分 (0-20分)
        rr_risk = 20  # 默认高风险
        
        if rr_ratio >= 3:
            rr_risk = 5  # 低风险
        elif rr_ratio >= 2:
            rr_risk = 10  # 中等风险
            
        risk_score += rr_risk
        
        # 确定风险等级
        if risk_score < 40:
            risk_level = "low"
            risk_description = "低风险-适合标准仓位"
        elif risk_score < 70:
            risk_level = "medium"
            risk_description = "中等风险-建议适中仓位"
        else:
            risk_level = "high"
            risk_description = "高风险-建议轻仓或观望"
            
        return risk_level, risk_description
        
    except Exception as e:
        logger.error(f"评估风险等级失败: {e}")
        return "high", "评估失败-建议保守操作"  # 出错时返回高风险 