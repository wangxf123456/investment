#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
期权Greeks计算工具
使用Black-Scholes模型计算期权的Greeks
"""

import pandas as pd
import numpy as np
from scipy.stats import norm
import os
import json

def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    """
    使用Black-Scholes模型计算期权Greeks
    
    参数:
        S: 标的资产当前价格
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 隐含波动率
        option_type: 'call' 或 'put'
    
    返回:
        dict: 包含所有Greeks的字典
    """
    
    # 处理到期或过期的情况
    if T <= 0:
        if option_type == 'call':
            value = max(S - K, 0)
            delta = 1 if S > K else 0
        else:
            value = max(K - S, 0)
            delta = -1 if K > S else 0
        
        return {
            'value': value,
            'delta': delta,
            'gamma': 0,
            'theta': 0,
            'vega': 0,
            'rho': 0
        }
    
    # 计算d1和d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # 计算Greeks
    if option_type == 'call':
        # Call期权
        value = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        # Put期权
        value = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = -norm.cdf(-d1)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    # Gamma和Vega对Call和Put都一样
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    
    # Theta
    if option_type == 'call':
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
    
    return {
        'bs_value': value,
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

def implied_volatility_from_price(market_price, S, K, T, r, option_type='call'):
    """
    从市场价格反推隐含波动率
    """
    from scipy.optimize import brentq
    
    def bs_price(sigma):
        greeks = black_scholes_greeks(S, K, T, r, sigma, option_type)
        return greeks['bs_value']
    
    def objective(sigma):
        return bs_price(sigma) - market_price
    
    try:
        iv = brentq(objective, 0.001, 5.0, maxiter=100)
        return iv
    except:
        return None

def calculate_greeks_for_options(ticker, risk_free_rate=0.045):
    """
    为某个标的的所有期权计算Greeks
    
    参数:
        ticker: 股票代码
        risk_free_rate: 无风险利率（默认4.5%）
    """
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ticker)
    
    if not os.path.exists(data_dir):
        print(f"错误: 找不到 {ticker} 的数据目录")
        return
    
    # 读取股票信息
    stock_info_file = os.path.join(data_dir, 'stock_info.json')
    if not os.path.exists(stock_info_file):
        print(f"错误: 找不到 {ticker} 的stock_info.json文件")
        return
    
    with open(stock_info_file, 'r') as f:
        stock_info = json.load(f)
    
    current_price = stock_info['current_price']
    
    # 读取所有期权数据
    all_options_file = os.path.join(data_dir, 'all_options.csv')
    if not os.path.exists(all_options_file):
        print(f"错误: 找不到 {ticker} 的all_options.csv文件")
        return
    
    df = pd.read_csv(all_options_file)
    
    print(f"\n计算 {ticker} 的期权Greeks...")
    print(f"当前股价: ${current_price:.2f}")
    print(f"无风险利率: {risk_free_rate*100:.2f}%")
    print(f"期权数量: {len(df)}")
    
    # 计算每个期权的Greeks
    greeks_list = []
    
    for idx, row in df.iterrows():
        try:
            # 计算到期时间（年）
            exp_date = pd.to_datetime(row['expirationDate'])
            now = pd.Timestamp.now()
            days_to_expiry = (exp_date - now).days
            T = max(days_to_expiry / 365.0, 0)
            
            # 获取参数
            K = row['strike']
            sigma = row.get('impliedVolatility', None)
            market_price = row.get('lastPrice', None)
            
            # 如果IV太小(<5%)或无效，尝试从市场价格反推
            use_implied_iv = False
            if pd.isna(sigma) or sigma is None or sigma <= 0 or sigma < 0.05:
                if pd.notna(market_price) and market_price > 0 and T > 0:
                    option_type = 'call' if row['optionType'] == 'CALL' else 'put'
                    calculated_iv = implied_volatility_from_price(market_price, current_price, K, T, risk_free_rate, option_type)
                    if calculated_iv:
                        sigma = calculated_iv
                        use_implied_iv = True
            
            # 如果仍然没有有效的IV，跳过Greeks计算
            if pd.isna(sigma) or sigma is None or sigma <= 0:
                greeks_list.append({
                    'bs_value': np.nan,
                    'delta': np.nan,
                    'gamma': np.nan,
                    'theta': np.nan,
                    'vega': np.nan,
                    'rho': np.nan,
                    'calculated_iv': np.nan
                })
                continue
            
            option_type = 'call' if row['optionType'] == 'CALL' else 'put'
            
            # 计算Greeks
            greeks = black_scholes_greeks(current_price, K, T, risk_free_rate, sigma, option_type)
            greeks['calculated_iv'] = sigma if use_implied_iv else np.nan
            greeks_list.append(greeks)
            
        except Exception as e:
            print(f"  警告: 计算第 {idx} 行期权的Greeks时出错: {e}")
            greeks_list.append({
                'bs_value': np.nan,
                'delta': np.nan,
                'gamma': np.nan,
                'theta': np.nan,
                'vega': np.nan,
                'rho': np.nan
            })
    
    # 添加Greeks到DataFrame（不覆盖原始列）
    greeks_df = pd.DataFrame(greeks_list)
    result_df = pd.concat([df, greeks_df], axis=1)
    
    # 保存结果
    output_file = os.path.join(data_dir, 'options_with_greeks.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✓ 已保存带Greeks的期权数据到: {output_file}")
    
    # 显示统计信息（只统计有效值）
    valid_greeks = result_df[result_df['delta'].notna()]
    if len(valid_greeks) > 0:
        print(f"\nGreeks统计信息 ({len(valid_greeks)}/{len(result_df)} 个期权有有效Greeks):")
        print(f"Delta: {valid_greeks['delta'].min():.4f} ~ {valid_greeks['delta'].max():.4f}")
        print(f"Gamma: {valid_greeks['gamma'].min():.6f} ~ {valid_greeks['gamma'].max():.6f}")
        print(f"Theta: {valid_greeks['theta'].min():.4f} ~ {valid_greeks['theta'].max():.4f}")
        print(f"Vega: {valid_greeks['vega'].min():.4f} ~ {valid_greeks['vega'].max():.4f}")
    else:
        print("\n警告: 没有计算出有效的Greeks")
    
    return result_df

def main():
    """
    主函数：为所有标的计算Greeks
    """
    tickers = ["NVDA", "QQQ", "IBIT"]
    
    print("="*60)
    print("期权Greeks计算工具")
    print("使用Black-Scholes模型")
    print("="*60)
    
    for ticker in tickers:
        try:
            calculate_greeks_for_options(ticker)
        except Exception as e:
            print(f"\n处理 {ticker} 时出错: {e}")
            continue
    
    print("\n" + "="*60)
    print("Greeks计算完成!")
    print("="*60)

if __name__ == "__main__":
    main()
