"""
交易信号监控机器人 - 主入口文件
"""
import time
import threading
import logging
import os
import sys
from config import *

# 导入模块
from modules.utils import setup_logging
from modules.api import setup_requests_session
from modules.bot import bot, run_bot, send_startup_message
from modules.signals import monitor_symbols

# 重要！导入命令处理模块以确保命令注册
import modules.bot_commands

# 设置日志
logger = setup_logging()

logger.info("📡 交易信号监控启动中...")

if __name__ == "__main__":
    try:
        # 确保清理之前的webhook设置
        bot.delete_webhook()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_symbols)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 发送启动消息
        try:
            send_startup_message()
        except Exception as e:
            logger.error(f"无法发送启动消息: {e}")

        # 启动机器人
        logger.info("开始运行机器人...")
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("收到退出信号，正在关闭机器人...")
        # 清理资源
        try:
            bot.stop_polling()
        except:
            pass
    except Exception as e:
        logger.error(f"机器人运行出错: {e}")
        # 重启机器人
        time.sleep(60)  # 等待1分钟后重试
        os.execv(sys.executable, ['python'] + sys.argv)  # 重启程序