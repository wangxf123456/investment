# 期权链数据Dashboard使用指南

## 📊 项目概述

这是一个完整的期权链数据获取和可视化系统，包含：
- 数据下载脚本
- Greeks计算工具
- **美观的Web Dashboard界面**

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载数据并计算Greeks

```bash
python run_all.py
```

这将自动执行：
- 下载NVDA、QQQ、IBIT的期权链数据
- 计算所有期权的Greeks（Delta, Gamma, Theta, Vega, Rho）
- 计算历史波动率(HV)和实现波动率(RV)

### 3. 启动Dashboard

```bash
python dashboard.py
```

然后在浏览器中打开：
```
http://localhost:5000
```

## 📁 项目结构

```
options_chain_fetcher/
├── fetch_options_chain.py      # 数据下载脚本
├── calculate_greeks.py         # Greeks计算脚本
├── dashboard.py                # Web服务器
├── run_all.py                  # 一键运行所有脚本
├── view_data.py                # 命令行数据查看工具
├── requirements.txt            # 依赖包列表
├── README_DASHBOARD.md         # 本文档
├── templates/
│   └── dashboard.html          # Dashboard前端页面
└── data/                       # 数据目录
    ├── NVDA/
    │   ├── stock_info.json
    │   ├── all_options.csv
    │   ├── options_with_greeks.csv
    │   └── ...
    ├── QQQ/
    └── IBIT/
```

## 🎨 Dashboard功能

### 1. 概览卡片
- 显示每个标的的当前股价
- 总期权数和到期日数量
- 30天历史波动率(HV)和实现波动率(RV)

### 2. 波动率分析图表
- 可切换不同标的(NVDA/QQQ/IBIT)
- 对比历史波动率(HV)和实现波动率(RV)
- 显示10日、20日、30日、60日的波动率

### 3. 期权链数据表格
- 可选择不同标的和到期日
- 分别显示看涨期权(Calls)和看跌期权(Puts)
- 包含以下信息：
  - 行权价(Strike)
  - 最新价格(Last Price)
  - 成交量(Volume)
  - 隐含波动率(IV)
  - **Greeks**: Delta, Gamma, Theta, Vega

### 4. 交互功能
- 实时数据刷新
- 标签切换查看不同标的
- 响应式设计，支持手机和平板

## 📊 数据说明

### Greeks解释

- **Delta**: 标的价格变动$1时，期权价格的变化
  - Call: 0到1之间
  - Put: -1到0之间
  
- **Gamma**: Delta的变化率，衡量Delta的稳定性
  - 值越大，Delta变化越快
  
- **Theta**: 时间衰减，每天损失的期权价值
  - 通常为负值
  
- **Vega**: 隐含波动率变动1%时，期权价格的变化
  
- **Rho**: 利率变动1%时，期权价格的变化

### 波动率解释

- **HV (Historical Volatility)**: 基于历史价格计算的波动率
  - 使用对数收益率的标准差
  - 年化处理（×√252）
  
- **RV (Realized Volatility)**: 使用高低价的Parkinson估计
  - 考虑了日内波动
  - 更准确地反映实际波动

- **IV (Implied Volatility)**: 隐含波动率
  - 从期权价格反推的波动率
  - 反映市场对未来波动的预期

## 🛠️ 高级使用

### 单独运行脚本

```bash
# 只下载数据
python fetch_options_chain.py

# 只计算Greeks
python calculate_greeks.py

# 命令行查看数据
python view_data.py
```

### 自定义配置

修改脚本中的参数：

**fetch_options_chain.py**:
```python
TICKERS = ["NVDA", "QQQ", "IBIT"]  # 可添加更多标的
```

**calculate_greeks.py**:
```python
risk_free_rate = 0.045  # 调整无风险利率
```

## 🎯 Dashboard界面特点

- **现代化设计**: 使用深色主题和渐变色
- **响应式布局**: 自动适配各种屏幕尺寸
- **交互式图表**: 使用Chart.js库
- **实时更新**: 点击刷新按钮获取最新数据
- **性能优化**: 快速加载和流畅动画

## 🔧 故障排除

### 端口被占用
如果5000端口被占用，修改dashboard.py：
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改成其他端口
```

### 数据未找到
确保先运行`run_all.py`下载数据

### API限制
如遇到yfinance API限制：
- 等待几分钟后重试
- 减少下载的到期日数量

## 📸 Dashboard截图说明

打开浏览器访问 http://localhost:5000，你将看到：

1. **顶部Header**: 标题和刷新按钮
2. **概览卡片**: 三个标的的实时信息
3. **波动率图表**: 交互式折线图
4. **期权表格**: 详细的期权数据和Greeks

## 💡 提示

- 建议每天运行一次`run_all.py`获取最新数据
- Dashboard可以一直运行在后台
- 数据保存在CSV文件中，可以用Excel打开
- Greeks计算基于Black-Scholes模型

## 📞 技术支持

如有问题，检查：
1. 所有依赖是否正确安装
2. data目录是否有数据文件
3. Python版本 >= 3.7
4. 网络连接是否正常

---

**享受使用吧！ 📈💰**
