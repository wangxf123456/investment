import io
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from tabulate import tabulate
import tqdm
from typing import Any, Dict, List, Optional, Union


_HOUSEHOLD_URL_2015 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2016/02/2016021816165233170.xls'
_HOUSEHOLD_URL_2016 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2017/02/2017020816484686050.xls'
_HOUSEHOLD_URL_2017 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2018/01/2018011616214550177.xls'
_HOUSEHOLD_URL_2018 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2019/02/2019020116022672266.xls'
_HOUSEHOLD_URL_2019 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2020/01/2020011915320918338.xls'
_HOUSEHOLD_URL_2020 = 'http://www.pbc.gov.cn/eportal/fileDir/defaultCurSite/resource/cms/2021/01/2021011909493056248.xls'
_HOUSEHOLD_URL_2021 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2022/01/2022011915585996443.xlsx'
_HOUSEHOLD_URL_2022 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/01/2023011817001029444.xls'
_HOUSEHOLD_URL_2023 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2024/01/2024011714311938329.xlsx'
_HOUSEHOLD_URL_2024 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2024/11/2024111417055388147.xlsx'
_ENTERPRISE_URL_2015 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304735226.xls'
_ENTERPRISE_URL_2016 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304755177.xls'
_ENTERPRISE_URL_2017 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304771269.xls'
_ENTERPRISE_URL_2018 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304726945.xls'
_ENTERPRISE_URL_2019 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304759964.xls'
_ENTERPRISE_URL_2020 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304733431.xls'
_ENTERPRISE_URL_2021 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304711200.xls'
_ENTERPRISE_URL_2022 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2023/02/2023022414304762017.xls'
_ENTERPRISE_URL_2023 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2024/01/2024011714335851539.xlsx'
_ENTERPRISE_URL_2024 = 'http://www.pbc.gov.cn/diaochatongjisi/resource/cms/2024/11/2024111417105027190.xlsx'

_BASE_YEAR = 2015
_ALL_DATA_HOUSEHOLD = [_HOUSEHOLD_URL_2015, _HOUSEHOLD_URL_2016, _HOUSEHOLD_URL_2017, _HOUSEHOLD_URL_2018, _HOUSEHOLD_URL_2019,
                       _HOUSEHOLD_URL_2020, _HOUSEHOLD_URL_2021, _HOUSEHOLD_URL_2022, _HOUSEHOLD_URL_2023, _HOUSEHOLD_URL_2024]
_ALL_DATA_ENTERPRISE = [_ENTERPRISE_URL_2015, _ENTERPRISE_URL_2016, _ENTERPRISE_URL_2017, _ENTERPRISE_URL_2018, _ENTERPRISE_URL_2019,
                        _ENTERPRISE_URL_2020, _ENTERPRISE_URL_2021, _ENTERPRISE_URL_2022, _ENTERPRISE_URL_2023, _ENTERPRISE_URL_2024]

_HOUSEHOLD_ROW_NUMBER = 10
_ENTERPRISE_ROW_NUMBER = 14


def process_deposit_data(deposit: Union[str, float]) -> float:
    if isinstance(deposit, str):
        return float(deposit.replace(u'\xa0', u' ').strip())
    else:
        return deposit


def get_row_numer(base_row_number, year, column_name):
    if column_name == 'enterprise':
        return base_row_number if year != 2022 else base_row_number - 1
    else:
        return base_row_number if year != 2022 else base_row_number + 1


def process_data(url_list, base_row_number, column_name) -> pd.DataFrame:
    result_dict = {
        'date': [], column_name: [],
    }
    for idx, url in enumerate(tqdm.tqdm(url_list, desc=f'Processing {column_name}')):
        xls_content = fetch_data(url)
        if xls_content:
            xls_file_obj = io.BytesIO(xls_content)
            data = pd.read_excel(xls_file_obj)
            year = _BASE_YEAR + idx
            row_number = get_row_numer(base_row_number, year, column_name)
            for month, deposit in enumerate(data.iloc[row_number][1:]):
                date = f'{_BASE_YEAR + idx}-{month + 1}'
                result_dict['date'].append(date)
                result_dict[column_name].append(process_deposit_data(deposit))
                if column_name == 'enterprise':
                    m0 = data.iloc[row_number - 1][1:]
                    if not result_dict.get('m0'):
                        result_dict['m0'] = []
                    result_dict['m0'].append(process_deposit_data(m0.iloc[month]))
        else:
            print(f"Failed to retrieve data from {url}")
            continue
    result = pd.DataFrame(result_dict)
    return result


