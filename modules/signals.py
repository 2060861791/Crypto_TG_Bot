"""
信号生成与处理模块
"""
import pandas as pd
import numpy as np
import logging
import time
import schedule
import functools
from datetime import datetime, timedelta
from modules.api import get_klines
from modules.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_ema, calculate_atr, get_market_type
)
from modules.risk import (
    calculate_stop_loss, calculate_take_profit, 
    calculate_position_size, evaluate_risk_level
)
from modules.utils import load_user_symbols
from modules.bot import bot, handle_error
from config import *

logger = logging.getLogger(__name__)

# 缓存装饰器
def cache_result(seconds=300):
    """缓存函数结果的装饰器"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = datetime.now()
            
            # 检查缓存是否存在且未过期
            if key in cache and (current_time - cache[key]['time']).total_seconds() < seconds:
                return cache[key]['result']
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = {'result': result, 'time': current_time}
            return result
        return wrapper
    return decorator

@cache_result(seconds=300)
def calculate_probability(symbol):
    """
    计算上涨/下跌概率
    """
    try:
        # 获取不同时间周期的K线数据
        df_1h = get_klines(symbol, interval="1h", limit=100)
        df_4h = get_klines(symbol, interval="4h", limit=50)
        df_1d = get_klines(symbol, interval="1d", limit=30)
        
        if df_1h is None or df_4h is None or df_1d is None:
            logger.error(f"获取 {symbol} K线数据失败")
            return None
            
        # 计算各种指标
        # 1. RSI指标
        rsi_1h = calculate_rsi(df_1h)
        rsi_4h = calculate_rsi(df_4h)
        rsi_1d = calculate_rsi(df_1d)
        
        # 2. MACD指标
        macd_line, signal_line, histogram = calculate_macd(df_1h)
        
        # 3. 布林带指标
        middle_band, upper_band, lower_band = calculate_bollinger_bands(df_1h)
        
        # 4. 趋势指标 (EMA)
        ema_short = calculate_ema(df_1h, EMA_SHORT)
        ema_long = calculate_ema(df_1h, EMA_LONG)
        
        # 5. 波动率指标 (ATR)
        atr = calculate_atr(df_1h)
        
        # 获取最新价格
        price = df_1h['close'].iloc[-1]
        
        # 判断价格在布林带中的位置 (0-1之间，0表示在下轨，1表示在上轨)
        bb_range = upper_band.iloc[-1] - lower_band.iloc[-1]
        if bb_range > 0:
            price_position_bb = (price - lower_band.iloc[-1]) / bb_range
        else:
            price_position_bb = 0.5
            
        # 获取市场类型
        market_type = get_market_type(df_1h)
        
        # 计算RSI指标信号概率 (RSI高于70超买，低于30超卖)
        rsi_1h_value = rsi_1h.iloc[-1] if not pd.isna(rsi_1h.iloc[-1]) else 50
        rsi_4h_value = rsi_4h.iloc[-1] if not pd.isna(rsi_4h.iloc[-1]) else 50
        rsi_1d_value = rsi_1d.iloc[-1] if not pd.isna(rsi_1d.iloc[-1]) else 50
        
        # 不同时间周期RSI的加权平均
        rsi_composite = (rsi_1h_value * 0.5 + rsi_4h_value * 0.3 + rsi_1d_value * 0.2)
        
        # RSI概率计算
        if rsi_composite >= RSI_OVERBOUGHT:
            rsi_probability = max(0, 100 - (rsi_composite - RSI_OVERBOUGHT) * 5)
        elif rsi_composite <= RSI_OVERSOLD:
            rsi_probability = min(100, 50 + (RSI_OVERSOLD - rsi_composite) * 5)
        else:
            # RSI在30-70之间，接近70看跌，接近30看涨
            rsi_range = RSI_OVERBOUGHT - RSI_OVERSOLD
            rsi_norm = (rsi_composite - RSI_OVERSOLD) / rsi_range
            rsi_probability = 100 - (rsi_norm * 100)
        
        # MACD信号概率
        if not pd.isna(histogram.iloc[-1]):
            if histogram.iloc[-1] > 0:
                macd_probability = 70 + min(29, abs(histogram.iloc[-1]) * 100)
            else:
                macd_probability = 30 - min(29, abs(histogram.iloc[-1]) * 100)
        else:
            macd_probability = 50
        
        # 布林带信号概率
        if not pd.isna(price_position_bb):
            if price_position_bb > 0.8:  # 接近上轨
                bb_probability = 30 - (price_position_bb - 0.8) * 150
            elif price_position_bb < 0.2:  # 接近下轨
                bb_probability = 70 + (0.2 - price_position_bb) * 150
            else:
                # 在布林带中间区域
                bb_probability = 50 + (0.5 - price_position_bb) * 40
        else:
            bb_probability = 50
        
        # 趋势信号概率
        if not pd.isna(ema_short.iloc[-1]) and not pd.isna(ema_long.iloc[-1]):
            ema_diff = (ema_short.iloc[-1] - ema_long.iloc[-1]) / ema_long.iloc[-1] * 100
            if ema_diff > 1:  # 强上升趋势
                trend_probability = 80 + min(19, ema_diff * 2)
            elif ema_diff < -1:  # 强下降趋势
                trend_probability = 20 - min(19, abs(ema_diff) * 2)
            else:  # 弱趋势
                trend_probability = 50 + (ema_diff * 30)
        else:
            trend_probability = 50
        
        # 波动率影响 (ATR相对值)
        atr_value = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
        atr_percent = atr_value / price * 100  # ATR占价格百分比
        
        # 综合计算上涨概率 (加权平均)
        # 使用单独权重而非INDICATOR_WEIGHTS字典
        up_probability = (
            rsi_probability * RSI_WEIGHT +
            macd_probability * MACD_WEIGHT +
            bb_probability * BOLLINGER_WEIGHT +
            trend_probability * EMA_WEIGHT
        )
        
        # 计算信号强度 (概率距离中点50的距离)
        signal_strength = abs(up_probability - 50) * 2  # 0-100
        
        # 信号强度文本描述
        if signal_strength > 80:
            signal_strength_text = "极强"
        elif signal_strength > 60:
            signal_strength_text = "较强"
        elif signal_strength > 40:
            signal_strength_text = "中等"
        elif signal_strength > 20:
            signal_strength_text = "较弱"
        else:
            signal_strength_text = "微弱"
        
        # 根据概率确定方向
        if up_probability > 60:
            direction = "buy"
        elif up_probability < 40:
            direction = "sell"
        else:
            direction = "neutral"
        
        # 短期建议
        if up_probability > STRONG_SIGNAL_THRESHOLD:
            short_term_rec = f"强烈看涨 ({signal_strength_text})"
        elif up_probability > 60:
            short_term_rec = f"看涨 ({signal_strength_text})"
        elif up_probability < (100 - STRONG_SIGNAL_THRESHOLD):
            short_term_rec = f"强烈看跌 ({signal_strength_text})"
        elif up_probability < 40:
            short_term_rec = f"看跌 ({signal_strength_text})"
        else:
            short_term_rec = f"震荡/观望 ({signal_strength_text})"
        
        # 长期建议基于日线RSI和趋势
        if rsi_1d_value < 40 and "上升" in market_type:
            long_term_rec = "看涨 (超跌+上升趋势)"
        elif rsi_1d_value > 60 and "下降" in market_type:
            long_term_rec = "看跌 (超买+下降趋势)"
        elif "强上升" in market_type:
            long_term_rec = "看涨 (强上升趋势)"
        elif "强下降" in market_type:
            long_term_rec = "看跌 (强下降趋势)"
        elif rsi_1d_value < 30:
            long_term_rec = "看涨 (长期超跌)"
        elif rsi_1d_value > 70:
            long_term_rec = "看跌 (长期超买)"
        else:
            long_term_rec = "中性 (无明显趋势)"
        
        # 风险收益比计算
        if direction == "buy":
            potential_reward = (upper_band.iloc[-1] - price) / price * 100
            potential_risk = (price - lower_band.iloc[-1]) / price * 100
        else:
            potential_reward = (price - lower_band.iloc[-1]) / price * 100
            potential_risk = (upper_band.iloc[-1] - price) / price * 100
        
        if potential_risk > 0:
            rr_ratio = potential_reward / potential_risk
        else:
            rr_ratio = 1.0
        
        # 风险收益比评级
        if rr_ratio > 3:
            rr_rating = "极佳"
        elif rr_ratio > 2:
            rr_rating = "优秀"
        elif rr_ratio > 1:
            rr_rating = "良好"
        else:
            rr_rating = "一般"
            
        rr_info = {
            "ratio": rr_ratio,
            "rating": rr_rating,
            "reward": potential_reward,
            "risk": potential_risk
        }
        
        # 添加风险管理参数
        risk_level, risk_description = evaluate_risk_level(
            up_probability, 
            market_type, 
            rr_info["ratio"] if rr_info else 0
        )
        
        # 计算止损位
        stop_loss = calculate_stop_loss(
            df_1h, 
            "buy" if up_probability > 50 else "sell", 
            "atr"
        )
        
        # 计算止盈位
        take_profit = calculate_take_profit(
            df_1h, 
            "buy" if up_probability > 50 else "sell", 
            risk_level
        )
        
        # 计算建议仓位
        position_size = calculate_position_size(df_1h, risk_level)
        position_text = f"{int(position_size * 100)}%"
        
        # 将所有数据合并到一个字典中
        result = {
            "symbol": symbol,
            "price": price,
            "up_probability": up_probability,
            "down_probability": 100 - up_probability,
            "signal_strength": signal_strength,
            "signal_strength_text": signal_strength_text,
            "direction": direction,
            "market_type": market_type,
            "rsi_1h": rsi_1h_value,
            "rsi_4h": rsi_4h_value,
            "rsi_1d": rsi_1d_value,
            "macd_histogram": histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0,
            "price_position_bb": price_position_bb,
            "atr": atr_value,
            "rr_info": rr_info,
            "short_term_rec": short_term_rec,
            "long_term_rec": long_term_rec,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size,
            "position_text": position_text
        }
        
        return result
    except Exception as e:
        logger.error(f"分析 {symbol} 失败: {e}")
        return None

# 监控所有交易对
def monitor_symbols():
    """监控所有配置的交易对，计算信号并处理变化"""
    try:
        # 从配置或数据库加载监控的交易对
        symbols = load_user_symbols()
        
        results = []
        critical_signals = []
        
        for symbol in symbols:
            try:
                # 计算信号
                prob_data = calculate_probability(symbol)
                
                if prob_data:
                    results.append(prob_data)
                    
                    # 判断是否是关键信号
                    if prob_data['signal_strength'] in ["强烈看涨", "强烈看跌"]:
                        critical_signals.append(prob_data)
                        
            except Exception as e:
                logger.error(f"处理 {symbol} 时出错: {e}")
                
        # 发送关键信号提醒
        if critical_signals:
            send_critical_signals(critical_signals)
            
        return results
    
    except Exception as e:
        handle_error(e, "监控交易对")
        return []

# 发送关键信号提醒
def send_critical_signals(signals):
    """发送关键信号提醒"""
    try:
        message = "🚨 关键信号提醒!\n\n"
        
        for signal in signals:
            direction_arrow = "↗️" if signal['up_probability'] > 50 else "↘️"
            risk_icon = "🟢" if signal.get('risk_level') == "low" else "🟡" if signal.get('risk_level') == "medium" else "🔴"
            
            # 计算止损百分比
            stop_loss_percent = abs((signal['stop_loss'] - signal['price']) / signal['price'] * 100)
            
            # 计算目标百分比
            target_percent = abs((signal['take_profit'] - signal['price']) / signal['price'] * 100)
            
            message += (
                f"💎 {signal['symbol']} {direction_arrow}\n"
                f"└ 价格: ${signal['price']:.2f}\n"
                f"└ 信号: {signal['signal_strength']}\n"
                f"└ 概率: ↑{signal['up_probability']:.1f}% | ↓{signal['down_probability']:.1f}%\n"
                f"└ 市场: {signal.get('market_type', 'N/A')}\n"
                f"└ 风险: {risk_icon} {signal.get('risk_description', 'N/A')}\n"
                f"└ 建议仓位: {signal.get('position_text', 'N/A')}\n"
                f"└ 止损: ${signal.get('stop_loss', 0):.2f} ({stop_loss_percent:.1f}%)\n"
                f"└ 目标: ${signal.get('take_profit', 0):.2f} ({target_percent:.1f}%)\n\n"
            )
            
        bot.send_message(CHAT_ID, message)
    
    except Exception as e:
        handle_error(e, "发送关键信号")

# 发送市场概况
def send_market_overview():
    """发送市场概况消息"""
    try:
        results = monitor_symbols()
        
        if not results:
            bot.send_message(CHAT_ID, "❌ 无法获取市场数据，请稍后再试")
            return
            
        # 添加当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📊 市场概况 ({current_time})\n\n"
        
        # 按上涨概率排序
        results.sort(key=lambda x: x['up_probability'], reverse=True)
        
        for result in results:
            direction_arrow = "↗️" if result['up_probability'] > 50 else "↘️"
            risk_icon = "🟢" if result.get('risk_level') == "low" else "🟡" if result.get('risk_level') == "medium" else "🔴"
            
            # 计算止损百分比
            stop_loss_percent = abs((result['stop_loss'] - result['price']) / result['price'] * 100)
            
            # 计算目标百分比
            target_percent = abs((result['take_profit'] - result['price']) / result['price'] * 100)
            
            message += (
                f"💎 {result['symbol']} {direction_arrow}\n"
                f"└ 价格: ${result['price']:.2f}\n"
                f"└ 概率: ↑{result['up_probability']:.1f}% | ↓{result['down_probability']:.1f}%\n"
                f"└ 市场: {result.get('market_type', 'N/A')}\n"
                f"└ 风险: {risk_icon} {result.get('risk_description', 'N/A')}\n"
                f"└ 建议仓位: {result.get('position_text', 'N/A')}\n"
                f"└ 止损: ${result.get('stop_loss', 0):.2f} ({stop_loss_percent:.1f}%)\n"
                f"└ 目标: ${result.get('take_profit', 0):.2f} ({target_percent:.1f}%)\n\n"
            )
            
        # 如果消息太长，拆分发送
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                bot.send_message(CHAT_ID, part)
        else:
            bot.send_message(CHAT_ID, message)
    
    except Exception as e:
        handle_error(e, "发送市场概况")

# 发送心跳消息
def send_heartbeat():
    """发送心跳消息，确认机器人正常运行"""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"💓 机器人正常运行中\n时间: {now}"
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        handle_error(e, "发送心跳")

# 定时任务运行函数
def run_schedule():
    """运行所有定时任务"""
    # 设置定时任务
    schedule.every(MONITOR_INTERVAL).minutes.do(send_market_overview)
    schedule.every(HEARTBEAT_INTERVAL).minutes.do(send_heartbeat)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            error_message = f"❌ 定时任务出错: {str(e)}"
            logger.error(error_message)
            try:
                bot.send_message(CHAT_ID, error_message)
            except:
                pass
            time.sleep(60) 