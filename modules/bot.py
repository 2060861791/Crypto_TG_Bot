"""
Telegram机器人核心功能
"""
import telebot
import logging
import time
from config import *

logger = logging.getLogger(__name__)

# 初始化机器人
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 🚀 仅允许授权用户使用
def is_authorized(user_id):
    """检查用户是否有权限使用机器人"""
    user_id = str(user_id)
    # 确保使用AUTHORIZED_USERS列表
    if 'AUTHORIZED_USERS' in globals():
        return user_id in AUTHORIZED_USERS or user_id == OWNER_ID
    else:
        # 如果未定义AUTHORIZED_USERS，则只允许OWNER_ID
        return user_id == OWNER_ID

# 启动消息
def send_startup_message():
    """发送机器人启动消息"""
    try:
        bot.send_message(CHAT_ID, f"@{OWNER_ID} 🤖 交易信号监控机器人已启动！\n\n使用 /m 查看市场概况\n使用 /help 查看帮助")
    except Exception as e:
        logger.error(f"无法发送启动消息: {e}")

# 错误处理
def handle_error(e, context=""):
    """统一错误处理"""
    error_message = f"@{OWNER_ID} ❌ 机器人运行异常 {context}: {str(e)}"
    logger.error(error_message)
    try:
        bot.send_message(CHAT_ID, error_message)
    except:
        pass

# 机器人轮询函数
def run_bot():
    """运行机器人的主函数"""
    while True:
        try:
            logger.info("开始 Telegram 机器人轮询...")
            # 使用配置文件中的参数
            bot.polling(
                none_stop=True,
                interval=POLLING_INTERVAL,
                timeout=POLLING_TIMEOUT,
                allowed_updates=['message', 'callback_query'],
                long_polling_timeout=LONG_POLLING_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Telegram 轮询出错: {e}")
            # 发生错误时，等待配置的延迟时间再重试
            time.sleep(ERROR_RETRY_DELAY)
            try:
                # 重置 webhook 以确保清理之前的连接
                bot.delete_webhook()
            except Exception as webhook_error:
                logger.error(f"清理webhook失败: {webhook_error}") 