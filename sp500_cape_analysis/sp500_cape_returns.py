import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import scipy.stats as stats
from statsmodels.nonparametric.smoothers_lowess import lowess
import os

def get_sp500_data():
    """获取标普500数据，从1974年开始到现在"""
    try:
        sp500 = yf.download('^GSPC', start='1974-01-01', end=None)  # end=None 表示获取到最新数据
        if sp500.empty:
            raise Exception("获取标普500数据失败")
        # 确保使用月末数据
        monthly_data = sp500['Close'].resample('ME').last()
        return monthly_data
    except Exception as e:
        print(f"获取标普500数据时出错: {str(e)}")
        raise

def get_shiller_cape():
    """从Robert Shiller的网站获取CAPE数据"""
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    
    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用requests下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # 检查是否成功
            
            # 将内容保存到临时文件
            with open('temp_shiller_data.xls', 'wb') as f:
                f.write(response.content)
            
            # 读取Excel文件
            df = pd.read_excel('temp_shiller_data.xls', sheet_name="Data", skiprows=7)
            if df.empty:
                raise Exception("CAPE数据为空")
                
            df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y.%m')
            df = df[['Date', 'CAPE']]
            df.set_index('Date', inplace=True)
            
            # 确保使用月末数据
            df = df.resample('ME').last()
            
            # 删除临时文件
            os.remove('temp_shiller_data.xls')
            
            if df.empty:
                raise Exception("处理后的CAPE数据为空")
            
            # 只保留1974年之后的数据
            df = df['1974':]
            
            return df
            
        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
            if attempt == max_retries - 1:
                print("无法获取Shiller CAPE数据，使用备用数据源...")
                raise Exception("无法获取CAPE数据，请检查网络连接或使用本地数据文件")

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

def create_scatter_plot(combined_data, years, current_cape=37):
    """创建散点图和拟合线"""
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=combined_data, x='CAPE', y=f'{years}Y_Returns', alpha=0.6)
    
    # 计算皮尔逊和斯皮尔曼相关系数
    pearson_corr = combined_data['CAPE'].corr(combined_data[f'{years}Y_Returns'])
    spearman_corr = combined_data['CAPE'].corr(combined_data[f'{years}Y_Returns'], method='spearman')
    
    # 线性回归
    z = np.polyfit(combined_data['CAPE'], combined_data[f'{years}Y_Returns'], 1)
    p = np.poly1d(z)
    plt.plot(combined_data['CAPE'], p(combined_data['CAPE']), "r--", alpha=0.8, label='线性回归')
    
    # LOWESS平滑
    lowess_result = lowess(combined_data[f'{years}Y_Returns'], combined_data['CAPE'], 
                          frac=0.3, it=3, return_sorted=True)
    plt.plot(lowess_result[:, 0], lowess_result[:, 1], 'b--', alpha=0.8, label='LOWESS平滑')
    
    # 添加当前CAPE的竖线
    plt.axvline(x=current_cape, color='r', linestyle='-', alpha=0.5)
    predicted_return = z[0] * current_cape + z[1]
    plt.plot([current_cape], [predicted_return], 'ro', markersize=10)
    
    # 在图表上添加信息
    equation = f'线性: y = {z[0]:.2f}x + {z[1]:.2f}'
    correlation_text = f'皮尔逊相关系数 = {pearson_corr:.2f}\n斯皮尔曼相关系数 = {spearman_corr:.2f}'
    current_cape_text = f'当前CAPE = {current_cape}\n预期收益率 = {predicted_return:.2f}%'
    
    plt.text(0.05, 0.95, equation + '\n' + correlation_text + '\n' + current_cape_text,
             transform=plt.gca().transAxes, 
             bbox=dict(facecolor='white', alpha=0.8))
    
    # 设置图表标题和标签
    plt.title(f'标普500席勒市盈率(CAPE)与未来{years}年年化收益率的关系\n' + 
             f'({combined_data.index.min().strftime("%Y年%m月")}-{combined_data.index.max().strftime("%Y年%m月")})')
    plt.xlabel('席勒市盈率(CAPE)')
    plt.ylabel(f'未来{years}年年化收益率(%)')
    
    # 添加图例
    plt.legend()
    
    # 添加网格
    plt.grid(True, alpha=0.3)
    
    # 保存图表
    plt.savefig(f'sp500_cape_returns_{years}y.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return {
        'pearson': pearson_corr,
        'spearman': spearman_corr,
        'linear': z
    }

