# 币安交易信号监控Telegram机器人

## 项目概述

这是一个基于 Telegram 的加密货币交易信号监控机器人，能够实时分析多个交易对的技术指标，并在市场出现重要变化时发送提醒。机器人使用多种技术指标综合分析，为用户提供市场趋势和交易信号的实时监控。

## 主要功能

1. **多币种监控**：同时监控多个加密货币交易对（ETHUSDT, BNBUSDT, KAITOUSDT, DOGEUSDT, SOLUSDT）
2. **技术指标分析**：计算并分析多种技术指标
3. **信号强度评估**：综合评估多个指标，计算上涨概率和信号强度
4. **风险管理**：自动计算止损位、止盈位和建议仓位大小
5. **实时提醒**：当市场出现重要变化时，通过 Telegram 发送提醒
6. **定时报告**：定期发送市场概况和心跳消息
7. **用户交互**：通过 Telegram 命令与机器人交互，查询市场状态
8. **自定义监控列表**：允许用户动态添加/删除监控币种
9. **Twilio 电话与短信通知**：计划集成 Twilio API，当市场出现关键信号时，向用户发送电话或短信提醒

## 部分命令预览

![未标题-1](https://github.com/user-attachments/assets/a7587834-e888-4fe2-ac2a-5ba900a9dd82)



## 技术指标策略

机器人使用以下技术指标进行分析：

1. **RSI (相对强弱指标)**
   - 周期：14
   - 超买阈值：70
   - 超卖阈值：30
   - 权重：25%

2. **MACD (移动平均线收敛/发散)**
   - 快线周期：12
   - 慢线周期：26
   - 信号线周期：9
   - 权重：25%

3. **布林带 (Bollinger Bands)**
   - 周期：20
   - 标准差倍数：2
   - 权重：20%

4. **趋势分析**
   - 使用 EMA (指数移动平均线)
   - 短期 EMA：10
   - 长期 EMA：20
   - 权重：20%

5. **波动率分析**
   - 使用 ATR (平均真实范围)
   - 周期：14
   - 权重：10%

## 风险管理功能

机器人提供以下风险管理功能：

1. **风险评级**：根据市场状况、指标一致性和风险收益比，将交易信号分为低风险、中风险和高风险
2. **止损策略**：
   - 使用ATR指标计算动态止损位
   - 根据市场波动率自动调整止损距离
   - 提供多种止损计算方法（ATR、布林带、波动区间）
3. **止盈策略**：
   - 使用斐波那契扩展位设置止盈目标
   - 根据风险等级动态调整止盈目标
4. **仓位管理**：
   - 根据风险等级确定基础仓位大小
   - 考虑市场波动率动态调整仓位比例
   - 为高风险交易推荐轻仓或观望

## 信号计算方法

机器人通过以下步骤计算交易信号：

1. **单指标信号**：分别计算各个技术指标的信号
2. **综合评分**：根据各指标权重计算综合得分
3. **风险评估**：评估交易的风险等级和风险收益比
4. **信号变化监控**：跟踪信号变化，及时发送提醒

## 系统架构

1. **模块化设计**：
   - 主入口模块(index.py)负责启动和协调
   - API模块处理所有网络请求
   - 指标模块负责技术指标计算
   - 信号模块负责信号生成与评估
   - 风险模块负责风险参数计算
   - 机器人模块处理Telegram交互

2. **目录结构**：
   ```
   project/
   ├── index.py                # 主入口文件
   ├── config.py               # 配置文件
   ├── modules/
   │   ├── __init__.py
   │   ├── api.py              # API请求模块
   │   ├── indicators.py       # 技术指标计算模块
   │   ├── signals.py          # 信号生成与评估模块
   │   ├── risk.py             # 风险管理模块
   │   ├── bot.py              # Telegram机器人核心功能
   │   ├── bot_commands.py     # 机器人命令处理
   │   └── utils.py            # 通用工具函数
   ├── data/                   # 数据存储目录
   │   └── user_symbols.json   # 用户自定义监控列表
   └── bot.log                 # 日志文件
   ```

3. **错误处理**：
   - 完善的日志记录系统
   - 多级错误处理和重试机制
   - 自动恢复和重启功能

## 命令参考

机器人支持以下Telegram命令：

| 命令 | 描述 |
|------|------|
| `/m` 或 `/market` | 查看当前市场分析，包含所有监控币种的信号、风险参数 |
| `/add SYMBOL` | 添加交易对到监控列表，例如 `/add BTCUSDT` |
| `/remove SYMBOL` | 从监控列表移除交易对，例如 `/remove DOGEUSDT` |
| `/list` | 显示当前所有监控的交易对列表 |
| `/risk SYMBOL` | 查看特定交易对的详细风险分析，例如 `/risk ETHUSDT` |
| `/myid` | 获取你的用户ID（用于授权） |
| `/help` 或 `/h` | 显示帮助信息 |

## 环境安装与配置部署

### 服务器配置部署与稳定运行（24小时不间断监控）

为了确保机器人能够稳定运行，并避免 Binance API 在国内被墙的问题，建议采取以下措施：

1. **使用国内服务器 + 代理**  
   由于 Binance API 在国内可能无法直接访问，可以购买国内服务器（如阿里云、腾讯云等），然后配置代理（如 Shadowsocks、Clash、WireGuard 等）来绕过访问限制，确保机器人能够正常获取市场数据。

2. **进程管理与自动重启**  
   服务器上运行 Python 脚本可能会因异常崩溃，为了确保机器人 24 小时不间断运行，推荐使用 `pm2` 进行进程管理：

   - **安装 pm2**  

     ```bash
     npm install -g pm2
     ```

   - **启动机器人**  

     ```bash
     pm2 start index.py --name trading-bot
     ```

   - **设置开机自启**  

     ```bash
     pm2 startup
     ```

   - **持久化进程**（防止服务器重启后丢失进程）  

     ```bash
     pm2 save
     ```

3. **日志监控与错误恢复**  

   - `pm2 logs trading-bot` 可实时查看日志，快速排查问题  
   - `pm2 restart trading-bot` 可手动重启机器人  
   - 结合 `pm2 monit` 监控内存和 CPU 使用情况，确保长期稳定运行  

### 1. 环境要求
- Python 3.6+
- 稳定的网络连接
- Telegram账号

### 2. 安装依赖

```bash
pip install pandas telebot requests backoff numpy schedule
```

### 3. 配置文件设置

修改`config.py`文件中的关键配置：

```python
# Telegram配置
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"  # 从BotFather获取
OWNER_ID = "YOUR_TELEGRAM_ID"  # 你的Telegram ID
CHAT_ID = "YOUR_CHAT_ID"  # 消息发送目标聊天ID

# 授权用户
AUTHORIZED_USERS = [
    "YOUR_TELEGRAM_ID",
    # 添加其他用户ID
]

# 自定义监控交易对
SYMBOLS = ["ETHUSDT", "BNBUSDT", "BTCUSDT", "DOGEUSDT", "SOLUSDT"]
```

### 4. 启动机器人

```bash
python index.py
```

## 使用示例

1. **查看市场分析**：
   发送命令 `/market` 或 `/m` 获取所有监控币种的当前市场分析

2. **添加监控币种**：
   发送命令 `/add BTCUSDT` 将比特币添加到监控列表

3. **查看风险分析**：
   发送命令 `/risk ETHUSDT` 获取以太坊的详细风险参数

4. **查看监控列表**：
   发送命令 `/list` 查看当前所有监控的交易对

## 安全特性

1. **用户授权**：只允许授权用户访问机器人
2. **API 限流**：遵循 Binance API 的请求限制
3. **错误恢复**：自动处理网络错误和 API 异常

## 维护与故障排除

### 常见问题

1. **机器人不响应命令**
   - 检查互联网连接
   - 确认Telegram Bot Token是否正确
   - 查看日志文件`bot.log`了解错误详情

2. **无法获取市场数据**
   - 检查Binance API是否可访问
   - 确认您监控的交易对是否存在
   - 尝试重启机器人

### 日志文件

机器人会在根目录下生成`bot.log`文件，记录所有操作和错误。查看此文件可以帮助诊断问题：

```bash
tail -f bot.log
```

## 注意事项

- 本机器人仅提供技术分析和市场监控，不构成投资建议
- 交易决策应结合多种因素，不应仅依赖技术指标
- 加密货币市场波动较大，请谨慎使用信号进行交易
- 建议先使用小资金测试机器人提供的信号准确性

## 许可与免责声明

本项目仅供学习和研究使用，作者不对使用本项目产生的任何投资损失负责。使用本项目即表示您了解并接受交易风险。

---

**祝您交易愉快！**
