import argparse

import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import tqdm


_SP500_TICKER = '^GSPC'
_NASDAQ_TICKER = '^IXIC'

_DCA = 100000
_TOTAL = 1000000

_FIELDS = ['date', 'yield', 'avg_yield']

_NUM_YEARS = [10, 20, 30]

def download_data(ticker):
    data = yf.download(ticker, start='1920-01-01', end=pd.to_datetime('today').strftime('%Y-%m-%d'))
    return data


def save_figure(df, title: str, file_name: str) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['avg_yield'], marker='o', linestyle='-', color='dodgerblue', label=title)
    plt.title(title)
    plt.xlabel('日期')
    plt.ylabel(f'年化收益')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.xticks(ticks=df.index[::5], rotation=45, fontsize=8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'{file_name}.png', format='png')
    plt.close()


def is_dca_date(day, index, df):
    if day == 15:
        return True
    if day > 15:
        return False
    if index + 1 < len(df) and df.iloc[index + 1]['Date'].day > 15:
        return True
    return False


def compute_avg_yield(total_invested, total_value, num_year):
    return ((total_value / total_invested) ** (1 / num_year) - 1) * 100


def simulate_dca(df, num_year):
    df = df.reset_index()
    result = pd.DataFrame(columns=_FIELDS)
    for outer_index, row in tqdm.tqdm(df.iterrows(), total=len(df)):
        end_date = row['Date'] + pd.DateOffset(years=num_year)
        end_result = df.loc[df['Date'] > end_date]
        if end_result.empty:
            break
        else:
            end_row = end_result.iloc[0]
        num_shares = 0
        total_invested = 0
        for inner_index in range(outer_index + 1, len(df), 22):
            inner_row = df.iloc[inner_index]
            investing = _DCA
            num_shares += investing / inner_row['Close']
            total_invested += investing
            if inner_row['Date'] > end_date:
                break
        total = num_shares * end_row['Close']
        if total_invested != 0:
            new_column = {
                'date': row['Date'], 'yield': total / total_invested, 'avg_yield': compute_avg_yield(total_invested, total, num_year)
            }
            result = pd.concat([result if not result.empty else None, pd.DataFrame([new_column])], ignore_index=True)
    result['date'] = pd.to_datetime(result['date'], format='%Y-%m')
    result['year'] = result['date'].dt.year
    grouped_result = result.groupby('year').mean()
    return grouped_result


def simulate_ls(df, num_year):
    result = pd.DataFrame(columns=_FIELDS)
    for index, row in tqdm.tqdm(df.iterrows(), total=len(df)):
        end_date = index + pd.DateOffset(years=num_year)
        end_result = df.loc[df.index > end_date]
        if end_result.empty:
            break
        else:
            end_row = end_result.iloc[0]
        num_shares = _TOTAL / row['Close']
        total = num_shares * end_row['Close']
        new_column = {
            'date': index, 'yield': total / _TOTAL, 'avg_yield': compute_avg_yield(_TOTAL, total, num_year)
        }
        result = pd.concat([result if not result.empty else None, pd.DataFrame([new_column])], ignore_index=True)
    result['date'] = pd.to_datetime(result['date'], format='%Y-%m')
    result = result.reset_index()
    result['year'] = result['date'].dt.year
    grouped_result = result.groupby('year').mean()
    return grouped_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--ticker', default=_SP500_TICKER)
    args = parser.parse_args()
    if args.ticker == _SP500_TICKER:
        prefix = 'sp500'
    else:
        prefix = 'nasdaq'
    df = download_data(args.ticker)
    stats = []
    for num_year in _NUM_YEARS:
        ls_result = simulate_ls(df, num_year)
        mean = ls_result['avg_yield'].mean()
        median = ls_result['avg_yield'].median()
        min = ls_result['avg_yield'].min()
        max = ls_result['avg_yield'].max()
        stats.append(f'ls, {num_year} years, mean yield: {mean:.2f}, median yield: {median:.2f}, min yield: {min:.2f}, max yield: {max:.2f}')
        save_figure(ls_result, f'{prefix} 梭哈 {num_year}年', f'{prefix}_ls_{num_year}')
        dca_result = simulate_dca(df, num_year)
        mean = dca_result['avg_yield'].mean()
        median = dca_result['avg_yield'].median()
        min = dca_result['avg_yield'].min()
        max = dca_result['avg_yield'].max()
        stats.append(f'dca, {num_year} years, mean yield: {mean:.2f}, median yield: {median:.2f}, min yield: {min:.2f}, max yield: {max:.2f}')
        save_figure(dca_result, f'{prefix} 定投 {num_year}年', f'{prefix}_dca_{num_year}')
    with open(f'stats_{prefix}.txt', 'w') as f:
        f.write('\n'.join(stats))


if __name__ == '__main__':
    main()