def generate_report_data(combined_data_by_period, correlations, z_values):
    """生成报告所需的所有数据"""
    # 使用1年期数据计算CAPE的基本统计信息
    data_1y = combined_data_by_period[1]
    cape_low = data_1y['CAPE'].quantile(0.25)
    cape_high = data_1y['CAPE'].quantile(0.75)
    current_cape = 37
    
    # 计算各期限的R²值和预期收益率
    r_squared_values = {}
    predicted_returns = {}
    
    for years in [1, 3, 5, 10, 20, 30]:
        period_data = combined_data_by_period[years]
        
        # 线性回归的R²
        y_pred = np.polyval(z_values[years]['linear'], period_data['CAPE'])
        y_actual = period_data[f'{years}Y_Returns']
        r_squared = 1 - (np.sum((y_actual - y_pred) ** 2) / np.sum((y_actual - y_actual.mean()) ** 2))
        r_squared_values[years] = r_squared
        
        # 计算预期收益率
        predicted_returns[years] = np.polyval(z_values[years]['linear'], current_cape)
    
    # 计算CAPE的百分位数
    cape_percentile = stats.percentileofscore(data_1y['CAPE'], current_cape)
    
    # 计算各期限的低CAPE和高CAPE时期的平均收益率
    returns_data = {}
    for years in [10, 20, 30]:
        period_data = combined_data_by_period[years]
        returns_when_low = period_data[period_data['CAPE'] < cape_low][f'{years}Y_Returns'].mean()
        returns_when_high = period_data[period_data['CAPE'] > cape_high][f'{years}Y_Returns'].mean()
        returns_data[f'returns_when_cape_low_{years}y'] = returns_when_low
        returns_data[f'returns_when_cape_high_{years}y'] = returns_when_high
        returns_data[f'returns_diff_{years}y'] = returns_when_low - returns_when_high
    
    # 准备返回数据
    report_data = {
        'cape_percentile': cape_percentile,
        'cape_min': data_1y['CAPE'].min(),
        'cape_max': data_1y['CAPE'].max(),
        'cape_mean': data_1y['CAPE'].mean(),
        'cape_median': data_1y['CAPE'].median(),
        'cape_low': cape_low,
        'cape_high': cape_high
    }
    
    # 添加各期限的相关系数和回归方程
    for years in [1, 3, 5, 10, 20, 30]:
        report_data[f'correlation_pearson_{years}y'] = correlations[years]['pearson']
        report_data[f'correlation_spearman_{years}y'] = correlations[years]['spearman']
        
        # 线性回归方程
        linear_coef = z_values[years]['linear']
        report_data[f'equation_linear_{years}y'] = f'y = {linear_coef[0]:.2f}x + {linear_coef[1]:.2f}'
        
        # R²值和预期收益率
        report_data[f'r_squared_{years}y'] = r_squared_values[years]
        report_data[f'predicted_return_{years}y'] = predicted_returns[years]
    
    # 添加收益率数据
    report_data.update(returns_data)
    
    return report_data

def main():
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    try:
        # 获取数据
        print("正在获取标普500数据...")
        sp500_data = get_sp500_data()
        print("正在获取CAPE数据...")
        cape_data = get_shiller_cape()
        
        print(f"标普500数据范围：{sp500_data.index.min().strftime('%Y年%m月')} 至 {sp500_data.index.max().strftime('%Y年%m月')}")
        print(f"CAPE数据范围：{cape_data.index.min().strftime('%Y年%m月')} 至 {cape_data.index.max().strftime('%Y年%m月')}")
        
        # 计算不同时期的收益率并分别分析
        print("\n正在计算和分析各期收益率...")
        returns_data = {}
        combined_data_by_period = {}
        correlations = {}
        z_values = {}
        
        for years in [1, 3, 5, 10, 20, 30]:
            # 计算收益率
            returns_data[years] = calculate_returns(sp500_data, years)
            valid_data = returns_data[years].dropna()
            print(f"\n{years}年期分析:")
            print(f"  数据范围：{valid_data.index.min().strftime('%Y年%m月')} 至 {valid_data.index.max().strftime('%Y年%m月')}")
            print(f"  数据点数量：{len(valid_data)}")
            
            # 为每个时期创建单独的组合数据
            period_data = pd.DataFrame({
                'CAPE': cape_data['CAPE'],
                f'{years}Y_Returns': returns_data[years]
            }).dropna()
            
            combined_data_by_period[years] = period_data
            print(f"  合并后数据范围：{period_data.index.min().strftime('%Y年%m月')} 至 {period_data.index.max().strftime('%Y年%m月')}")
            print(f"  CAPE范围：{period_data['CAPE'].min():.1f} - {period_data['CAPE'].max():.1f}")
            
            # 创建图表并获取相关系数和回归系数
            results = create_scatter_plot(period_data, years)
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
        report_data = generate_report_data(combined_data_by_period, correlations, z_values)
        
        # 添加各期限的数据范围信息
        for years in [1, 3, 5, 10, 20, 30]:
            period_data = combined_data_by_period[years]
            report_data[f'period_{years}y_start'] = period_data.index.min().strftime('%Y年%m月')
            report_data[f'period_{years}y_end'] = period_data.index.max().strftime('%Y年%m月')
            report_data[f'period_{years}y_count'] = len(period_data)
        
        # 读取模板
        with open('report_template.md', 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 使用模板生成报告
        report = template.format(**report_data)
        
        # 保存报告，使用UTF-8-SIG编码（带BOM）
        with open('analysis_report.md', 'w', encoding='utf-8-sig') as f:
            f.write(report)
            
        print("\n分析完成！报告已保存为 analysis_report.md")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main() 