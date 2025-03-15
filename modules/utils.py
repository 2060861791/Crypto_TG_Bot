import json
import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# 设置日志
def setup_logging():
    """设置日志记录系统"""
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件输出
    try:
        file_handler = logging.FileHandler('bot.log', encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"无法设置文件日志: {e}")
    
    # 禁用一些不需要的日志
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telebot").setLevel(logging.WARNING)
    logging.getLogger("schedule").setLevel(logging.WARNING)
    
    logger = logging.getLogger("bot")
    logger.info(f"日志系统初始化完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return logger

# 确保数据目录存在
def ensure_data_dir():
    Path("data").mkdir(exist_ok=True)

# 读取用户自定义监控列表
def load_user_symbols():
    try:
        ensure_data_dir()
        if not os.path.exists("data/user_symbols.json"):
            # 如果文件不存在，使用默认列表
            from config import SYMBOLS
            return SYMBOLS
            
        with open("data/user_symbols.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载用户自定义币种失败: {e}")
        # 发生错误时返回默认列表
        from config import SYMBOLS
        return SYMBOLS

# 保存用户自定义监控列表
def save_user_symbols(symbols):
    try:
        ensure_data_dir()
        with open("data/user_symbols.json", "w") as f:
            json.dump(symbols, f)
        return True
    except Exception as e:
        logger.error(f"保存用户自定义币种失败: {e}")
        return False 