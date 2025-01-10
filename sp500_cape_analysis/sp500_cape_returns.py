import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import requests
import scipy.stats as stats

def get_sp500_data():
    # 获取标普500数据，从1974年开始
    sp500 = yf.download('^GSPC', start='1974-01-01')
    # 确保使用月末数据
    monthly_data = sp500['Close'].resample('ME').last()
    return monthly_data

def get_shiller_cape():
    # 从Robert Shiller的网站获取CAPE数据
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    df = pd.read_excel(url, sheet_name="Data", skiprows=7)
    df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y.%m')
    df = df[['Date', 'CAPE']]
    df.set_index('Date', inplace=True)
    # 确保使用月末数据
    df = df.resample('ME').last()
    return df

def calculate_returns(prices, years=10):
    """计算年化收益率"""
    returns = pd.Series(index=prices.index, dtype=float)
    for i in range(len(prices) - years*12):
        start_price = prices.iloc[i]
        end_price = prices.iloc[i + years*12]
        returns.iloc[i] = (end_price / start_price) ** (1/years) - 1
    return returns * 100  # 转换为百分比

def create_scatter_plot(combined_data, years, current_cape=37):
    """创建散点图和趋势线"""
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=combined_data, x='CAPE', y=f'{years}Y_Returns', alpha=0.6)
    
    # 添加趋势线
    z = np.polyfit(combined_data['CAPE'], combined_data[f'{years}Y_Returns'], 1)
    p = np.poly1d(z)
    plt.plot(combined_data['CAPE'], p(combined_data['CAPE']), "r--", alpha=0.8)
    
    # 计算相关系数
    correlation = combined_data['CAPE'].corr(combined_data[f'{years}Y_Returns'])
    
    # 添加当前CAPE的竖线
    plt.axvline(x=current_cape, color='r', linestyle='-', alpha=0.5)
    predicted_return = z[0] * current_cape + z[1]
    plt.plot([current_cape], [predicted_return], 'ro', markersize=10)
    
    # 在图表上添加信息
    equation = f'y = {z[0]:.2f}x + {z[1]:.2f}'
    correlation_text = f'相关系数 = {correlation:.2f}'
    current_cape_text = f'当前CAPE = {current_cape}\n预期收益率 = {predicted_return:.2f}%'
    plt.text(0.05, 0.95, equation + '\n' + correlation_text + '\n' + current_cape_text,
             transform=plt.gca().transAxes, 
             bbox=dict(facecolor='white', alpha=0.8))
    
    # 设置图表标题和标签
    plt.title(f'标普500席勒市盈率(CAPE)与未来{years}年年化收益率的关系\n' + 
             f'({combined_data.index.min().strftime("%Y年%m月")}-{combined_data.index.max().strftime("%Y年%m月")})')
    plt.xlabel('席勒市盈率(CAPE)')
    plt.ylabel(f'未来{years}年年化收益率(%)')
    
    # 添加网格
    plt.grid(True, alpha=0.3)
    
    # 保存图表
    plt.savefig(f'sp500_cape_returns_{years}y.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return correlation, z

def generate_report_data(combined_data, correlations, z_values):
    """生成报告所需的所有数据"""
    cape_low = combined_data['CAPE'].quantile(0.25)
    cape_high = combined_data['CAPE'].quantile(0.75)
    current_cape = 37
    
    # 计算各期限的R²值和预期收益率
    r_squared_values = {}
    predicted_returns = {}
    for years in [1, 3, 5, 10]:
        y_pred = np.polyval(z_values[years], combined_data['CAPE'])
        y_actual = combined_data[f'{years}Y_Returns']
        r_squared = 1 - (np.sum((y_actual - y_pred) ** 2) / np.sum((y_actual - y_actual.mean()) ** 2))
        r_squared_values[years] = r_squared
        predicted_returns[years] = z_values[years][0] * current_cape + z_values[years][1]
    
    # 计算CAPE的百分位数
    cape_percentile = stats.percentileofscore(combined_data['CAPE'], current_cape)
    
    return {
        'start_date': combined_data.index.min().strftime('%Y年%m月'),
        'end_date': combined_data.index.max().strftime('%Y年%m月'),
        'correlation_1y': correlations[1],
        'correlation_3y': correlations[3],
        'correlation_5y': correlations[5],
        'correlation_10y': correlations[10],
        'equation_1y': f'y = {z_values[1][0]:.2f}x + {z_values[1][1]:.2f}',
        'equation_3y': f'y = {z_values[3][0]:.2f}x + {z_values[3][1]:.2f}',
        'equation_5y': f'y = {z_values[5][0]:.2f}x + {z_values[5][1]:.2f}',
        'equation_10y': f'y = {z_values[10][0]:.2f}x + {z_values[10][1]:.2f}',
        'r_squared_1y': r_squared_values[1],
        'r_squared_3y': r_squared_values[3],
        'r_squared_5y': r_squared_values[5],
        'r_squared_10y': r_squared_values[10],
        'predicted_return_1y': predicted_returns[1],
        'predicted_return_3y': predicted_returns[3],
        'predicted_return_5y': predicted_returns[5],
        'predicted_return_10y': predicted_returns[10],
        'cape_percentile': cape_percentile,
        'cape_min': combined_data['CAPE'].min(),
        'cape_max': combined_data['CAPE'].max(),
        'cape_mean': combined_data['CAPE'].mean(),
        'cape_median': combined_data['CAPE'].median(),
        'cape_low': cape_low,
        'cape_high': cape_high,
        'returns_when_cape_low_10y': combined_data[combined_data['CAPE'] < cape_low]['10Y_Returns'].mean(),
        'returns_when_cape_high_10y': combined_data[combined_data['CAPE'] > cape_high]['10Y_Returns'].mean()
    }

def main():
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 获取数据
    sp500_data = get_sp500_data()
    cape_data = get_shiller_cape()
    
    # 计算不同时期的收益率
    returns_data = {}
    for years in [1, 3, 5, 10]:
        returns_data[years] = calculate_returns(sp500_data, years)
    
    # 合并数据
    combined_data = pd.DataFrame({
        'CAPE': cape_data['CAPE'],
        '1Y_Returns': returns_data[1],
        '3Y_Returns': returns_data[3],
        '5Y_Returns': returns_data[5],
        '10Y_Returns': returns_data[10]
    })
    
    # 删除任何包含NaN的行
    combined_data = combined_data.dropna()
    
    # 创建所有时期的图表并获取相关系数和趋势线参数
    correlations = {}
    z_values = {}
    for years in [1, 3, 5, 10]:
        correlation, z = create_scatter_plot(combined_data, years)
        correlations[years] = correlation
        z_values[years] = z
    
    # 生成报告数据
    report_data = generate_report_data(combined_data, correlations, z_values)
    
    # 读取模板
    with open('report_template.md', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 使用模板生成报告
    report = template.format(**report_data)
    
    # 保存报告
    with open('analysis_report.md', 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    main() 