# 期权链数据下载工具

## 功能说明

此工具用于下载以下标的的期权链数据：
- **NVDA** (英伟达)
- **QQQ** (纳斯达克100 ETF)
- **IBIT** (iShares Bitcoin Trust)

## 数据内容

下载的数据包括：

### 1. 期权链数据
- 所有到期日的看涨(Call)和看跌(Put)期权
- **Greeks**:
  - Delta: 期权价格对标的价格的敏感度
  - Gamma: Delta的变化率
  - Theta: 时间衰减
  - Vega: 对波动率的敏感度
  - (注: yfinance提供的数据中包含impliedVolatility字段)

### 2. 波动率数据
- **HV (Historical Volatility)**: 历史波动率
  - HV_10d: 10日历史波动率
  - HV_20d: 20日历史波动率
  - HV_30d: 30日历史波动率
  - HV_60d: 60日历史波动率

- **RV (Realized Volatility)**: 实现波动率
  - RV_10d: 10日实现波动率（基于Parkinson估计）
  - RV_20d: 20日实现波动率
  - RV_30d: 30日实现波动率

### 3. 标的股价
- 当前市场价格
- 历史价格数据

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

直接运行脚本：

```bash
python fetch_options_chain.py
```

## 数据输出

数据将保存在 `data/` 目录下，每个标的有独立的子目录：

```
data/
├── NVDA/
│   ├── stock_info.json          # 股票基本信息和波动率
│   ├── summary.json             # 数据摘要
│   ├── all_options.csv          # 所有期权数据合并
│   ├── 2025-01-17_calls.csv    # 单个到期日的看涨期权
│   ├── 2025-01-17_puts.csv     # 单个到期日的看跌期权
│   └── ...
├── QQQ/
│   └── ...
└── IBIT/
    └── ...
```

## 数据字段说明

### stock_info.json
```json
{
  "ticker": "NVDA",
  "current_price": 150.25,
  "implied_volatility": 0.45,
  "timestamp": "2025-12-22T17:30:00",
  "historical_volatility": {
    "HV_10d": 0.38,
    "HV_20d": 0.42,
    "HV_30d": 0.40,
    "HV_60d": 0.45
  },
  "realized_volatility": {
    "RV_10d": 0.36,
    "RV_20d": 0.39,
    "RV_30d": 0.41
  }
}
```

### 期权链CSV文件字段
- `contractSymbol`: 期权合约代号
- `strike`: 行权价
- `lastPrice`: 最新价格
- `bid`: 买价
- `ask`: 卖价
- `volume`: 成交量
- `openInterest`: 持仓量
- `impliedVolatility`: 隐含波动率
- `optionType`: 期权类型 (CALL/PUT)
- `expirationDate`: 到期日
- `underlyingPrice`: 标的价格

## 注意事项

1. **API限制**: yfinance对请求频率有限制，脚本已添加延时
2. **数据延迟**: 免费数据可能有15-20分钟延迟
3. **Greeks计算**: yfinance不直接提供完整的Greeks，主要提供impliedVolatility
4. **运行时间**: 完整下载所有数据约需3-5分钟

## 如果需要更详细的Greeks

如果需要完整的Greeks（Delta, Gamma, Theta, Vega, Rho），可以：
1. 使用付费API（如Interactive Brokers、TD Ameritrade等）
2. 使用期权定价模型自行计算（Black-Scholes模型）

本脚本可以作为基础，后续可扩展添加Greeks计算功能。
