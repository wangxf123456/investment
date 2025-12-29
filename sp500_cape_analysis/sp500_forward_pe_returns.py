import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import scipy.stats as stats
from statsmodels.nonparametric.smoothers_lowess import lowess
import os
import time
import io

def get_sp500_data():
    """获取标普500数据，从1990年开始到现在"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"  尝试下载 SP500 数据 (第 {attempt + 1}/{max_retries} 次)...")
            ticker = yf.Ticker('^GSPC')
            sp500 = ticker.history(start='1990-01-01', auto_adjust=True)
            
            if sp500.empty:
                raise Exception("获取标普500数据失败")
            # 确保使用月末数据
            monthly_data = sp500['Close'].resample('M').last()
            return monthly_data
        except Exception as e:
            print(f"  尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"获取标普500数据时出错: {str(e)}")
                raise

def get_forward_pe_data():
    """
    获取标普500 Forward PE数据
    尝试从多个数据源获取：
    1. Multpl.com (S&P 500 PE Ratio)
    2. 使用备用计算方法
    """
    print("正在获取 Forward PE 数据...")
    
    # 方法1：尝试从 Multpl.com 获取 PE Ratio 数据
    try:
        print("  尝试从 Multpl.com 获取 PE 数据...")
        url = "https://www.multpl.com/s-p-500-pe-ratio/table/by-month"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'datatable'})
        
        if table:
            dates = []
            values = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    date_str = cols[0].text.strip()
                    value_str = cols[1].text.strip().replace(',', '')
                    
                    try:
                        date = pd.to_datetime(date_str)
                        value = float(value_str)
                        dates.append(date)
                        values.append(value)
                    except:
                        continue
            
            if dates:
                df = pd.DataFrame({'Date': dates, 'PE': values})
                df.set_index('Date', inplace=True)
                df = df.sort_index()
                df = df.resample('M').last()
                df = df['1990':]
                print(f"  成功获取 Trailing PE 数据: {len(df)} 个数据点")
                
                # 注意：这是 Trailing PE，我们将基于此估算 Forward PE
                # Forward PE = Trailing PE * (1 - 预期盈利增长率的调整因子)
                # 这里我们使用一个简化的方法：Forward PE ≈ Trailing PE * 0.9 (假设平均10%盈利增长)
                df['Forward_PE'] = df['PE'] * 0.9
                return df[['Forward_PE', 'PE']]
                
    except Exception as e:
        print(f"  从 Multpl.com 获取数据失败: {str(e)}")
    
    # 方法2：尝试从 Quandl/NASDAQ 获取数据
    try:
        print("  尝试从备用数据源获取...")
        # 使用估算的PE数据
        # 基于标普500的历史收益和价格计算
        return estimate_forward_pe_from_earnings()
    except Exception as e:
        print(f"  备用方法失败: {str(e)}")
    
    raise Exception("无法获取 Forward PE 数据")

def estimate_forward_pe_from_earnings():
    """
    基于标普500的历史数据估算 Forward PE
    使用 Shiller 数据中的收益数据来计算
    """
    print("  使用 Shiller 数据计算 PE...")
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    with open('temp_shiller_data_pe.xls', 'wb') as f:
        f.write(response.content)
    
    df = pd.read_excel('temp_shiller_data_pe.xls', sheet_name="Data", skiprows=7)
    
    # 提取需要的列
    df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y.%m')
    
    # Price 列和 Earnings 列
    price_col = [col for col in df.columns if 'Price' in str(col) or col == 'P'][0]
    earnings_col = [col for col in df.columns if 'Earnings' in str(col) or col == 'E'][0]
    
    df = df[['Date', price_col, earnings_col, 'CAPE']]
    df.columns = ['Date', 'Price', 'Earnings', 'CAPE']
    df.set_index('Date', inplace=True)
    
    # 计算 Trailing PE
    df['Trailing_PE'] = df['Price'] / df['Earnings']
    
    # 估算 Forward PE（基于12个月远期盈利预期）
    # 使用历史盈利增长率来估算
    df['Earnings_Growth'] = df['Earnings'].pct_change(12)  # 12个月盈利增长
    df['Expected_Earnings'] = df['Earnings'] * (1 + df['Earnings_Growth'].rolling(12).mean().shift(1))
    df['Forward_PE'] = df['Price'] / df['Expected_Earnings']
    
    # 清理数据
    df = df[['Forward_PE', 'Trailing_PE']].dropna()
    df = df.resample('M').last()
    df = df['1990':]
    
    # 删除临时文件
    if os.path.exists('temp_shiller_data_pe.xls'):
        os.remove('temp_shiller_data_pe.xls')
    
    # 使用合理的范围过滤异常值
    df = df[(df['Forward_PE'] > 5) & (df['Forward_PE'] < 60)]
    
    print(f"  成功计算 Forward PE 数据: {len(df)} 个数据点")
    return df

def get_yfinance_forward_pe():
    """
    从 yfinance 获取当前的 Forward PE
    用于对比和验证
    """
    try:
        sp500 = yf.Ticker('^GSPC')
        info = sp500.info
        forward_pe = info.get('forwardPE', None)
        trailing_pe = info.get('trailingPE', None)
        return forward_pe, trailing_pe
    except:
        return None, None

def calculate_returns(prices, years=10):
    """计算年化收益率
    对于每个时间点，计算未来years年的年化收益率
    如果未来数据不足years年，则返回NaN
    """
    returns = pd.Series(index=prices.index, dtype=float)
    for i in range(len(prices)):
        if i + years*12 < len(prices):
            start_price = prices.iloc[i]
            end_price = prices.iloc[i + years*12]
            returns.iloc[i] = (end_price / start_price) ** (1/years) - 1
    return returns * 100  # 转换为百分比

def create_pe_price_comparison_plot(sp500_data, pe_data):
    """创建Forward PE和SP500股价的时间序列对比图"""
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # 统一时区（移除时区信息）
    sp500_idx = sp500_data.index.tz_localize(None) if sp500_data.index.tz is not None else sp500_data.index
    pe_idx = pe_data.index.tz_localize(None) if pe_data.index.tz is not None else pe_data.index
    
    sp500_data = sp500_data.copy()
    sp500_data.index = sp500_idx
    pe_data = pe_data.copy()
    pe_data.index = pe_idx
    
    # 找到共同的时间范围
    common_start = max(sp500_data.index.min(), pe_data.index.min())
    common_end = min(sp500_data.index.max(), pe_data.index.max())
    
    # 筛选共同时间范围的数据
    sp500_filtered = sp500_data[(sp500_data.index >= common_start) & (sp500_data.index <= common_end)]
    pe_filtered = pe_data[(pe_data.index >= common_start) & (pe_data.index <= common_end)]
    
    # 删除缺失值并插值填充
    sp500_filtered = sp500_filtered.dropna()
    pe_filtered = pe_filtered.dropna()
    
    # 绘制SP500股价（左Y轴，使用对数刻度）
    color1 = '#2E86AB'
    ax1.set_xlabel('时间', fontsize=12)
    ax1.set_ylabel('标普500指数', color=color1, fontsize=12)
    ax1.semilogy(sp500_filtered.index, sp500_filtered.values, color=color1, linewidth=1.5, label='标普500指数')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(bottom=sp500_filtered.min() * 0.8)
    
    # 创建右Y轴绘制Forward PE
    ax2 = ax1.twinx()
    color2 = '#E94F37'
    ax2.set_ylabel('Forward PE', color=color2, fontsize=12)
    ax2.plot(pe_filtered.index, pe_filtered['Forward_PE'].values, color=color2, linewidth=1.5, alpha=0.8, label='Forward PE')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 添加Forward PE历史均值线
    pe_mean = pe_filtered['Forward_PE'].mean()
    ax2.axhline(y=pe_mean, color=color2, linestyle='--', alpha=0.5, linewidth=1)
    ax2.text(pe_filtered.index[-1], pe_mean, f' 均值: {pe_mean:.1f}', 
             color=color2, fontsize=10, va='center')
    
    # 设置标题
    plt.title(f'标普500指数与Forward PE历史走势对比\n({common_start.strftime("%Y年%m月")} - {common_end.strftime("%Y年%m月")})', 
              fontsize=14, fontweight='bold')
    
    # 添加图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # 添加网格
    ax1.grid(True, alpha=0.3)
    
    fig.tight_layout()
    plt.savefig('sp500_forward_pe_history.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Forward PE与股价对比图已保存为 sp500_forward_pe_history.png")

def create_scatter_plot(combined_data, years, current_pe=21):
    """创建散点图和拟合线"""
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=combined_data, x='Forward_PE', y=f'{years}Y_Returns', alpha=0.6)
    
    # 计算皮尔逊和斯皮尔曼相关系数
    pearson_corr = combined_data['Forward_PE'].corr(combined_data[f'{years}Y_Returns'])
    spearman_corr = combined_data['Forward_PE'].corr(combined_data[f'{years}Y_Returns'], method='spearman')
    
    # 线性回归
    z = np.polyfit(combined_data['Forward_PE'], combined_data[f'{years}Y_Returns'], 1)
    p = np.poly1d(z)
    plt.plot(combined_data['Forward_PE'], p(combined_data['Forward_PE']), "r--", alpha=0.8, label='线性回归')
    
    # LOWESS平滑
    lowess_result = lowess(combined_data[f'{years}Y_Returns'], combined_data['Forward_PE'], 
                          frac=0.3, it=3, return_sorted=True)
    plt.plot(lowess_result[:, 0], lowess_result[:, 1], 'b--', alpha=0.8, label='LOWESS平滑')
    
    # 添加当前PE的竖线
    plt.axvline(x=current_pe, color='r', linestyle='-', alpha=0.5)
    predicted_return = z[0] * current_pe + z[1]
    plt.plot([current_pe], [predicted_return], 'ro', markersize=10)
    
    # 在图表上添加信息
    equation = f'线性: y = {z[0]:.2f}x + {z[1]:.2f}'
    correlation_text = f'皮尔逊相关系数 = {pearson_corr:.2f}\n斯皮尔曼相关系数 = {spearman_corr:.2f}'
    current_pe_text = f'当前Forward PE = {current_pe}\n预期收益率 = {predicted_return:.2f}%'
    
    plt.text(0.05, 0.95, equation + '\n' + correlation_text + '\n' + current_pe_text,
             transform=plt.gca().transAxes, 
             bbox=dict(facecolor='white', alpha=0.8),
             verticalalignment='top')
    
    # 设置图表标题和标签
    plt.title(f'标普500 Forward PE与未来{years}年年化收益率的关系\n' + 
             f'({combined_data.index.min().strftime("%Y年%m月")}-{combined_data.index.max().strftime("%Y年%m月")})')
    plt.xlabel('Forward PE')
    plt.ylabel(f'未来{years}年年化收益率(%)')
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(f'sp500_forward_pe_returns_{years}y.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return {
        'pearson': pearson_corr,
        'spearman': spearman_corr,
        'linear': z
    }

def generate_report_data(combined_data_by_period, correlations, z_values, current_pe):
    """生成报告所需的所有数据"""
    # 使用1年期数据计算PE的基本统计信息
    data_1y = combined_data_by_period[1]
    pe_low = data_1y['Forward_PE'].quantile(0.25)
    pe_high = data_1y['Forward_PE'].quantile(0.75)
    
    # 计算各期限的R²值和预期收益率
    r_squared_values = {}
    predicted_returns = {}
    
    for years in [1, 3, 5, 10, 20]:
        if years not in combined_data_by_period:
            continue
        period_data = combined_data_by_period[years]
        
        # 线性回归的R²
        y_pred = np.polyval(z_values[years]['linear'], period_data['Forward_PE'])
        y_actual = period_data[f'{years}Y_Returns']
        ss_res = np.sum((y_actual - y_pred) ** 2)
        ss_tot = np.sum((y_actual - y_actual.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        r_squared_values[years] = r_squared
        
        # 计算预期收益率
        predicted_returns[years] = np.polyval(z_values[years]['linear'], current_pe)
    
    # 计算PE的百分位数
    pe_percentile = stats.percentileofscore(data_1y['Forward_PE'], current_pe)
    
    # 计算各期限的低PE和高PE时期的平均收益率
    returns_data = {}
    for years in [5, 10, 20]:
        if years not in combined_data_by_period:
            continue
        period_data = combined_data_by_period[years]
        returns_when_low = period_data[period_data['Forward_PE'] < pe_low][f'{years}Y_Returns'].mean()
        returns_when_high = period_data[period_data['Forward_PE'] > pe_high][f'{years}Y_Returns'].mean()
        returns_data[f'returns_when_pe_low_{years}y'] = returns_when_low if not np.isnan(returns_when_low) else 0
        returns_data[f'returns_when_pe_high_{years}y'] = returns_when_high if not np.isnan(returns_when_high) else 0
        returns_data[f'returns_diff_{years}y'] = (returns_when_low - returns_when_high) if not (np.isnan(returns_when_low) or np.isnan(returns_when_high)) else 0
    
    # 准备返回数据
    report_data = {
        'current_pe': current_pe,
        'pe_percentile': pe_percentile,
        'pe_min': data_1y['Forward_PE'].min(),
        'pe_max': data_1y['Forward_PE'].max(),
        'pe_mean': data_1y['Forward_PE'].mean(),
        'pe_median': data_1y['Forward_PE'].median(),
        'pe_low': pe_low,
        'pe_high': pe_high
    }
    
    # 添加各期限的相关系数和回归方程
    for years in [1, 3, 5, 10, 20]:
        if years not in correlations:
            continue
        report_data[f'correlation_pearson_{years}y'] = correlations[years]['pearson']
        report_data[f'correlation_spearman_{years}y'] = correlations[years]['spearman']
        
        # 线性回归方程
        linear_coef = z_values[years]['linear']
        report_data[f'equation_linear_{years}y'] = f'y = {linear_coef[0]:.2f}x + {linear_coef[1]:.2f}'
        
        # R²值和预期收益率
        report_data[f'r_squared_{years}y'] = r_squared_values.get(years, 0)
        report_data[f'predicted_return_{years}y'] = predicted_returns.get(years, 0)
    
    # 添加收益率数据
    report_data.update(returns_data)
    
    return report_data

def main():
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    try:
        # 获取当前的 Forward PE
        print("正在获取当前市场 Forward PE...")
        current_forward_pe, current_trailing_pe = get_yfinance_forward_pe()
        if current_forward_pe:
            print(f"  当前 Forward PE: {current_forward_pe:.1f}")
        if current_trailing_pe:
            print(f"  当前 Trailing PE: {current_trailing_pe:.1f}")
        
        # 如果无法获取，使用估计值
        if not current_forward_pe:
            current_forward_pe = 21.0  # 使用合理的估计值
            print(f"  使用估计的 Forward PE: {current_forward_pe}")
        
        # 获取数据
        print("\n正在获取标普500数据...")
        sp500_data = get_sp500_data()
        
        print("\n正在获取Forward PE数据...")
        pe_data = get_forward_pe_data()
        
        # 统一时区
        if sp500_data.index.tz is not None:
            sp500_data.index = sp500_data.index.tz_localize(None)
        
        print(f"\n标普500数据范围：{sp500_data.index.min().strftime('%Y年%m月')} 至 {sp500_data.index.max().strftime('%Y年%m月')}")
        print(f"Forward PE数据范围：{pe_data.index.min().strftime('%Y年%m月')} 至 {pe_data.index.max().strftime('%Y年%m月')}")
        
        # 生成Forward PE与股价对比图
        print("\n正在生成Forward PE与股价对比图...")
        create_pe_price_comparison_plot(sp500_data, pe_data)
        
        # 计算不同时期的收益率并分别分析
        print("\n正在计算和分析各期收益率...")
        returns_data = {}
        combined_data_by_period = {}
        correlations = {}
        z_values = {}
        
        # 由于数据从1990年开始，20年期数据到2004年，所以不分析30年期
        for years in [1, 3, 5, 10, 20]:
            # 计算收益率
            returns_data[years] = calculate_returns(sp500_data, years)
            valid_data = returns_data[years].dropna()
            
            if len(valid_data) < 12:  # 至少需要12个数据点
                print(f"\n{years}年期分析: 数据点不足，跳过")
                continue
                
            print(f"\n{years}年期分析:")
            print(f"  数据范围：{valid_data.index.min().strftime('%Y年%m月')} 至 {valid_data.index.max().strftime('%Y年%m月')}")
            print(f"  数据点数量：{len(valid_data)}")
            
            # 为每个时期创建单独的组合数据
            period_data = pd.DataFrame({
                'Forward_PE': pe_data['Forward_PE'],
                f'{years}Y_Returns': returns_data[years]
            }).dropna()
            
            if len(period_data) < 12:
                print(f"  合并后数据点不足，跳过")
                continue
            
            combined_data_by_period[years] = period_data
            print(f"  合并后数据范围：{period_data.index.min().strftime('%Y年%m月')} 至 {period_data.index.max().strftime('%Y年%m月')}")
            print(f"  Forward PE范围：{period_data['Forward_PE'].min():.1f} - {period_data['Forward_PE'].max():.1f}")
            
            # 创建图表并获取相关系数和回归系数
            results = create_scatter_plot(period_data, years, current_forward_pe)
            correlations[years] = {
                'pearson': results['pearson'],
                'spearman': results['spearman']
            }
            z_values[years] = {
                'linear': results['linear']
            }
            print(f"  皮尔逊相关系数：{results['pearson']:.3f}")
            print(f"  斯皮尔曼相关系数：{results['spearman']:.3f}")
        
        # 生成报告数据
        print("\n正在生成报告...")
        report_data = generate_report_data(combined_data_by_period, correlations, z_values, current_forward_pe)
        
        # 添加各期限的数据范围信息
        for years in [1, 3, 5, 10, 20]:
            if years in combined_data_by_period:
                period_data = combined_data_by_period[years]
                report_data[f'period_{years}y_start'] = period_data.index.min().strftime('%Y年%m月')
                report_data[f'period_{years}y_end'] = period_data.index.max().strftime('%Y年%m月')
                report_data[f'period_{years}y_count'] = len(period_data)
        
        # 读取模板
        with open('forward_pe_report_template.md', 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 使用模板生成报告
        report = template.format(**report_data)
        
        # 保存报告
        with open('forward_pe_analysis_report.md', 'w', encoding='utf-8-sig') as f:
            f.write(report)
            
        print("\n分析完成！报告已保存为 forward_pe_analysis_report.md")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()

