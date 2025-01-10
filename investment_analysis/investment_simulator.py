import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_historical_metrics(ticker, start_year=None, dividend_yield=0):
    """计算历史年化回报率和波动率，加入估算的股息收益率"""
    try:
        # 获取尽可能长的历史数据
        stock = yf.Ticker(ticker)
        hist = stock.history(period="max")
        
        # 如果指定了起始年份，只使用该年份之后的数据
        if start_year:
            hist = hist[hist.index.year >= start_year]
        
        # 计算价格回报
        hist['Price_Return'] = hist['Close'].pct_change().fillna(0)
        
        # 加入估算的每日股息收益率
        daily_div_yield = (1 + dividend_yield) ** (1/252) - 1
        hist['Total_Return'] = hist['Price_Return'] + daily_div_yield
        
        # 计算年度总回报率
        annual_returns = (1 + hist['Total_Return']).resample('Y').prod() - 1
        
        # 计算年化回报率和波动率
        annual_return = (1 + annual_returns).prod() ** (1/len(annual_returns)) - 1
        annual_std = annual_returns.std()
        
        print(f"\n{ticker} 历史数据分析（含估算股息收益率 {dividend_yield*100:.1f}%）:")
        print(f"数据年份范围: {hist.index[0].year} - {hist.index[-1].year}")
        print(f"总年数: {len(annual_returns)}")
        print(f"年化总回报率: {annual_return*100:.1f}%")
        print(f"年度波动率: {annual_std*100:.1f}%")
        print(f"年度总回报率分布:")
        print(annual_returns.describe())
        print("\n各个十年的平均总回报率:")
        
        # 计算每个十年的平均回报率
        for decade_start in range(hist.index[0].year // 10 * 10, 
                                hist.index[-1].year // 10 * 10, 10):
            decade_end = decade_start + 9
            decade_data = annual_returns[
                (annual_returns.index.year >= decade_start) & 
                (annual_returns.index.year <= decade_end)
            ]
            if not decade_data.empty:
                decade_return = (1 + decade_data).prod() ** (1/len(decade_data)) - 1
                print(f"{decade_start}s: {decade_return*100:.1f}%")
        
        return annual_return, annual_std
        
    except Exception as e:
        print(f"获取{ticker}数据时出错: {e}")
        return None, None

# 初始投资金额
TREASURY_INITIAL = 520000
VOO_INITIAL = 80000
QQQM_INITIAL = 80000
FOUR01K_INITIAL = 240000

# 每月从国债转移到股票的金额
MONTHLY_TRANSFER = 10000  # 每月总共转移10000 (VOO 5000 + QQQM 5000)
TOTAL_TRANSFER = 320000  # 总共要转移的金额
MONTHS_TO_TRANSFER = TOTAL_TRANSFER // MONTHLY_TRANSFER  # 需要转移的月数

# 模拟参数
YEARS = 30
SIMULATIONS = 100000  # 增加到10万次模拟

# 获取实际历史数据
print("\n计算历史回报率和波动率（含估算股息）...")

# 使用标普500指数（^GSPC）的50年数据，加入VOO的股息收益率1.4%
print("\n获取标普500指数50年数据...")
VOO_DIVIDEND_YIELD = 0.014  # VOO当前股息收益率1.4%
VOO_RETURN, VOO_STD = calculate_historical_metrics("^GSPC", 1974, VOO_DIVIDEND_YIELD)

# 使用纳斯达克100指数（^NDX）的数据，加入QQQM的股息收益率0.5%
print("\n获取纳斯达克100指数数据...")
QQQM_DIVIDEND_YIELD = 0.005  # QQQM当前股息收益率0.5%
QQQM_RETURN, QQQM_STD = calculate_historical_metrics("^NDX", 1974, QQQM_DIVIDEND_YIELD)

if VOO_RETURN is None or QQQM_RETURN is None:
    print("使用默认值")
    # 如果无法获取数据，使用默认值（含股息的历史回报）
    VOO_RETURN = 0.102 + VOO_DIVIDEND_YIELD  # 10.2% + 1.4% 股息
    VOO_STD = 0.16
    QQQM_RETURN = 0.135 + QQQM_DIVIDEND_YIELD  # 13.5% + 0.5% 股息
    QQQM_STD = 0.32

VOO_EXPENSE_RATIO = 0.0003  # VOO的管理费率0.03%
QQQM_EXPENSE_RATIO = 0.0015  # QQQM的管理费率0.15%

# 税率设置
LONG_TERM_CAPITAL_GAINS_TAX = 0.20  # 长期资本利得税率20%
TREASURY_INTEREST_TAX = 0.37  # 国债利息所得税率37%

def simulate_treasury_returns(initial=TREASURY_INITIAL, years=YEARS):
    """模拟国债收益，考虑每月转出资金和税收
    假设利率从4.25%开始，随时间逐渐降至2.5%左右"""
    rates = np.linspace(0.0425, 0.025, years)
    monthly_rates = rates / 12  # 转换为月利率
    
    balance = initial
    yearly_balances = [initial]
    months_completed = 0
    
    for year in range(years):
        year_rate = rates[year]
        yearly_interest = 0
        for month in range(12):
            if months_completed < MONTHS_TO_TRANSFER:
                balance -= MONTHLY_TRANSFER
                months_completed += 1
            monthly_interest = balance * monthly_rates[year]
            yearly_interest += monthly_interest
            balance += monthly_interest
        
        # 扣除利息所得税
        tax_on_interest = yearly_interest * TREASURY_INTEREST_TAX
        balance -= tax_on_interest
        yearly_balances.append(balance)
    
    return yearly_balances

def simulate_stock_returns_with_monthly_investment(initial, monthly_investment, 
                                                 expected_return, std_dev,
                                                 expense_ratio,
                                                 years=YEARS, simulations=SIMULATIONS):
    """使用Monte Carlo模拟股票回报，包含每月投资和管理费"""
    results = np.zeros((simulations, years + 1))
    results[:, 0] = initial
    
    # 调整回报率以反映管理费
    expected_return = expected_return - expense_ratio
    monthly_return = expected_return / 12
    monthly_std = std_dev / np.sqrt(12)
    
    for sim in range(simulations):
        balance = initial
        months_invested = 0
        
        for year in range(years):
            for month in range(12):
                if months_invested < MONTHS_TO_TRANSFER:
                    balance += monthly_investment
                    months_invested += 1
                monthly_return_rate = np.random.lognormal(
                    mean=np.log(1 + monthly_return) - monthly_std**2/2,
                    sigma=monthly_std
                ) - 1
                balance *= (1 + monthly_return_rate)
            results[sim, year + 1] = balance
    
    # 在最终结果中扣除长期资本利得税
    capital_gains = results[:, -1] - (initial + monthly_investment * min(MONTHS_TO_TRANSFER, years * 12))
    results[:, -1] -= capital_gains * LONG_TERM_CAPITAL_GAINS_TAX
    
    return results

def simulate_401k_returns(initial=FOUR01K_INITIAL, expected_return=0.10, 
                         std_dev=0.15, years=YEARS, simulations=SIMULATIONS):
    """模拟401k账户回报"""
    results = np.zeros((simulations, years + 1))
    results[:, 0] = initial
    
    for sim in range(simulations):
        balance = initial
        for year in range(years):
            return_rate = np.random.normal(expected_return, std_dev)
            balance *= (1 + return_rate)
            results[sim, year + 1] = balance
    
    return results

def main():
    print("\n开始进行100,000次蒙特卡洛模拟...")
    
    # 运行模拟
    treasury_results = simulate_treasury_returns()
    
    print("\n模拟VOO (标普500ETF)投资结果...")
    voo_results = simulate_stock_returns_with_monthly_investment(
        VOO_INITIAL, 5000, VOO_RETURN, VOO_STD, VOO_EXPENSE_RATIO)
    
    print("\n模拟QQQM (纳斯达克100ETF)投资结果...")
    qqqm_results = simulate_stock_returns_with_monthly_investment(
        QQQM_INITIAL, 5000, QQQM_RETURN, QQQM_STD, QQQM_EXPENSE_RATIO)
    
    print("\n模拟401k账户投资结果...")
    four01k_results = simulate_401k_returns()
    
    # 合并所有资产
    print("\n合并资产组合结果...")
    total_results = np.zeros((SIMULATIONS, YEARS + 1))
    total_results += treasury_results  # 广播到所有模拟
    total_results += voo_results
    total_results += qqqm_results
    total_results += four01k_results
    
    # 计算每种资产的中位数结果
    treasury_final = treasury_results[-1]  # 国债没有多次模拟，直接取最后一个值
    voo_median = np.median(voo_results[:, -1])
    qqqm_median = np.median(qqqm_results[:, -1])
    four01k_median = np.median(four01k_results[:, -1])
    
    # 计算统计数据
    percentiles = np.percentile(total_results[:, -1], [5, 25, 50, 75, 95])
    mean_result = np.mean(total_results[:, -1])
    
    print(f"\n=== {YEARS}年后投资组合分析（基于{SIMULATIONS:,}次模拟） ===")
    print(f"初始投资总额: ${TREASURY_INITIAL + VOO_INITIAL + QQQM_INITIAL + FOUR01K_INITIAL:,.2f}")
    print(f"每月从国债转移至股票: ${MONTHLY_TRANSFER:,.2f}")
    print(f"总计划转移金额: ${TOTAL_TRANSFER:,.2f}")
    
    print(f"\n费用和税率设置:")
    print(f"VOO管理费率: {VOO_EXPENSE_RATIO*100:.3f}%")
    print(f"QQQM管理费率: {QQQM_EXPENSE_RATIO*100:.3f}%")
    print(f"长期资本利得税率: {LONG_TERM_CAPITAL_GAINS_TAX*100:.1f}%")
    print(f"国债利息所得税率: {TREASURY_INTEREST_TAX*100:.1f}%")
    
    print(f"\n各资产类别增长情况（中位数）:")
    print(f"国债:")
    print(f"  初始金额: ${TREASURY_INITIAL:,.2f}")
    print(f"  最终金额: ${treasury_final:,.2f}")
    print(f"  增长倍数: {treasury_final/TREASURY_INITIAL:.1f}倍")
    
    voo_total_invest = VOO_INITIAL + 5000 * MONTHS_TO_TRANSFER
    print(f"\nVOO (标普500ETF):")
    print(f"  初始金额: ${VOO_INITIAL:,.2f}")
    print(f"  定投金额: ${5000 * MONTHS_TO_TRANSFER:,.2f}")
    print(f"  总投入: ${voo_total_invest:,.2f}")
    print(f"  最终金额: ${voo_median:,.2f}")
    print(f"  相对总投入增长倍数: {voo_median/voo_total_invest:.1f}倍")
    print(f"  年化回报率(税费前): {VOO_RETURN*100:.1f}%")
    
    qqqm_total_invest = QQQM_INITIAL + 5000 * MONTHS_TO_TRANSFER
    print(f"\nQQQM (纳斯达克100ETF):")
    print(f"  初始金额: ${QQQM_INITIAL:,.2f}")
    print(f"  定投金额: ${5000 * MONTHS_TO_TRANSFER:,.2f}")
    print(f"  总投入: ${qqqm_total_invest:,.2f}")
    print(f"  最终金额: ${qqqm_median:,.2f}")
    print(f"  相对总投入增长倍数: {qqqm_median/qqqm_total_invest:.1f}倍")
    print(f"  年化回报率(税费前): {QQQM_RETURN*100:.1f}%")
    
    print(f"\n401k账户:")
    print(f"  初始金额: ${FOUR01K_INITIAL:,.2f}")
    print(f"  最终金额: ${four01k_median:,.2f}")
    print(f"  增长倍数: {four01k_median/FOUR01K_INITIAL:.1f}倍")
    
    print(f"\n投资组合整体表现:")
    print(f"最差情况 (5th percentile): ${percentiles[0]:,.2f}")
    print(f"25th percentile: ${percentiles[1]:,.2f}")
    print(f"中位数 (50th percentile): ${percentiles[2]:,.2f}")
    print(f"75th percentile: ${percentiles[3]:,.2f}")
    print(f"最好情况 (95th percentile): ${percentiles[4]:,.2f}")
    print(f"平均值: ${mean_result:,.2f}")
    
    print("\n生成可视化图表...")
    
    # 绘制结果分布图
    plt.figure(figsize=(12, 6))
    
    # 计算合理的横坐标范围和bin数量
    data = total_results[:, -1] / 1_000_000
    q1, q99 = np.percentile(data, [1, 99])  # 使用1和99百分位数作为范围
    bin_width = (q99 - q1) / 100  # 使用更细的bin
    bins = np.arange(0, q99 + bin_width, bin_width)
    
    print(f"\n资产分布统计:")
    print(f"1%分位数: ${q1*1_000_000:,.2f}")
    print(f"99%分位数: ${q99*1_000_000:,.2f}")
    print(f"Bin宽度: ${bin_width*1_000_000:,.2f}")
    
    sns.histplot(data, bins=bins, stat='density', element='step')
    plt.xlim(0, q99)
    plt.title('Asset Distribution after 30 Years (Million USD)')
    plt.xlabel('Total Assets (Million USD)')
    plt.ylabel('Density')
    plt.grid(True, alpha=0.3)
    plt.savefig('distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 绘制资产增长路径图
    plt.figure(figsize=(12, 6))
    percentiles = np.percentile(total_results, [5, 25, 50, 75, 95], axis=0)  # 增加25和75百分位数
    years = np.arange(YEARS + 1)
    
    # 绘制中位数路径
    plt.plot(years, percentiles[2] / 1_000_000, 'b-', linewidth=2, label='Median Path')
    
    # 绘制置信区间
    plt.fill_between(years, 
                     percentiles[0] / 1_000_000,  # 5%
                     percentiles[4] / 1_000_000,  # 95%
                     alpha=0.2,
                     color='blue',
                     label='90% Confidence Interval')
    
    plt.fill_between(years, 
                     percentiles[1] / 1_000_000,  # 25%
                     percentiles[3] / 1_000_000,  # 75%
                     alpha=0.3,
                     color='blue',
                     label='50% Confidence Interval')
    
    plt.title('Asset Growth Projection')
    plt.xlabel('Years')
    plt.ylabel('Total Assets (Million USD)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('growth_path.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n模拟完成。图表已保存为 distribution.png 和 growth_path.png")

if __name__ == "__main__":
    main() 