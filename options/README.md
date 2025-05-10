# 期权分析工具

这个工具用于分析特定股票的期权数据，计算期权被行权的概率和卖方的年化收益率，帮助找出最佳的期权交易机会。

## 功能

- 获取AAPL, MSFT, TSLA, NVDA, AMZN, GOOGL, META, IBIT, SPY, QQQ等股票的期权数据
- 计算不同到期日和行权价的期权被行权概率
- 计算作为期权卖方的年化收益率
- 找出被行权概率低、年化收益率高的最佳期权
- 生成数据可视化图表

## 安装

1. 安装所需的Python包：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行脚本:

```bash
python options_analysis.py
```

2. 脚本会自动分析所有指定股票的期权数据，并在控制台输出最佳的10个期权交易机会。

3. 结果会保存在`results`目录下，包括：
   - `options_analysis_results.csv`: 所有期权的详细数据
   - `best_options_overall.csv`: 整体最佳的10个期权
   - `best_options_by_ticker.csv`: 按股票分类的最佳期权
   - 多个可视化图表(.png文件)

## 结果说明

- `ticker`: 股票代码
- `option_type`: 期权类型(call看涨/put看跌)
- `expiration_date`: 到期日
- `strike`: 行权价
- `current_price`: 当前股价
- `option_price`: 期权价格
- `implied_volatility`: 隐含波动率
- `exercise_probability`: 被行权概率(%)
- `annualized_return`: 年化收益率(%)
- `volume`: 成交量
- `open_interest`: 未平仓合约数

## 注意事项

- 本工具使用yfinance获取数据，依赖于Yahoo Finance的API可用性
- 行权概率和年化收益率计算基于Black-Scholes模型和一些假设条件
- 推荐寻找被行权概率低于30%且年化收益率较高的期权
- 投资有风险，交易需谨慎 