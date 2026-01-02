# 投资数据分析工具集

一个综合性的投资分析工具集合，涵盖宏观经济指标、股票期权分析、资产配置等多个领域。

## 📊 宏观经济分析

### [存款与M1](./deposits/README.md)
从央行官网拉取的活期存款数据，追踪货币供应量变化

### [市场综合预警仪表盘](./market_indicators/README.md)
5大核心市场预警指标：
- ERP (股权风险溢价)
- 巴菲特指标 (总市值/GDP)
- 高收益债利差 (HY Credit Spreads)
- 净流动性指标
- 20法则 (P/E + 通胀率)

### [美国债务与金价关系分析](./gold_analysis/analysis_report.md)
1970-2025年美国联邦债务与金价比率关系分析，包括债务/金价比率趋势和投资启示

## 📈 股票市场分析

### [美股收益分析](./backtesting/README.md)
长期投资标普500以及纳斯达克100的平均收益，历史回测数据

### [标普500回报率和CAPE相关性](./sp500_cape_analysis/analysis_report.md)
标普500回报率和CAPE（周期调整市盈率）相关性分析，包括Forward PE与未来收益率关系

## 🎯 期权交易工具

### [期权分析工具](./options/README.md)
期权交易策略分析：
- 计算期权被行权概率
- 卖方年化收益率计算
- 最佳期权交易机会推荐
- 支持AAPL, MSFT, TSLA, NVDA, AMZN, GOOGL, META, IBIT, SPY, QQQ等

### [期权链数据下载工具](./options_chain_fetcher/README.md)
下载NVDA, QQQ, IBIT的完整期权链数据：
- 所有到期日的期权数据
- 历史波动率 (HV) 和实现波动率 (RV)
- 隐含波动率和Greeks指标

## 💰 资产配置与估值

### [投资分析](./investment_analysis/investment_report.md)
投资分析，包括投资回报率，风险，以及30年后的资产预测

### [房地产DCF](./real_estate_dcf/reports/dcf_report.md)
房地产DCF估值模型，包括租金收入，运营支出，增长率，贴现率，预测期，最终资本化率

## 🛠️ 使用说明

每个子目录都包含独立的工具和详细的README文档，请查看相应目录了解具体使用方法。

## ⚠️ 免责声明

本工具集仅供学习和参考使用，不构成任何投资建议。投资有风险，入市需谨慎。
