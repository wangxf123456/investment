#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
期权链数据下载脚本
下载NVDA、QQQ、IBIT的期权链数据，包括Greeks、波动率等信息
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
import json

# 创建数据目录
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

# 需要分析的标的列表
TICKERS = ["NVDA", "QQQ", "IBIT"]

def calculate_historical_volatility(stock, periods=[10, 20, 30, 60]):
    """
    计算历史波动率 (HV - Historical Volatility)
    使用不同周期计算年化历史波动率
    """
    try:
        # 获取历史数据（最多90天）
        hist = stock.history(period="3mo")
        if hist.empty:
            return None
        
        # 计算对数收益率
        log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
        
        hv_dict = {}
        for period in periods:
            if len(log_returns) >= period:
                # 计算年化波动率（假设252个交易日）
                volatility = log_returns.tail(period).std() * np.sqrt(252)
                hv_dict[f'HV_{period}d'] = volatility
        
        return hv_dict
    except Exception as e:
        print(f"    计算历史波动率时出错: {e}")
        return None

def calculate_realized_volatility(stock, periods=[10, 20, 30]):
    """
    计算实现波动率 (RV - Realized Volatility)
    使用高频数据计算实际实现的波动率
    """
    try:
        # 获取历史数据
        hist = stock.history(period="3mo")
        if hist.empty:
            return None
        
        # 使用Parkinson波动率估计（使用高低价）
        # RV = sqrt(1/(4*N*ln(2)) * sum((ln(High/Low))^2))
        rv_dict = {}
        
        for period in periods:
            if len(hist) >= period:
                recent_data = hist.tail(period)
                high_low_ratio = np.log(recent_data['High'] / recent_data['Low']) ** 2
                parkinson_vol = np.sqrt(high_low_ratio.sum() / (4 * period * np.log(2))) * np.sqrt(252)
                rv_dict[f'RV_{period}d'] = parkinson_vol
        
        return rv_dict
    except Exception as e:
        print(f"    计算实现波动率时出错: {e}")
        return None

def get_stock_info(ticker):
    """
    获取标的股票的基本信息和波动率
    """
    print(f"\n正在获取 {ticker} 的基本信息...")
    
    try:
        stock = yf.Ticker(ticker)
        
        # 获取当前股价
        current_price = stock.info.get('regularMarketPrice', 0)
        if current_price == 0:
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        # 获取隐含波动率（如果可用）
        implied_volatility = stock.info.get('impliedVolatility', None)
        
        # 计算历史波动率
        hv = calculate_historical_volatility(stock)
        
        # 计算实现波动率
        rv = calculate_realized_volatility(stock)
        
        stock_info = {
            'ticker': ticker,
            'current_price': current_price,
            'implied_volatility': implied_volatility,
            'timestamp': datetime.now().isoformat(),
            'historical_volatility': hv if hv else {},
            'realized_volatility': rv if rv else {}
        }
        
        print(f"  当前股价: ${current_price:.2f}")
        if hv:
            for key, val in hv.items():
                print(f"  {key}: {val*100:.2f}%")
        if rv:
            for key, val in rv.items():
                print(f"  {key}: {val*100:.2f}%")
        
        return stock_info, stock
    
    except Exception as e:
        print(f"  获取 {ticker} 信息时出错: {e}")
        return None, None