def fetch_data(url: str) -> Optional[str]:
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.status_code == 200:
        return response.content
    else:
        return None


def calculate_year_on_year_changes(data: pd.DataFrame) -> pd.DataFrame:
    data['household_yoy'] = data['household'].pct_change(periods=12, fill_method=None) * 100
    data['household_yoy'] = data['household_yoy'].map('{:.2f}%'.format)
    data['enterprise_yoy'] = data['enterprise'].pct_change(periods=12, fill_method=None) * 100
    data['enterprise_yoy'] = data['enterprise_yoy'].map('{:.2f}%'.format)
    data['m0_yoy'] = data['m0'].pct_change(periods=12, fill_method=None) * 100
    data['m0_yoy'] = data['m0_yoy'].map('{:.2f}%'.format)
    data['household_enterprise'] = data['household'] + data['enterprise']
    data['household_enterprise_yoy'] = data['household_enterprise'].pct_change(periods=12, fill_method=None) * 100
    data['household_enterprise_yoy'] = data['household_enterprise_yoy'].map('{:.2f}%'.format)
    data['m1'] = data['enterprise'] + data['m0']
    data['m1_yoy'] = data['m1'].pct_change(periods=12, fill_method=None) * 100
    data['m1_yoy'] = data['m1_yoy'].map('{:.2f}%'.format)
    data['total'] = data['household_enterprise'] + data['m0']
    data['total_yoy'] = data['total'].pct_change(periods=12, fill_method=None) * 100
    data['total_yoy'] = data['total_yoy'].map('{:.2f}%'.format)
    return data


def save_figure(index, data, title: str, file_name: str = None) -> None:
    if not file_name:
        file_name = title
    plt.figure(figsize=(10, 6))
    plt.plot(index, data, marker='o', linestyle='-', color='dodgerblue', label=title)
    plt.title(title)
    plt.xlabel('日期')
    plt.ylabel(f'{title}(亿)')
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
    df_cleaned = df.dropna(subset=['个人活期存款'])
    df_sorted = df_cleaned.sort_index(ascending=False)
    markdown_table = tabulate(df_sorted, headers='keys', tablefmt='pipe', stralign='left', numalign='left')
    with open('README.tpl', 'r', encoding='utf-8') as readme_file:
        readme_content = readme_file.read()
    merged_content = readme_content.replace('<!--TABLE_MARKER-->', markdown_table)
    with open('README.md', 'w', encoding='utf-8') as readme_file:
        readme_file.write(merged_content)


def main():
    df_household = process_data(_ALL_DATA_HOUSEHOLD, _HOUSEHOLD_ROW_NUMBER, 'household')
    df_enterprise = process_data(_ALL_DATA_ENTERPRISE, _ENTERPRISE_ROW_NUMBER, 'enterprise')
    df = pd.merge(df_household, df_enterprise, on='date')
    df = calculate_year_on_year_changes(df)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df.set_index('date', inplace=True)
    save_figure(df.index, df['household'], '个人活期存款')
    save_figure(df.index, df['enterprise'], '企业活期存款')
    save_figure(df.index, df['household_enterprise'], '企业活期存款 + 个人活期存款', '企业活期存款_个人活期存款')
    save_figure(df.index, df['m1'], 'M1', 'M1')
    save_figure(df.index, df['total'], '企业活期存款 + 个人活期存款 + M0', '企业活期存款_个人活期存款_M0')
    df.rename(columns={'household': '个人活期存款', 'enterprise': '单位活期存款', 'household_yoy':
                       '个人活期同比', 'enterprise_yoy': '单位活期同比', 'total': '单位个人M0合计',
                       'total_yoy': '单位个人M0合计同比', 'household_enterprise': '单位个人合计',
                       'household_enterprise_yoy': '单位个人合计同比'}, inplace=True)
    df.index.name = '日期'
    df.index = df.index.strftime('%Y-%m')
    df.to_csv('result.csv', float_format='%.2f')
    generate_markdown(df)


if __name__ == '__main__':
    main()
