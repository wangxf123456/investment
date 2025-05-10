#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from scipy.stats import norm
import os
import json
import glob

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据目录和结果目录
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(results_dir, exist_ok=True)

# Black-Scholes模型计算期权的隐含波动率和被行权概率
def calculate_implied_probability(S, K, T, r, sigma, option_type='put'):
    """
    计算期权被行权的概率
    S: 当前股价
    K: 行权价
    T: 到期时间（年）
    r: 无风险利率
    sigma: 波动率
    option_type: 'call' 或 'put'
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        # 看涨期权被行权的概率
        return norm.cdf(d2)
    else:
        # 看跌期权被行权的概率
        return norm.cdf(-d2)

def calculate_annualized_return(option_price, strike_price, spot_price, days_to_expiry, option_type='put'):
    """
    计算期权卖方的年化收益率
    option_price: 期权价格
    strike_price: 行权价
    spot_price: 当前股价
    days_to_expiry: 到期天数
    option_type: 'call' 或 'put'
    """
    if option_type == 'put':
        # 对于看跌期权，最大盈利是期权费
        max_profit = option_price
        # 最大风险是行权价减去期权费（考虑股票价格可能跌至零）
        max_risk = strike_price - option_price
    else:
        # 对于看涨期权，最大盈利是期权费
        max_profit = option_price
        # 最大风险理论上是无限的，但为了计算，我们假设一个最大损失
        max_risk = spot_price * 2  # 假设最大损失是当前股价的两倍
    
    # 年化收益率计算
    if max_risk > 0:
        return (max_profit / max_risk) * (365 / days_to_expiry) * 100
    return 0

def analyze_local_options():
    """分析本地存储的期权数据"""
    all_results = []
    best_options = []
    
    # 获取无风险利率（这里使用美国10年期国债收益率的近似值）
    risk_free_rate = 0.04  # 4%，您可以根据最新数据调整
    
    # 检查数据目录中的所有股票文件夹
    tickers = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    for ticker in tickers:
        print(f"分析 {ticker} 的期权数据...")
        ticker_dir = os.path.join(data_dir, ticker)
        
        # 读取股票信息文件
        info_file = os.path.join(ticker_dir, 'info.json')
        if not os.path.exists(info_file):
            print(f"  未找到 {ticker} 的信息文件，跳过...")
            continue
        
        try:
            with open(info_file, 'r') as f:
                ticker_info = json.load(f)
            
            current_price = ticker_info.get('current_price', 0)
            if current_price == 0:
                print(f"  无法获取 {ticker} 的当前价格，跳过...")
                continue
                
            print(f"  当前股价: {current_price}")
            
            # 获取该股票所有的期权文件
            expiration_dates = ticker_info.get('expiration_dates', [])
            if not expiration_dates:
                print(f"  未找到 {ticker} 的到期日信息，尝试从文件名中获取...")
                put_files = glob.glob(os.path.join(ticker_dir, "*_puts.csv"))
                expiration_dates = [os.path.basename(f).split('_')[0] for f in put_files]
            
            if not expiration_dates:
                print(f"  未找到 {ticker} 的到期日信息，跳过...")
                continue
                
            print(f"  分析以下到期日: {expiration_dates}")
            
            for exp_date in expiration_dates:
                # 计算到期天数
                try:
                    exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
                    days_to_expiry = (exp_datetime - datetime.now()).days
                    if days_to_expiry <= 0:
                        print(f"  到期日 {exp_date} 已过期，跳过...")
                        continue
                        
                    years_to_expiry = days_to_expiry / 365
                    
                    print(f"  分析到期日: {exp_date} (还有 {days_to_expiry} 天)")
                    
                    # 读取看跌期权数据
                    puts_file = os.path.join(ticker_dir, f"{exp_date}_puts.csv")
                    if os.path.exists(puts_file):
                        puts = pd.read_csv(puts_file)
                        print(f"    分析看跌期权 (总共 {len(puts)} 个)")
                        
                        # 只分析接近当前价格的期权 (价内和价外10%)
                        min_strike = current_price * 0.9
                        max_strike = current_price * 1.1
                        filtered_puts = puts[(puts['strike'] >= min_strike) & (puts['strike'] <= max_strike)]
                        
                        if len(filtered_puts) > 0:
                            print(f"    过滤后剩余 {len(filtered_puts)} 个看跌期权 (行权价在 {min_strike:.2f} 和 {max_strike:.2f} 之间)")
                            puts = filtered_puts
                        else:
                            # 如果没有期权在范围内，则选择最接近当前价格的几个
                            puts = puts.iloc[abs(puts['strike'] - current_price).argsort()[:5]]
                            print(f"    没有期权在价格范围内，选择最接近当前价格的 {len(puts)} 个")
                        
                        for idx, put in puts.iterrows():
                            strike = put['strike']
                            put_price = put['lastPrice']
                            implied_volatility = put['impliedVolatility']
                            volume = put['volume'] if not pd.isna(put['volume']) else 0
                            open_interest = put['openInterest'] if not pd.isna(put['openInterest']) else 0
                            
                            # 计算被行权概率
                            exercise_prob = calculate_implied_probability(
                                current_price, strike, years_to_expiry, risk_free_rate, implied_volatility, 'put'
                            )
                            
                            # 计算年化收益率
                            annualized_return = calculate_annualized_return(
                                put_price, strike, current_price, days_to_expiry, 'put'
                            )
                            
                            # 保存结果
                            result = {
                                'ticker': ticker,
                                'option_type': 'put',
                                'expiration_date': exp_date,
                                'days_to_expiry': days_to_expiry,
                                'strike': strike,
                                'current_price': current_price,
                                'option_price': put_price,
                                'implied_volatility': implied_volatility,
                                'exercise_probability': exercise_prob * 100,
                                'annualized_return': annualized_return,
                                'volume': volume,
                                'open_interest': open_interest
                            }
                            all_results.append(result)
                            print(f"      分析看跌期权: 行权价={strike}, 价格={put_price}, 被行权概率={exercise_prob*100:.2f}%, 年化收益率={annualized_return:.2f}%")
                    
                    # 读取看涨期权数据
                    calls_file = os.path.join(ticker_dir, f"{exp_date}_calls.csv")
                    if os.path.exists(calls_file):
                        calls = pd.read_csv(calls_file)
                        print(f"    分析看涨期权 (总共 {len(calls)} 个)")
                        
                        # 只分析接近当前价格的期权 (价内和价外10%)
                        filtered_calls = calls[(calls['strike'] >= min_strike) & (calls['strike'] <= max_strike)]
                        
                        if len(filtered_calls) > 0:
                            print(f"    过滤后剩余 {len(filtered_calls)} 个看涨期权 (行权价在 {min_strike:.2f} 和 {max_strike:.2f} 之间)")
                            calls = filtered_calls
                        else:
                            # 如果没有期权在范围内，则选择最接近当前价格的几个
                            calls = calls.iloc[abs(calls['strike'] - current_price).argsort()[:5]]
                            print(f"    没有期权在价格范围内，选择最接近当前价格的 {len(calls)} 个")
                        
                        for idx, call in calls.iterrows():
                            strike = call['strike']
                            call_price = call['lastPrice']
                            implied_volatility = call['impliedVolatility']
                            volume = call['volume'] if not pd.isna(call['volume']) else 0
                            open_interest = call['openInterest'] if not pd.isna(call['openInterest']) else 0
                            
                            # 计算被行权概率
                            exercise_prob = calculate_implied_probability(
                                current_price, strike, years_to_expiry, risk_free_rate, implied_volatility, 'call'
                            )
                            
                            # 计算年化收益率
                            annualized_return = calculate_annualized_return(
                                call_price, strike, current_price, days_to_expiry, 'call'
                            )
                            
                            # 保存结果
                            result = {
                                'ticker': ticker,
                                'option_type': 'call',
                                'expiration_date': exp_date,
                                'days_to_expiry': days_to_expiry,
                                'strike': strike,
                                'current_price': current_price,
                                'option_price': call_price,
                                'implied_volatility': implied_volatility,
                                'exercise_probability': exercise_prob * 100,
                                'annualized_return': annualized_return,
                                'volume': volume,
                                'open_interest': open_interest
                            }
                            all_results.append(result)
                            print(f"      分析看涨期权: 行权价={strike}, 价格={call_price}, 被行权概率={exercise_prob*100:.2f}%, 年化收益率={annualized_return:.2f}%")
                
                except Exception as e:
                    print(f"    处理到期日 {exp_date} 时出错: {e}")
                    continue
            
            # 对该股票找出最优的期权（收益率最高且行权概率低于30%的）
            ticker_results = [r for r in all_results if r['ticker'] == ticker]
            if ticker_results:
                # 筛选行权概率小于30%的期权
                low_prob_options = [r for r in ticker_results if r['exercise_probability'] < 30]
                if low_prob_options:
                    # 按年化收益率排序
                    sorted_options = sorted(low_prob_options, key=lambda x: x['annualized_return'], reverse=True)
                    # 选取最优的看跌和看涨期权
                    best_put = next((o for o in sorted_options if o['option_type'] == 'put'), None)
                    best_call = next((o for o in sorted_options if o['option_type'] == 'call'), None)
                    
                    if best_put:
                        best_options.append(best_put)
                        print(f"  找到最佳看跌期权: 到期日={best_put['expiration_date']}, 行权价={best_put['strike']}, 年化收益率={best_put['annualized_return']:.2f}%")
                    if best_call:
                        best_options.append(best_call)
                        print(f"  找到最佳看涨期权: 到期日={best_call['expiration_date']}, 行权价={best_call['strike']}, 年化收益率={best_call['annualized_return']:.2f}%")
            
        except Exception as e:
            print(f"处理 {ticker} 时出错: {e}")
            continue
    
    # 转换为DataFrame
    results_df = pd.DataFrame(all_results)
    best_options_df = pd.DataFrame(best_options)
    
    # 保存结果
    if not results_df.empty:
        results_df.to_csv(os.path.join(results_dir, "options_analysis_results.csv"), index=False)
        print(f"保存分析结果到 {os.path.join(results_dir, 'options_analysis_results.csv')}")
        
        # 按年化收益率排序，找出最佳期权
        best_overall_df = results_df[results_df['exercise_probability'] < 30].sort_values('annualized_return', ascending=False).head(10)
        best_overall_df.to_csv(os.path.join(results_dir, "best_options_overall.csv"), index=False)
        print(f"保存最佳期权到 {os.path.join(results_dir, 'best_options_overall.csv')}")
        
        # 输出最佳期权
        if not best_options_df.empty:
            best_options_df.to_csv(os.path.join(results_dir, "best_options_by_ticker.csv"), index=False)
            print(f"保存按股票分类的最佳期权到 {os.path.join(results_dir, 'best_options_by_ticker.csv')}")
            
        # 创建可视化
        create_visualizations(results_df, best_overall_df)
    
    return results_df, best_options_df

def create_visualizations(results_df, best_options_df):
    """创建可视化图表"""
    print("创建可视化图表...")
    
    # 1. 不同股票的最佳期权年化收益率比较
    plt.figure(figsize=(12, 8))
    best_by_ticker = results_df.sort_values(['ticker', 'annualized_return'], ascending=[True, False]).groupby('ticker').first()
    best_by_ticker['annualized_return'].plot(kind='bar')
    plt.title('各股票最佳期权年化收益率')
    plt.xlabel('股票代码')
    plt.ylabel('年化收益率 (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'best_returns_by_ticker.png'))
    print(f"保存图表到 {os.path.join(results_dir, 'best_returns_by_ticker.png')}")
    
    # 2. 到期日vs收益率散点图
    plt.figure(figsize=(12, 8))
    plt.scatter(results_df['days_to_expiry'], results_df['annualized_return'], alpha=0.5)
    plt.title('到期日vs年化收益率')
    plt.xlabel('到期天数')
    plt.ylabel('年化收益率 (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'expiry_vs_return.png'))
    print(f"保存图表到 {os.path.join(results_dir, 'expiry_vs_return.png')}")
    
    # 3. 行权概率vs收益率散点图
    plt.figure(figsize=(12, 8))
    plt.scatter(results_df['exercise_probability'], results_df['annualized_return'], alpha=0.5)
    plt.title('行权概率vs年化收益率')
    plt.xlabel('行权概率 (%)')
    plt.ylabel('年化收益率 (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'probability_vs_return.png'))
    print(f"保存图表到 {os.path.join(results_dir, 'probability_vs_return.png')}")
    
    # 4. 最佳期权详情
    if len(best_options_df) > 0:
        plt.figure(figsize=(12, 8))
        best_options_df.sort_values('annualized_return', ascending=False).head(10).plot(
            x='ticker', y='annualized_return', kind='bar', color='green'
        )
        plt.title('十大最佳期权(按年化收益率)')
        plt.xlabel('股票代码')
        plt.ylabel('年化收益率 (%)')
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'top10_best_options.png'))
        print(f"保存图表到 {os.path.join(results_dir, 'top10_best_options.png')}")

if __name__ == "__main__":
    print("开始分析本地期权数据...")
    results_df, best_options_df = analyze_local_options()
    
    if not results_df.empty:
        print("\n分析完成! 结果已保存到 'results' 目录")
        
        print("\n十大最佳期权 (按年化收益率排序):")
        best_overall = results_df[results_df['exercise_probability'] < 30].sort_values('annualized_return', ascending=False).head(10)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(best_overall[['ticker', 'option_type', 'expiration_date', 'strike', 'current_price', 
                           'option_price', 'exercise_probability', 'annualized_return']])
    else:
        print("没有找到符合条件的期权数据。请先运行 download_options_data.py 下载数据。") 