def download_options_chain(ticker):
    """
    下载单个标的的完整期权链数据
    """
    print(f"\n{'='*60}")
    print(f"开始下载 {ticker} 的期权链数据")
    print(f"{'='*60}")
    
    # 创建该标的的数据目录
    ticker_dir = os.path.join(data_dir, ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    
    # 获取股票信息
    stock_info, stock = get_stock_info(ticker)
    if not stock_info or not stock:
        print(f"  跳过 {ticker}，无法获取股票信息")
        return False
    
    # 保存股票基本信息
    info_file = os.path.join(ticker_dir, 'stock_info.json')
    with open(info_file, 'w') as f:
        json.dump(stock_info, f, indent=2)
    
    # 获取期权到期日
    try:
        print(f"\n正在获取期权到期日列表...")
        time.sleep(2)
        
        expiration_dates = stock.options
        print(f"  找到 {len(expiration_dates)} 个到期日")
        
        if not expiration_dates:
            print(f"  {ticker} 没有可用的期权数据")
            return False
        
        # 选择前几个到期日（例如前6个）
        selected_expirations = list(expiration_dates[:6])
        print(f"  选择下载以下到期日: {selected_expirations}")
        
        all_options_data = []
        
        # 下载每个到期日的期权链
        for exp_date in selected_expirations:
            print(f"\n  正在下载到期日 {exp_date} 的期权链...")
            time.sleep(2)
            
            try:
                option_chain = stock.option_chain(exp_date)
                
                # 处理看涨期权
                calls = option_chain.calls.copy()
                calls['optionType'] = 'CALL'
                calls['expirationDate'] = exp_date
                calls['underlyingPrice'] = stock_info['current_price']
                
                # 处理看跌期权
                puts = option_chain.puts.copy()
                puts['optionType'] = 'PUT'
                puts['expirationDate'] = exp_date
                puts['underlyingPrice'] = stock_info['current_price']
                
                # 合并数据
                combined = pd.concat([calls, puts], ignore_index=True)
                all_options_data.append(combined)
                
                print(f"    看涨期权: {len(calls)} 个")
                print(f"    看跌期权: {len(puts)} 个")
                
                # 保存单独的CSV文件
                calls_file = os.path.join(ticker_dir, f"{exp_date}_calls.csv")
                puts_file = os.path.join(ticker_dir, f"{exp_date}_puts.csv")
                
                calls.to_csv(calls_file, index=False, encoding='utf-8-sig')
                puts.to_csv(puts_file, index=False, encoding='utf-8-sig')
                
            except Exception as e:
                print(f"    下载到期日 {exp_date} 时出错: {e}")
                continue
        
        # 合并所有期权数据
        if all_options_data:
            all_options_df = pd.concat(all_options_data, ignore_index=True)
            
            # 保存完整的期权链数据
            all_options_file = os.path.join(ticker_dir, 'all_options.csv')
            all_options_df.to_csv(all_options_file, index=False, encoding='utf-8-sig')
            
            print(f"\n  ✓ 成功保存 {len(all_options_df)} 条期权数据到 {all_options_file}")
            
            # 生成数据摘要
            summary = {
                'ticker': ticker,
                'download_time': datetime.now().isoformat(),
                'total_options': len(all_options_df),
                'expiration_dates': selected_expirations,
                'calls_count': len(all_options_df[all_options_df['optionType'] == 'CALL']),
                'puts_count': len(all_options_df[all_options_df['optionType'] == 'PUT']),
                'columns': list(all_options_df.columns)
            }
            
            summary_file = os.path.join(ticker_dir, 'summary.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"  ✓ 数据摘要已保存到 {summary_file}")
            return True
        else:
            print(f"  未能下载任何期权数据")
            return False
            
    except Exception as e:
        print(f"  获取期权链时出错: {e}")
        return False

def main():
    """
    主函数：下载所有标的的期权链数据
    """
    print("="*60)
    print("期权链数据下载工具")
    print(f"标的列表: {', '.join(TICKERS)}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    success_count = 0
    
    for i, ticker in enumerate(TICKERS):
        if i > 0:
            delay = 5
            print(f"\n等待 {delay} 秒以避免API限制...")
            time.sleep(delay)
        
        try:
            if download_options_chain(ticker):
                success_count += 1
        except Exception as e:
            print(f"\n下载 {ticker} 时发生错误: {e}")
            continue
    
    print("\n" + "="*60)
    print(f"下载完成! 成功: {success_count}/{len(TICKERS)}")
    print(f"数据保存在: {data_dir}")
    print("="*60)

if __name__ == "__main__":
    main()
