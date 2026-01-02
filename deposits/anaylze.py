import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
import akshare as ak


def get_money_supply_data() -> pd.DataFrame:
    """从AKShare获取货币供应量数据"""
    print('正在获取货币供应量数据...')
    df = ak.macro_china_money_supply()

    # 数据是倒序的，反转一下
    df = df.iloc[::-1].reset_index(drop=True)

    # 重命名列
    df.columns = ['date', 'M2', 'M2_yoy', 'M2_mom', 'M1', 'M1_yoy', 'M1_mom', 'M0', 'M0_yoy', 'M0_mom']

    # 解析日期
    df['date'] = pd.to_datetime(df['date'], format='%Y年%m月份')

    # 只保留需要的列
    df = df[['date', 'M0', 'M1', 'M2', 'M0_yoy', 'M1_yoy', 'M2_yoy']]

    return df


def calculate_derived_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """计算派生指标"""
    # 从2025年1月起，M1包括：M0 + 单位活期存款 + 个人活期存款 + 非银行支付机构客户备付金
    # 所以 单位活期存款（近似）= M1 - M0
    data['enterprise'] = data['M1'] - data['M0']

    # 计算同比增长率
    data['enterprise_yoy'] = data['enterprise'].pct_change(periods=12, fill_method=None) * 100
    data['enterprise_yoy'] = data['enterprise_yoy'].map(lambda x: f'{x:.2f}%' if pd.notna(x) else 'nan%')

    # 格式化同比增长率
    data['M0_yoy_formatted'] = data['M0_yoy'].map(lambda x: f'{x:.2f}%' if pd.notna(x) else 'nan%')
    data['M1_yoy_formatted'] = data['M1_yoy'].map(lambda x: f'{x:.2f}%' if pd.notna(x) else 'nan%')
    data['M2_yoy_formatted'] = data['M2_yoy'].map(lambda x: f'{x:.2f}%' if pd.notna(x) else 'nan%')

    return data


def save_figure(index, data, title: str, file_name: str = None) -> None:
    """保存图表"""
    if not file_name:
        file_name = title
    plt.figure(figsize=(10, 6))
    plt.plot(index, data, marker='o', linestyle='-', color='dodgerblue', label=title)
    plt.title(title)
    plt.xlabel('日期')
    plt.ylabel(f'{title}(亿元)')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.xticks(rotation=45, fontsize=8)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'{file_name}.png', format='png')
    plt.close()


def generate_markdown(df):
    """生成Markdown文档"""
    # df已经是重命名后的，所以使用新的列名
    first_col = df.columns[0]
    df_cleaned = df.dropna(subset=[first_col])
    df_sorted = df_cleaned.sort_index(ascending=False)
    markdown_table = tabulate(df_sorted, headers='keys', tablefmt='pipe', stralign='left', numalign='left')
    with open('README.tpl', 'r', encoding='utf-8') as readme_file:
        readme_content = readme_file.read()
    merged_content = readme_content.replace('<!--TABLE_MARKER-->', markdown_table)
    with open('README.md', 'w', encoding='utf-8') as readme_file:
        readme_file.write(merged_content)


def main():
    # 获取数据
    df = get_money_supply_data()

    # 计算派生指标
    df = calculate_derived_metrics(df)

    # 设置日期为索引
    df.set_index('date', inplace=True)

    # 生成图表
    print('正在生成图表...')
    save_figure(df.index, df['M0'], 'M0（流通中货币）', 'M0')
    save_figure(df.index, df['M1'], 'M1（狭义货币）', 'M1')
    save_figure(df.index, df['M2'], 'M2（广义货币）', 'M2')
    save_figure(df.index, df['enterprise'], '单位活期存款（M1-M0）', '单位活期存款')

    # 准备输出数据
    output_df = df.copy()
    output_df.index.name = '日期'
    output_df.index = output_df.index.strftime('%Y-%m')

    # 重命名列以便输出
    output_df.rename(columns={
        'M0': 'M0(亿元)',
        'M1': 'M1(亿元)',
        'M2': 'M2(亿元)',
        'M0_yoy': 'M0同比(%)',
        'M1_yoy': 'M1同比(%)',
        'M2_yoy': 'M2同比(%)',
        'enterprise': '单位活期存款(亿元)',
        'enterprise_yoy': '单位活期同比',
        'M0_yoy_formatted': 'M0同比',
        'M1_yoy_formatted': 'M1同比',
        'M2_yoy_formatted': 'M2同比'
    }, inplace=True)

    # 选择要保存的列
    columns_to_save = ['M0(亿元)', 'M1(亿元)', 'M2(亿元)', 'M0同比', 'M1同比', 'M2同比', '单位活期存款(亿元)', '单位活期同比']
    output_df = output_df[columns_to_save]

    # 保存CSV
    print('正在保存数据...')
    output_df.to_csv('result.csv', float_format='%.2f')

    # 生成Markdown
    print('正在生成README...')
    generate_markdown(output_df)

    print('数据更新完成!')
    print(f'数据范围: {output_df.index[0]} 到 {output_df.index[-1]}')
    print(f'总共 {len(output_df)} 条记录')


if __name__ == '__main__':
    main()
