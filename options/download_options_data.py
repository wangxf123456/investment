#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
import json
import pickle

# 创建数据目录
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

# 需要分析的股票列表 - 只下载SPY
tickers = ["SPY"]

def find_closest_expiration(expirations, target_date):
    """找到最接近目标日期的到期日"""
    if not expirations:
        return None
    
    closest = expirations[0]
    closest_diff = abs((datetime.strptime(closest, '%Y-%m-%d') - target_date).days)
    
    for exp in expirations:
        exp_date = datetime.strptime(exp, '%Y-%m-%d')
        diff = abs((exp_date - target_date).days)
        if diff < closest_diff:
            closest = exp
            closest_diff = diff
    
    return closest

def download_ticker_data(ticker):
    """下载单个股票的期权数据"""
    print(f"下载 {ticker} 的数据...")
    
    try:
        ticker_data = {}
        
        # 创建该股票的数据目录
        ticker_dir = os.path.join(data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        
        # 获取股票信息
        stock = yf.Ticker(ticker)
        time.sleep(1)  # 添加延时
        
        # 获取股票当前价格
        current_price = stock.info.get('regularMarketPrice', 0)
        if current_price == 0:
            current_price = stock.history(period="1d")['Close'].iloc[-1]
        
        print(f"  当前股价: {current_price}")
        ticker_data['current_price'] = current_price
        
        # 获取期权到期日列表
        print(f"  获取期权到期日列表...")
        time.sleep(2)  # 添加延时
        
        try:
            expiration_dates = stock.options
            print(f"  获取到 {len(expiration_dates)} 个到期日")
            
            # 计算特定的目标日期（一周、两周、一个月、两个月）
            today = datetime.now()
            target_dates = [
                today + timedelta(days=7),    # 一周
                today + timedelta(days=14),   # 两周
                today + timedelta(days=30),   # 一个月
                today + timedelta(days=60)    # 两个月
            ]
            
            # 找到最接近目标日期的到期日
            selected_expirations = []
            for target in target_dates:
                closest_exp = find_closest_expiration(expiration_dates, target)
                if closest_exp and closest_exp not in selected_expirations:
                    selected_expirations.append(closest_exp)
            
            print(f"  选择下载以下到期日: {selected_expirations}")
            ticker_data['expiration_dates'] = selected_expirations
            
            # 保存基本信息
            with open(os.path.join(ticker_dir, 'info.json'), 'w') as f:
                json.dump(ticker_data, f)
            
            # 为每个选定的到期日下载期权数据
            for exp_date in selected_expirations:
                # 添加延时
                time.sleep(3)
                
                print(f"  下载到期日 {exp_date} 的期权数据...")
                
                try:
                    option_chain = stock.option_chain(exp_date)
                    
                    # 保存看跌期权数据
                    puts_df = option_chain.puts
                    puts_file = os.path.join(ticker_dir, f"{exp_date}_puts.csv")
                    puts_df.to_csv(puts_file, index=False)
                    print(f"    保存了 {len(puts_df)} 个看跌期权到 {puts_file}")
                    
                    # 保存看涨期权数据
                    calls_df = option_chain.calls
                    calls_file = os.path.join(ticker_dir, f"{exp_date}_calls.csv")
                    calls_df.to_csv(calls_file, index=False)
                    print(f"    保存了 {len(calls_df)} 个看涨期权到 {calls_file}")
                    
                    # 添加延时
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    下载到期日 {exp_date} 的期权数据时出错: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"  获取期权到期日出错: {e}")
            return False
        
    except Exception as e:
        print(f"下载 {ticker} 数据时出错: {e}")
        return False

def download_all_data():
    """下载所有股票的期权数据"""
    success_count = 0
    
    for i, ticker in enumerate(tickers):
        if i > 0:
            # 每个股票之间添加较长的延时
            delay = 5 + i * 2  # 增加延时，后面的股票等待更长时间
            print(f"等待 {delay} 秒以避免API速率限制...")
            time.sleep(delay)
        
        # 尝试下载数据，如果失败则重试一次
        success = download_ticker_data(ticker)
        
        if not success:
            print(f"首次下载 {ticker} 失败，5秒后重试一次...")
            time.sleep(5)
            success = download_ticker_data(ticker)
        
        if success:
            success_count += 1
    
    return success_count

if __name__ == "__main__":
    print("开始下载期权数据...")
    start_time = datetime.now()
    
    success_count = download_all_data()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() // 60
    
    print(f"\n下载完成! 已成功下载 {success_count}/{len(tickers)} 个股票的数据")
    print(f"数据保存在 {data_dir} 目录中")
    print(f"总耗时: {duration} 分钟") 