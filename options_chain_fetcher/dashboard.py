#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
期权数据Dashboard Web服务器
提供可视化界面查看期权链数据
"""

from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TICKERS = ["NVDA", "QQQ", "IBIT"]

def load_stock_info(ticker):
    """加载股票基本信息"""
    info_file = os.path.join(DATA_DIR, ticker, 'stock_info.json')
    if os.path.exists(info_file):
        with open(info_file, 'r') as f:
            return json.load(f)
    return None

def load_options_data(ticker):
    """加载期权数据"""
    greeks_file = os.path.join(DATA_DIR, ticker, 'options_with_greeks.csv')
    if os.path.exists(greeks_file):
        df = pd.read_csv(greeks_file)
        return df
    return None

@app.route('/')
def index():
    """主页"""
    return render_template('dashboard.html')

@app.route('/api/overview')
def get_overview():
    """获取所有标的的概览数据"""
    overview = []
    
    for ticker in TICKERS:
        info = load_stock_info(ticker)
        if info:
            df = load_options_data(ticker)
            
            overview_data = {
                'ticker': ticker,
                'current_price': info['current_price'],
                'timestamp': info['timestamp'],
                'hv': info.get('historical_volatility', {}),
                'rv': info.get('realized_volatility', {}),
                'total_options': len(df) if df is not None else 0,
                'num_expirations': df['expirationDate'].nunique() if df is not None else 0
            }
            overview.append(overview_data)
    
    return jsonify(overview)

@app.route('/api/ticker/<ticker>')
def get_ticker_data(ticker):
    """获取单个标的的详细数据"""
    info = load_stock_info(ticker)
    df = load_options_data(ticker)
    
    if info is None or df is None:
        return jsonify({'error': 'Data not found'}), 404
    
    # 获取所有到期日
    expirations = sorted(df['expirationDate'].unique().tolist())
    
    # 计算IV统计
    iv_data = df[df['impliedVolatility'].notna() & (df['impliedVolatility'] > 0)]
    iv_stats = {
        'mean': float(iv_data['impliedVolatility'].mean()) if len(iv_data) > 0 else 0,
        'median': float(iv_data['impliedVolatility'].median()) if len(iv_data) > 0 else 0,
        'min': float(iv_data['impliedVolatility'].min()) if len(iv_data) > 0 else 0,
        'max': float(iv_data['impliedVolatility'].max()) if len(iv_data) > 0 else 0
    }
    
    # Greeks统计
    valid_df = df[(df['delta'].notna()) & (df['delta'] != 0)]
    greeks_stats = {
        'delta_call_avg': float(valid_df[valid_df['optionType']=='CALL']['delta'].mean()) if len(valid_df) > 0 else 0,
        'delta_put_avg': float(valid_df[valid_df['optionType']=='PUT']['delta'].mean()) if len(valid_df) > 0 else 0,
        'gamma_avg': float(valid_df['gamma'].mean()) if len(valid_df) > 0 else 0,
        'theta_avg': float(valid_df['theta'].mean()) if len(valid_df) > 0 else 0,
        'vega_avg': float(valid_df['vega'].mean()) if len(valid_df) > 0 else 0
    }
    
    return jsonify({
        'ticker': ticker,
        'info': info,
        'expirations': expirations,
        'iv_stats': iv_stats,
        'greeks_stats': greeks_stats,
        'total_calls': int(len(df[df['optionType']=='CALL'])),
        'total_puts': int(len(df[df['optionType']=='PUT']))
    })

@app.route('/api/options/<ticker>/<expiration>')
def get_options_chain(ticker, expiration):
    """获取特定到期日的期权链（优化版本）"""
    df = load_options_data(ticker)
    info = load_stock_info(ticker)
    
    if df is None or info is None:
        return jsonify({'error': 'Data not found'}), 404
    
    # 筛选特定到期日
    exp_df = df[df['expirationDate'] == expiration].copy()
    
    if len(exp_df) == 0:
        return jsonify({'error': 'Expiration date not found'}), 404
    
    current_price = info['current_price']
    exp_df['distance_from_atm'] = abs(exp_df['strike'] - current_price)
    
    # 优先筛选有流动性的期权（IV > 0 且 lastPrice > 0）
    exp_df_priority = exp_df[
        (exp_df['impliedVolatility'].notna()) & 
        (exp_df['impliedVolatility'] > 0) &
        (exp_df['lastPrice'].notna()) & 
        (exp_df['lastPrice'] > 0)
    ].copy()
    
    # 如果优先数据不够，则放宽条件
    if len(exp_df_priority) < 20:
        exp_df_priority = exp_df[
            ((exp_df['lastPrice'].notna()) & (exp_df['lastPrice'] > 0)) |
            ((exp_df['impliedVolatility'].notna()) & (exp_df['impliedVolatility'] > 0))
        ].copy()
    
    # === 处理看涨期权 (Calls) ===
    calls_all = exp_df_priority[exp_df_priority['optionType']=='CALL'].copy()
    
    # 分为价内和价外，按strike和volume排序
    calls_otm = calls_all[calls_all['strike'] > current_price].sort_values(['strike', 'volume'], ascending=[True, False])  # 价外，strike升序，volume降序
    calls_itm = calls_all[calls_all['strike'] <= current_price].sort_values(['strike', 'volume'], ascending=[False, False])  #价内，strike降序，volume降序
    
    # 取前15个价外 + 前5个价内（最接近现价的）
    calls_selected = pd.concat([
        calls_itm.head(5),
        calls_otm.head(15)
    ]).sort_values(['strike', 'volume'], ascending=[True, False])
    
    # === 处理看跌期权 (Puts) ===
    puts_all = exp_df_priority[exp_df_priority['optionType']=='PUT'].copy()
    
    # 分为价内和价外，按strike和volume排序
    puts_otm = puts_all[puts_all['strike'] < current_price].sort_values(['strike', 'volume'], ascending=[False, False])  # 价外，strike降序，volume降序
    puts_itm = puts_all[puts_all['strike'] >= current_price].sort_values(['strike', 'volume'], ascending=[True, False])  # 价内，strike升序，volume降序
    
    # 取前15个价外 + 前5个价内（最接近现价的）
    puts_selected = pd.concat([
        puts_itm.head(5),
        puts_otm.head(15)
    ]).sort_values(['strike', 'volume'], ascending=[False, False])
    
    # 转换为字典，并处理NaN值
    import numpy as np
    calls_data = calls_selected.replace({np.nan: None}).to_dict('records')
    puts_data = puts_selected.replace({np.nan: None}).to_dict('records')
    
    return jsonify({
        'ticker': ticker,
        'expiration': expiration,
        'current_price': current_price,
        'calls': calls_data,
        'puts': puts_data
    })

@app.route('/api/volatility/<ticker>')
def get_volatility_data(ticker):
    """获取波动率数据用于图表"""
    info = load_stock_info(ticker)
    
    if info is None:
        return jsonify({'error': 'Data not found'}), 404
    
    hv = info.get('historical_volatility', {})
    rv = info.get('realized_volatility', {})
    
    # 准备图表数据
    periods = []
    hv_values = []
    rv_values = []
    
    for period in ['10d', '20d', '30d', '60d']:
        hv_key = f'HV_{period}'
        rv_key = f'RV_{period}'
        
        if hv_key in hv:
            periods.append(period)
            hv_values.append(hv[hv_key] * 100)
            rv_values.append(rv.get(rv_key, 0) * 100)
    
    return jsonify({
        'ticker': ticker,
        'periods': periods,
        'hv': hv_values,
        'rv': rv_values
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("期权数据Dashboard启动中...")
    print("="*60)
    print(f"\n访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
