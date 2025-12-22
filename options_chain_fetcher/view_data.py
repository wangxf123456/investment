#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据查看工具
快速查看下载的期权数据和Greeks
"""

import pandas as pd
import json
import os

def display_stock_info(ticker):
    """显示股票基本信息"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ticker)
    stock_info_file = os.path.join(data_dir, 'stock_info.json')
    
    if not os.path.exists(stock_info_file):
        print(f"找不到 {ticker} 的数据")
        return
    
    with open(stock_info_file, 'r') as f:
        info = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"{ticker} - 股票信息")
    print(f"{'='*60}")
    print(f"当前股价: ${info['current_price']:.2f}")
    print(f"更新时间: {info['timestamp']}")
    
    print(f"\n历史波动率 (HV):")
    for key, val in info['historical_volatility'].items():
        print(f"  {key}: {val*100:.2f}%")
    
    print(f"\n实现波动率 (RV):")
    for key, val in info['realized_volatility'].items():
        print(f"  {key}: {val*100:.2f}%")

def display_options_summary(ticker):
    """显示期权数据摘要"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ticker)
    greeks_file = os.path.join(data_dir, 'options_with_greeks.csv')
    
    if not os.path.exists(greeks_file):
        print(f"找不到 {ticker} 的期权数据")
        return
    
    df = pd.read_csv(greeks_file)
    
    print(f"\n期权数据摘要:")
    print(f"  总期权数: {len(df)}")
    print(f"  看涨期权: {len(df[df['optionType']=='CALL'])}")
    print(f"  看跌期权: {len(df[df['optionType']=='PUT'])}")
    print(f"  到期日数量: {df['expirationDate'].nunique()}")
    
    print(f"\nGreeks统计 (非零值):")
    
    # 过滤掉零值和无效值
    valid_df = df[(df['delta'].notna()) & (df['delta'] != 0)]
    
    if len(valid_df) > 0:
        print(f"\nDelta:")
        print(f"  Call平均: {valid_df[valid_df['optionType']=='CALL']['delta'].mean():.4f}")
        print(f"  Put平均: {valid_df[valid_df['optionType']=='PUT']['delta'].mean():.4f}")
        
        print(f"\nGamma (平均): {valid_df['gamma'].mean():.6f}")
        print(f"Theta (平均): {valid_df['theta'].mean():.4f}")
        print(f"Vega (平均): {valid_df['vega'].mean():.4f}")
    
    # 显示隐含波动率分布
    iv_data = df[df['impliedVolatility'].notna() & (df['impliedVolatility'] > 0)]
    if len(iv_data) > 0:
        print(f"\n隐含波动率 (IV):")
        print(f"  平均: {iv_data['impliedVolatility'].mean()*100:.2f}%")
        print(f"  中位数: {iv_data['impliedVolatility'].median()*100:.2f}%")
        print(f"  最小: {iv_data['impliedVolatility'].min()*100:.2f}%")
        print(f"  最大: {iv_data['impliedVolatility'].max()*100:.2f}%")

def show_atm_options(ticker, num_strikes=5):
    """显示平值附近的期权"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ticker)
    greeks_file = os.path.join(data_dir, 'options_with_greeks.csv')
    stock_info_file = os.path.join(data_dir, 'stock_info.json')
    
    if not os.path.exists(greeks_file) or not os.path.exists(stock_info_file):
        print(f"找不到 {ticker} 的完整数据")
        return
    
    with open(stock_info_file, 'r') as f:
        info = json.load(f)
    
    current_price = info['current_price']
    df = pd.read_csv(greeks_file)
    
    # 找到第一个到期日的期权
    first_exp = df['expirationDate'].min()
    exp_df = df[df['expirationDate'] == first_exp].copy()
    
    # 计算距离平值的距离
    exp_df['distance_from_atm'] = abs(exp_df['strike'] - current_price)
    
    # 排序并选择最接近平值的期权
    exp_df = exp_df.sort_values('distance_from_atm')
    
    print(f"\n{'='*60}")
    print(f"{ticker} - 平值附近期权 (到期日: {first_exp})")
    print(f"当前股价: ${current_price:.2f}")
    print(f"{'='*60}")
    
    # 分别显示Call和Put
    for opt_type in ['CALL', 'PUT']:
        print(f"\n{opt_type}期权:")
        type_df = exp_df[exp_df['optionType'] == opt_type].head(num_strikes)
        
        display_cols = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 
                       'impliedVolatility', 'delta', 'gamma', 'theta', 'vega']
        
        # 选择存在的列
        available_cols = [col for col in display_cols if col in type_df.columns]
        
        if len(type_df) > 0:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.float_format', lambda x: f'{x:.4f}' if abs(x) < 1 else f'{x:.2f}')
            print(type_df[available_cols].to_string(index=False))

def main():
    """主函数：显示所有标的的数据"""
    tickers = ["NVDA", "QQQ", "IBIT"]
    
    print("="*60)
    print("期权链数据查看器")
    print("="*60)
    
    for ticker in tickers:
        try:
            display_stock_info(ticker)
            display_options_summary(ticker)
            show_atm_options(ticker)
            print("\n")
        except Exception as e:
            print(f"\n查看 {ticker} 数据时出错: {e}")
            continue
    
    print("="*60)
    print("提示: 详细数据请查看 data/ 目录下的CSV文件")
    print("="*60)

if __name__ == "__main__":
    main()
