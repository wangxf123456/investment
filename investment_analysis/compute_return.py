import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_historical_metrics(ticker, etf_ticker=None, start_year=None, include_dividends=True):
    """计算历史年化回报率和波动率，可选使用ETF的股息率"""
    try:
        # 获取指数数据
        index = yf.Ticker(ticker)
        hist = index.history(period="max")
        
        # 如果指定了ETF，获取其股息率
        if etf_ticker:
            etf = yf.Ticker(etf_ticker)
            etf_hist = etf.history(period="max")
            etf_hist['Dividends'] = etf_hist['Dividends'].fillna(0)
            annual_dividends = etf_hist['Dividends'].resample('YE').sum()
            annual_prices = etf_hist['Close'].resample('YE').last()
            dividend_yields = annual_dividends / annual_prices
            avg_dividend_yield = dividend_yields.mean()
        else:
            # 使用指数自身的股息数据
            hist['Dividends'] = hist['Dividends'].fillna(0)
            annual_dividends = hist['Dividends'].resample('YE').sum()
            annual_prices = hist['Close'].resample('YE').last()
            dividend_yields = annual_dividends / annual_prices
            avg_dividend_yield = dividend_yields.mean()
        
        # 如果指定了起始年份，只使用该年份之后的数据
        if start_year:
            hist = hist[hist.index.year >= start_year]
        
        # 计算基本价格回报
        hist['Price_Return'] = hist['Close'].pct_change().fillna(0)
        
        if include_dividends:
            # 计算包含股息的总回报（使用平均股息率）
            if etf_ticker:
                # 使用ETF的平均股息率，按年计算复利
                annual_price_returns = (1 + hist['Price_Return']).resample('YE').prod() - 1
                annual_total_returns = (1 + annual_price_returns) * (1 + avg_dividend_yield) - 1
            else:
                # 使用实际股息数据
                hist['Total_Return'] = hist['Price_Return'] + hist['Dividends'] / hist['Close'].shift(1)
                annual_total_returns = (1 + hist['Total_Return']).resample('YE').prod() - 1
        else:
            # 仅计算价格变化
            annual_total_returns = (1 + hist['Price_Return']).resample('YE').prod() - 1
        
        # 计算年化回报率和波动率
        annual_return = (1 + annual_total_returns).prod() ** (1/len(annual_total_returns)) - 1
        annual_std = annual_total_returns.std()
        
        dividend_str = "含股息再投资" if include_dividends else "不含股息"
        etf_str = f"(使用{etf_ticker}的股息率)" if etf_ticker and include_dividends else ""
        print(f"\n{ticker} 历史数据分析（{dividend_str}）{etf_str}:")
        print(f"数据年份范围: {hist.index[0].year} - {hist.index[-1].year}")
        print(f"总年数: {len(annual_total_returns)}")
        print(f"年化总回报率: {annual_return*100:.1f}%")
        print(f"年度波动率: {annual_std*100:.1f}%")
        print(f"平均股息收益率: {avg_dividend_yield*100:.2f}%")
        print(f"年度总回报率分布:")
        print(annual_total_returns.describe())
        print("\n各个十年的平均总回报率:")
        
        # 计算每个十年的平均回报率
        for decade_start in range(hist.index[0].year // 10 * 10, 
                                hist.index[-1].year // 10 * 10, 10):
            decade_end = decade_start + 9
            decade_data = annual_total_returns[
                (annual_total_returns.index.year >= decade_start) & 
                (annual_total_returns.index.year <= decade_end)
            ]
            if not decade_data.empty:
                decade_return = (1 + decade_data).prod() ** (1/len(decade_data)) - 1
                print(f"{decade_start}s: {decade_return*100:.1f}%")
        
        return annual_return, annual_std, avg_dividend_yield
        
    except Exception as e:
        print(f"获取{ticker}数据时出错: {e}")
        return None, None, None

def main():
    # 计算含股息的回报率
    print("\n计算历史回报率和波动率（含股息再投资）...")
    
    # 使用标普500指数的50年数据，但使用VOO的股息率
    print("\n获取标普500指数50年数据（使用VOO的股息率）...")
    SP500_RETURN, SP500_STD, SP500_DIV = calculate_historical_metrics("^GSPC", "VOO", 1974, include_dividends=True)
    
    # 使用纳斯达克100指数的50年数据，但使用QQQ的股息率
    print("\n获取纳斯达克100指数50年数据（使用QQQ的股息率）...")
    NDX_RETURN, NDX_STD, NDX_DIV = calculate_historical_metrics("^NDX", "QQQ", 1974, include_dividends=True)
    
    # 计算不含股息的回报率
    print("\n计算历史回报率和波动率（不含股息）...")
    
    print("\n获取标普500指数50年数据...")
    SP500_RETURN_NO_DIV, SP500_STD_NO_DIV, _ = calculate_historical_metrics("^GSPC", start_year=1974, include_dividends=False)
    
    print("\n获取纳斯达克100指数50年数据...")
    NDX_RETURN_NO_DIV, NDX_STD_NO_DIV, _ = calculate_historical_metrics("^NDX", start_year=1974, include_dividends=False)
    
    print("\n总结（50年历史数据）：")
    print(f"标普500含股息年化回报率: {SP500_RETURN*100:.1f}%, 波动率: {SP500_STD*100:.1f}%, 平均股息率: {SP500_DIV*100:.2f}%")
    print(f"标普500不含股息年化回报率: {SP500_RETURN_NO_DIV*100:.1f}%, 波动率: {SP500_STD_NO_DIV*100:.1f}%")
    print(f"纳斯达克100含股息年化回报率: {NDX_RETURN*100:.1f}%, 波动率: {NDX_STD*100:.1f}%, 平均股息率: {NDX_DIV*100:.2f}%")
    print(f"纳斯达克100不含股息年化回报率: {NDX_RETURN_NO_DIV*100:.1f}%, 波动率: {NDX_STD_NO_DIV*100:.1f}%")

if __name__ == "__main__":
    main() 