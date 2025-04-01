import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取债务数据
debt_data = pd.read_csv('GFDEBTN.csv')
debt_data['observation_date'] = pd.to_datetime(debt_data['observation_date'])
debt_data.set_index('observation_date', inplace=True)

# 债务数据是百万美元，转换为万亿美元以便更好显示
debt_data['GFDEBTN_Trillion'] = debt_data['GFDEBTN'] / 1000000

# 读取金价数据
gold_data = pd.read_csv('gold_price_data.csv')
gold_data['date'] = pd.to_datetime(gold_data['date'])
gold_data.set_index('date', inplace=True)
gold_data.columns = ['Gold_Price']

# 合并数据
combined_data = pd.concat([debt_data, gold_data], axis=1)
combined_data = combined_data.dropna()

# 计算债务/金价比率
combined_data['Debt_Gold_Ratio'] = combined_data['GFDEBTN'] / combined_data['Gold_Price']

# 创建图表
plt.figure(figsize=(15, 10))

# 绘制债务/金价比率趋势
plt.subplot(2, 1, 1)
plt.plot(combined_data.index, combined_data['Debt_Gold_Ratio'], color='blue')
plt.title('美国债务/金价比率趋势 (1970-2025)')
plt.xlabel('年份')
plt.ylabel('债务/金价比率')
plt.grid(True)

# 添加垂直线标记重要时间点
key_years = [1980, 2000, 2008, 2020, 2024]
for year in key_years:
    plt.axvline(x=pd.to_datetime(f'{year}-01-01'), color='gray', linestyle='--', alpha=0.7)

# 绘制原始数据对比
plt.subplot(2, 1, 2)
ax1 = plt.gca()
ax2 = ax1.twinx()

ax1.plot(combined_data.index, combined_data['GFDEBTN_Trillion'], color='red', label='美国债务')
ax2.plot(combined_data.index, combined_data['Gold_Price'], color='gold', label='金价')

# 设置适当的刻度
years = np.arange(1970, 2030, 10)
ax1.set_xticks([pd.to_datetime(f'{year}-01-01') for year in years])
ax1.set_xticklabels(years)

ax1.set_xlabel('年份')
ax1.set_ylabel('美国债务 (万亿美元)', color='red')
ax2.set_ylabel('金价 (美元/盎司)', color='gold')

plt.title('美国债务与金价对比 (1970-2025)')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
plt.grid(True)

plt.tight_layout()
plt.savefig('gold_debt_analysis.png', dpi=300)  # 提高分辨率
plt.close()

# 计算一些统计指标
# 使用金价数据的最后一个可用日期
gold_last_date = gold_data.index[-1]
gold_first_date = combined_data.index[0]

# 找到最接近的债务数据点
nearest_debt_last = debt_data.index[debt_data.index <= gold_last_date][-1]
nearest_debt_first = combined_data.index[0]

stats = {
    '起始年份': gold_first_date.year,
    '结束年份': gold_last_date.year,
    '起始债务(十亿美元)': debt_data.loc[nearest_debt_first, 'GFDEBTN'] / 1000,
    '结束债务(万亿美元)': debt_data.loc[nearest_debt_last, 'GFDEBTN'] / 1000000,
    '起始金价(美元/盎司)': gold_data.loc[gold_first_date, 'Gold_Price'],
    '结束金价(美元/盎司)': gold_data.loc[gold_last_date, 'Gold_Price'],
    '债务增长倍数': debt_data.loc[nearest_debt_last, 'GFDEBTN'] / debt_data.loc[nearest_debt_first, 'GFDEBTN'],
    '金价增长倍数': gold_data.loc[gold_last_date, 'Gold_Price'] / gold_data.loc[gold_first_date, 'Gold_Price'],
    '债务/金价比率变化': (debt_data.loc[nearest_debt_last, 'GFDEBTN'] / gold_data.loc[gold_last_date, 'Gold_Price']) / 
                    (debt_data.loc[nearest_debt_first, 'GFDEBTN'] / gold_data.loc[gold_first_date, 'Gold_Price']),
    '最大债务/金价比率': combined_data['Debt_Gold_Ratio'].max(),
    '最小债务/金价比率': combined_data['Debt_Gold_Ratio'].min(),
    '平均债务/金价比率': combined_data['Debt_Gold_Ratio'].mean()
}

# 保存统计结果
with open('analysis_stats.txt', 'w', encoding='utf-8') as f:
    for key, value in stats.items():
        f.write(f'{key}: {value:.2f}\n') 