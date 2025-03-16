"""
Telegram机器人命令处理模块
"""
import logging
from telebot import types
from modules.bot import bot, is_authorized
from modules.signals import calculate_probability, monitor_symbols, send_market_overview
from modules.utils import load_user_symbols, save_user_symbols
from modules.api import get_klines
from config import *
from datetime import datetime

logger = logging.getLogger(__name__)

# 帮助命令
@bot.message_handler(commands=['h', 'help'])
def help_command(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
    
    help_text = (
        "🤖 <b>交易信号监控机器人 - 帮助信息</b>\n\n"
        "<b>可用命令:</b>\n\n"
        "📊 <b>/m</b> 或 <b>/market</b>\n- 查看当前市场分析\n\n"
        "➕ <b>/add BTC</b>\n- 添加交易对到监控列表\n\n"
        "➖ <b>/remove DOGE</b>\n- 从监控列表中移除交易对\n\n"
        "📋 <b>/list</b>\n- 显示当前监控的交易对列表\n\n"
        "🔍 <b>/risk ETH</b>\n- 查看特定交易对的详细风险分析\n\n"
        "🆔 <b>/myid</b>\n- 获取你的用户ID\n\n"
        "✅ <b>/test</b>\n- 测试机器人是否正常响应\n\n"
        "❓ <b>/help</b> 或 <b>/h</b>\n- 显示此帮助信息"
    )
    
    bot.reply_to(message, help_text, parse_mode="HTML")

# 获取用户ID
@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.reply_to(message, f"🆔 你的用户ID是: {message.from_user.id}")

# 市场分析命令
@bot.message_handler(commands=['m', 'market'])
def market_command(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
    
    bot.reply_to(message, "📊 正在获取市场数据，请稍等...")
    send_market_overview()

# 添加新命令处理函数 (添加监控币种)
@bot.message_handler(commands=['add'])
def add_symbol(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ 请指定要添加的币种，例如: /add BTC")
        return
        
    # 获取币名并转换为大写
    coin = args[1].upper()
    
    # 如果已经包含USDT，使用原样，否则添加USDT后缀
    if 'USDT' in coin:
        symbol = coin
    else:
        symbol = f"{coin}USDT"
    
    # 验证交易对是否存在
    try:
        # 尝试获取K线数据，验证交易对是否存在
        test_data = get_klines(symbol, interval="1h", limit=1)
        if test_data is None or test_data.empty:
            bot.reply_to(message, f"❌ 交易对 {symbol} 不存在或无法获取数据")
            return
            
        # 加载当前监控列表
        current_symbols = load_user_symbols()
        
        # 检查是否已存在
        if symbol in current_symbols:
            bot.reply_to(message, f"ℹ️ {symbol} 已在监控列表中")
            return
            
        # 添加到列表
        current_symbols.append(symbol)
        
        # 保存更新后的列表
        if save_user_symbols(current_symbols):
            bot.reply_to(message, f"✅ 已添加 {symbol} 到监控列表")
        else:
            bot.reply_to(message, f"❌ 保存监控列表失败，请稍后再试")
            
    except Exception as e:
        logger.error(f"添加监控币种失败 - {symbol}: {e}")
        bot.reply_to(message, f"❌ 添加失败: {str(e)}")

# 添加新命令处理函数 (移除监控币种)
@bot.message_handler(commands=['remove'])
def remove_symbol(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ 请指定要移除的币种，例如: /remove BTC")
        return
    
    # 获取币名并转换为大写
    coin = args[1].upper()
    
    # 如果已经包含USDT，使用原样，否则添加USDT后缀
    if 'USDT' in coin:
        symbol = coin
    else:
        symbol = f"{coin}USDT"
    
    # 加载当前监控列表
    current_symbols = load_user_symbols()
    
    # 检查是否存在
    if symbol not in current_symbols:
        bot.reply_to(message, f"ℹ️ {symbol} 不在监控列表中")
        return
        
    # 从列表中移除
    current_symbols.remove(symbol)
    
    # 保存更新后的列表
    if save_user_symbols(current_symbols):
        bot.reply_to(message, f"✅ 已从监控列表中移除 {symbol}")
    else:
        bot.reply_to(message, f"❌ 保存监控列表失败，请稍后再试")

# 添加新命令处理函数 (查看监控列表)
@bot.message_handler(commands=['list'])
def list_symbols(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
    
    # 加载当前监控列表
    current_symbols = load_user_symbols()
    
    if not current_symbols:
        bot.reply_to(message, "📋 监控列表为空")
        return
        
    # 格式化列表
    symbols_list = "\n".join([f"• {symbol}" for symbol in current_symbols])
    bot.reply_to(message, f"📋 当前监控列表:\n{symbols_list}")

# 添加风险分析命令
@bot.message_handler(commands=['risk'])
def risk_analysis(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ 请指定要分析的币种，例如: /risk BTC")
        return
    
    # 获取币名并转换为大写
    coin = args[1].upper()
    
    # 如果已经包含USDT，使用原样，否则添加USDT后缀
    if 'USDT' in coin:
        symbol = coin
    else:
        symbol = f"{coin}USDT"
    
    bot.reply_to(message, f"🔍 正在分析 {symbol} 的风险参数，请稍等...")
    
    try:
        # 尝试获取K线数据，验证交易对是否存在
        test_data = get_klines(symbol, interval="1h", limit=1)
        if test_data is None or test_data.empty:
            bot.reply_to(message, f"❌ 交易对 {symbol} 不存在或无法获取数据")
            return
        
        # 获取分析数据
        prob_data = calculate_probability(symbol)
        
        if not prob_data:
            bot.reply_to(message, f"❌ 无法获取 {symbol} 的数据，请确认交易对是否正确")
            return
            
        # 风险图标
        risk_icon = "🟢" if prob_data.get('risk_level') == "low" else "🟡" if prob_data.get('risk_level') == "medium" else "🔴"
        
        # 方向箭头
        direction_arrow = "↗️" if prob_data['up_probability'] > 50 else "↘️"
        
        # 计算止损百分比
        stop_loss_percent = abs((prob_data['stop_loss'] - prob_data['price']) / prob_data['price'] * 100)
        
        # 计算目标百分比
        target_percent = abs((prob_data['take_profit'] - prob_data['price']) / prob_data['price'] * 100)
        
        # 风险收益比
        rr_ratio = prob_data.get('rr_info', {}).get('ratio', 0)
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化消息
        message_text = (
            f"🔍 {symbol} 风险分析 {direction_arrow} ({current_time})\n\n"
            f"📊 市场情况:\n"
            f"└ 当前价格: ${prob_data['price']:.4f}\n"
            f"└ 上涨概率: {prob_data['up_probability']:.1f}%\n"
            f"└ 市场类型: {prob_data.get('market_type', 'N/A')}\n"
            f"└ 信号强度: {prob_data.get('signal_strength_text', 'N/A')}\n\n"
            
            f"⚠️ 风险评估:\n"
            f"└ 风险等级: {risk_icon} {prob_data.get('risk_level', 'N/A').upper()}\n"
            f"└ 风险说明: {prob_data.get('risk_description', 'N/A')}\n"
            f"└ 风险收益比: {rr_ratio:.2f}\n\n"
            
            f"💰 交易参数:\n"
            f"└ 建议仓位: {prob_data.get('position_text', 'N/A')}\n"
            f"└ 建议止损: ${prob_data.get('stop_loss', 0):.4f} ({stop_loss_percent:.1f}%)\n"
            f"└ 目标价位: ${prob_data.get('take_profit', 0):.4f} ({target_percent:.1f}%)\n\n"
            
            f"📈 技术指标:\n"
            f"└ RSI (1h): {prob_data.get('rsi_1h', 0):.1f}\n"
            f"└ RSI (4h): {prob_data.get('rsi_4h', 0):.1f}\n"
            f"└ RSI (1d): {prob_data.get('rsi_1d', 0):.1f}\n"
            f"└ MACD柱状图: {prob_data.get('macd_histogram', 0):.6f}\n"
            f"└ 布林带位置: {prob_data.get('price_position_bb', 0):.2f}\n"
            f"└ ATR: {prob_data.get('atr', 0):.4f}\n\n"
            
            f"💡 交易建议:\n"
            f"└ 短期: {prob_data.get('short_term_rec', 'N/A')}\n"
            f"└ 长期: {prob_data.get('long_term_rec', 'N/A')}"
        )
        
        bot.reply_to(message, message_text)
        
    except Exception as e:
        logger.error(f"分析 {symbol} 风险失败: {e}")
        bot.reply_to(message, f"❌ 分析失败: {str(e)}")

# 添加一个简单的测试命令
@bot.message_handler(commands=['test'])
def test_command(message):
    """测试机器人是否正常响应"""
    bot.reply_to(message, "✅ 机器人工作正常!")

# 处理未知命令
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "🚫 你无权使用此机器人！")
        return
        
    bot.reply_to(message, "❓ 未知命令，使用 /help 查看可用命令") 