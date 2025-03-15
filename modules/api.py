"""
API请求相关功能
"""
import requests
import pandas as pd
import logging
import backoff
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException, ProxyError, SSLError
from config import *

logger = logging.getLogger(__name__)

# 配置 requests 的重试策略
def setup_requests_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # 总重试次数
        backoff_factor=1,  # 重试间隔
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Binance API URL
BINANCE_API_URL = "https://api.binance.com/api/v3"

# 使用 backoff 装饰器处理网络请求重试
@backoff.on_exception(
    backoff.expo,
    (RequestException, ProxyError, SSLError),
    max_tries=5,
    max_time=300
)
def get_binance_data(endpoint, params=None):
    """统一的 Binance API 请求函数"""
    try:
        session = setup_requests_session()
        url = f"{BINANCE_API_URL}/{endpoint}"
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Binance API 请求失败: {e}")
        return None
    finally:
        session.close()

# 🚀 获取 Binance 交易对 K 线数据
def get_klines(symbol, interval="15m", limit=100):
    try:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        data = get_binance_data("klines", params)
        if not data:
            return None

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        
        # 只转换需要的列，减少计算量
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
            
        return df
    except Exception as e:
        error_message = f"❌ 获取K线数据失败 - {symbol}: {str(e)}"
        logger.error(error_message)
        return None 