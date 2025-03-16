# Telegram配置
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OWNER_ID = "YOUR_OWNER_ID"  # 严格限制只有你能使用
CHAT_ID = "YOUR_CHAT_ID"  # 添加这一行，通常与OWNER_ID相同

# 交易对配置
SYMBOLS = ["ETHUSDT", "BNBUSDT", "KAITOUSDT", "DOGEUSDT", "SOLUSDT"]

# 技术指标参数
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2
EMA_SHORT = 10
EMA_LONG = 20
ATR_PERIOD = 14

# 指标权重
RSI_WEIGHT = 0.25
MACD_WEIGHT = 0.25
BOLLINGER_WEIGHT = 0.20
EMA_WEIGHT = 0.20
ATR_WEIGHT = 0.10

# 安全配置
MAX_REQUESTS_PER_MINUTE = 60  # Binance API 限制

# 信号阈值
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# 定时任务间隔（分钟）
MONITOR_INTERVAL = 15
HEARTBEAT_INTERVAL = 240  # 4小时

# 添加重试和超时配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
MAX_RETRIES = 5      # 最大重试次数
RETRY_DELAY = 1      # 重试延迟（秒）

# 添加代理配置（如果需要）
PROXY_CONFIG = {
    'http': None,  # 如果需要代理，填写代理地址，如 'http://proxy.example.com:8080'
    'https': None
}

# 添加机器人轮询配置
POLLING_INTERVAL = 3       # 轮询间隔（秒）
POLLING_TIMEOUT = 30       # 轮询超时时间（秒）
LONG_POLLING_TIMEOUT = 30  # 长轮询超时时间（秒）

# 添加错误处理配置
ERROR_RETRY_DELAY = 30    # 错误重试延迟（秒）
MAX_RESTART_ATTEMPTS = 3  # 最大重启尝试次数

# 风险管理配置
POSITION_LOW_RISK = 0.30    # 低风险仓位比例
POSITION_MEDIUM_RISK = 0.15 # 中等风险仓位比例
POSITION_HIGH_RISK = 0.05   # 高风险仓位比例

# 止盈目标配置 (斐波那契水平)
TAKE_PROFIT_LOW_RISK = 1.618  # 低风险止盈倍数(ATR)
TAKE_PROFIT_MEDIUM_RISK = 2.0  # 中等风险止盈倍数(ATR)
TAKE_PROFIT_HIGH_RISK = 3.0  # 高风险止盈倍数(ATR)

# 止损配置
STOP_LOSS_MULTIPLIER = 1.5  # 止损ATR倍数
USE_DYNAMIC_SL = True  # 使用动态止损

# 信号强度阈值
PROBABILITY_CHANGE_THRESHOLD = 15  # 概率变化阈值(百分比)
STRONG_SIGNAL_THRESHOLD = 75  # 强烈信号阈值(百分比)

# 授权用户列表
AUTHORIZED_USERS = [
    "694209327",  # 将机器人拥有者ID添加到授权列表
    # 可以添加其他授权用户ID
]

# 其他配置保持不变... 