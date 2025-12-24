#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场综合预警仪表盘 - Market Indicators Dashboard
================================================

计算以下关键市场指标:
1. ERP (股权风险溢价) - Equity Risk Premium
2. 巴菲特指标 (Buffett Indicator) - 总市值 / GDP
3. 高收益债利差 (HY Credit Spreads / OAS)
4. 净流动性指标 (Net Liquidity) - 美联储资产负债表 - TGA - RRP
5. 20法则 (Rule of 20) - 标普500 P/E + 通胀率

数据来源: FRED, multpl.com
注意: 20法则使用的是 Trailing PE (TTM)，不是 Forward PE
"""

import os
import sys
import io
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings

# 设置控制台编码为UTF-8 (Windows兼容)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

warnings.filterwarnings('ignore')

import pandas as pd
import requests
from tabulate import tabulate
from bs4 import BeautifulSoup
from fredapi import Fred


class DataFetchError(Exception):
    """数据获取失败异常"""
    pass


class MarketIndicators:
    """市场指标计算器 - 只使用真实数据，获取不到就报错"""
    
    def __init__(self, fred_api_key: str):
        if not fred_api_key:
            raise DataFetchError("必须提供 FRED API Key")
        
        self.fred = Fred(api_key=fred_api_key)
        self.results = {}
        self.data_sources = {}
    
    def _get_fred_series(self, series_id: str, description: str, periods: int = 365) -> pd.Series:
        """从FRED获取数据，失败则报错"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periods)
            data = self.fred.get_series(series_id, start_date, end_date)
            if data is None or len(data) == 0:
                raise DataFetchError(f"FRED {series_id} 返回空数据")
            data = data.dropna()
            if len(data) == 0:
                raise DataFetchError(f"FRED {series_id} 无有效数据")
            latest_date = data.index[-1]
            self.data_sources[description] = f"FRED ({series_id}), {latest_date.strftime('%Y-%m-%d')}"
            return data
        except Exception as e:
            raise DataFetchError(f"获取 FRED {series_id} ({description}) 失败: {e}")
    
    def _get_fred_latest(self, series_id: str, description: str) -> float:
        """获取FRED最新值"""
        data = self._get_fred_series(series_id, description)
        return float(data.iloc[-1])
    
    def _get_sp500_pe_trailing(self) -> float:
        """从 multpl.com 获取 S&P 500 Trailing PE (TTM)"""
        try:
            url = 'https://www.multpl.com/s-p-500-pe-ratio'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise DataFetchError(f"multpl.com 返回状态码 {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            big_value = soup.find('div', {'id': 'current'})
            if not big_value:
                raise DataFetchError("multpl.com 页面结构变化，找不到数据")
            
            value_text = big_value.get_text(strip=True)
            match = re.search(r'Ratio[:\s]*([\d.]+)', value_text)
            if not match:
                raise DataFetchError(f"multpl.com 无法解析PE值: {value_text}")
            
            pe = float(match.group(1))
            self.data_sources['S&P 500 Trailing PE'] = "multpl.com (实时)"
            return pe
        except requests.RequestException as e:
            raise DataFetchError(f"访问 multpl.com 失败: {e}")
    
    def _get_sp500_dividend_yield(self) -> float:
        """从 multpl.com 获取 S&P 500 股息收益率"""
        try:
            url = 'https://www.multpl.com/s-p-500-dividend-yield'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise DataFetchError(f"multpl.com dividend 返回状态码 {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            big_value = soup.find('div', {'id': 'current'})
            if not big_value:
                raise DataFetchError("multpl.com 页面结构变化")
            
            value_text = big_value.get_text(strip=True)
            match = re.search(r'Yield[:\s]*([\d.]+)', value_text)
            if not match:
                raise DataFetchError(f"无法解析股息收益率: {value_text}")
            
            div_yield = float(match.group(1))
            self.data_sources['S&P 500 股息收益率'] = "multpl.com (实时)"
            return div_yield
        except requests.RequestException as e:
            raise DataFetchError(f"访问 multpl.com 股息收益率失败: {e}")
    
    def calculate_erp(self) -> Dict:
        """计算股权风险溢价 (ERP)"""
        result = {
            'name': 'ERP (股权风险溢价)',
            'value': None,
            'warning_level': None,
            'threshold': '< 3.0%',
            'status': None,
        }
        
        # 获取数据
        pe_ratio = self._get_sp500_pe_trailing()
        dividend_yield = self._get_sp500_dividend_yield()
        treasury_10y = self._get_fred_latest('DGS10', '10年期国债收益率')
        
        # 计算盈利收益率 ERP
        earnings_yield = (1 / pe_ratio) * 100
        earnings_erp = earnings_yield - treasury_10y
        
        # 计算隐含 ERP (Gordon模型)
        # 预期回报 = 股息收益率 + 回购收益率(约2%) + 预期增长率(约5%)
        buyback_yield = 2.0  # 历史平均
        expected_growth = 5.0  # 长期名义增长
        expected_return = dividend_yield + buyback_yield + expected_growth
        implied_erp = expected_return - treasury_10y
        
        result['value'] = implied_erp
        
        if implied_erp < 3.0:
            result['warning_level'] = '🔴 红灯'
            result['status'] = '危险'
        elif implied_erp < 4.0:
            result['warning_level'] = '🟡 黄灯'
            result['status'] = '警惕'
        else:
            result['warning_level'] = '🟢 绿灯'
            result['status'] = '正常'
        
        self.results['erp'] = result
        return result
    
    def calculate_buffett_indicator(self) -> Dict:
        """计算巴菲特指标 (总市值/GDP)"""
        result = {
            'name': '巴菲特指标',
            'value': None,
            'warning_level': None,
            'threshold': '> 180%',
            'status': None,
        }
        
        # NCBCEL: 非金融企业股权市值 (十亿美元)
        market_cap = self._get_fred_latest('NCBCEL', '企业股权市值')
        # GDP (十亿美元)
        gdp = self._get_fred_latest('GDP', 'GDP')
        
        ratio = (market_cap / gdp) * 100
        result['value'] = ratio
        
        if ratio > 180:
            result['warning_level'] = '🔴 红灯'
            result['status'] = '极度高估'
        elif ratio > 140:
            result['warning_level'] = '🟡 黄灯'
            result['status'] = '高估'
        else:
            result['warning_level'] = '🟢 绿灯'
            result['status'] = '正常'
        
        self.results['buffett'] = result
        return result
    
    def calculate_hy_spread(self) -> Dict:
        """计算高收益债利差 (OAS)"""
        result = {
            'name': '高收益债利差 (OAS)',
            'value': None,
            'warning_level': None,
            'threshold': '> 500 bps',
            'status': None,
        }
        
        # BAMLH0A0HYM2: ICE BofA US High Yield OAS (单位: %)
        oas_pct = self._get_fred_latest('BAMLH0A0HYM2', 'HY OAS')
        oas_bps = oas_pct * 100  # 转换为基点
        
        result['value'] = oas_bps
        
        if oas_bps > 500:
            result['warning_level'] = '🔴 红灯'
            result['status'] = '危险'
        elif oas_bps > 400:
            result['warning_level'] = '🟡 黄灯'
            result['status'] = '警惕'
        else:
            result['warning_level'] = '🟢 绿灯'
            result['status'] = '正常'
        
        self.results['hy_spread'] = result
        return result
    
    def calculate_net_liquidity(self) -> Dict:
        """计算净流动性 (Fed资产 - TGA - RRP)"""
        result = {
            'name': '净流动性',
            'value': None,
            'warning_level': None,
            'threshold': '趋势判断',
            'status': None,
        }
        
        # WALCL: 美联储总资产 (百万美元)
        fed_assets = self._get_fred_latest('WALCL', '美联储资产')
        # WTREGEN: 财政部TGA (百万美元)
        tga = self._get_fred_latest('WTREGEN', 'TGA')
        # RRPONTSYD: 逆回购 (十亿美元)
        rrp_billions = self._get_fred_latest('RRPONTSYD', 'RRP')
        rrp = rrp_billions * 1000  # 转为百万美元
        
        net_liquidity = fed_assets - tga - rrp
        result['value'] = net_liquidity / 1000000  # 转为万亿
        
        # 判断趋势 - 比较最近值与3个月前
        fed_hist = self._get_fred_series('WALCL', '美联储资产(历史)', periods=365)
        n = len(fed_hist)
        if n >= 2:
            # 比较最新值与最早值
            recent_val = fed_hist.iloc[-1]
            # 尽量取3个月前的值
            older_idx = max(0, n - 13)  # 约3个月前（周数据）
            older_val = fed_hist.iloc[older_idx]
            if recent_val > older_val:
                result['warning_level'] = '🟢 绿灯'
                result['status'] = '上升趋势'
            else:
                result['warning_level'] = '🟡 黄灯'
                result['status'] = '下降趋势'
        else:
            result['warning_level'] = '🟡 黄灯'
            result['status'] = '数据不足'
        
        self.results['net_liquidity'] = result
        return result
    
    def calculate_rule_of_20(self) -> Dict:
        """计算20法则 (Trailing PE + CPI)"""
        result = {
            'name': '20法则 (Trailing PE)',
            'value': None,
            'warning_level': None,
            'threshold': '> 20',
            'status': None,
        }
        
        # Trailing PE
        pe_ratio = self._get_sp500_pe_trailing()
        
        # CPI 同比变化率 - 需要获取足够长的历史数据
        cpi_data = self._get_fred_series('CPIAUCSL', 'CPI', periods=500)
        cpi_data = cpi_data.dropna()  # 移除NaN
        if len(cpi_data) < 13:
            raise DataFetchError(f"CPI数据不足，只有{len(cpi_data)}个点，需要至少13个")
        latest_cpi = cpi_data.iloc[-1]
        year_ago_cpi = cpi_data.iloc[-13]
        cpi_yoy = ((latest_cpi / year_ago_cpi) - 1) * 100
        
        rule_20_value = pe_ratio + abs(cpi_yoy)
        result['value'] = rule_20_value
        
        if rule_20_value > 24:
            result['warning_level'] = '🔴 红灯'
            result['status'] = '严重高估'
        elif rule_20_value > 20:
            result['warning_level'] = '🟡 黄灯'
            result['status'] = '高估'
        else:
            result['warning_level'] = '🟢 绿灯'
            result['status'] = '正常'
        
        self.results['rule_of_20'] = result
        return result
    
    def run_all_indicators(self) -> None:
        """运行所有指标计算"""
        print(f"\n运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        errors = []
        
        # 尝试计算每个指标
        for name, func in [
            ('ERP', self.calculate_erp),
            ('巴菲特指标', self.calculate_buffett_indicator),
            ('高收益债利差', self.calculate_hy_spread),
            ('净流动性', self.calculate_net_liquidity),
            ('20法则', self.calculate_rule_of_20),
        ]:
            try:
                func()
            except DataFetchError as e:
                errors.append(f"[{name}] {e}")
        
        # 打印结果
        self.print_dashboard()
        self.print_data_sources()
        
        # 打印错误
        if errors:
            print("\n" + "=" * 70)
            print("❌ 数据获取失败:")
            for err in errors:
                print(f"  {err}")
    
    def print_dashboard(self) -> None:
        """打印仪表盘"""
        print("\n" + "=" * 70)
        print("📈 市场指标数据")
        print("=" * 70)
        
        table_data = []
        for key, result in self.results.items():
            if result['value'] is not None:
                if key == 'erp':
                    value_str = f"{result['value']:.2f}%"
                elif key == 'buffett':
                    value_str = f"{result['value']:.1f}%"
                elif key == 'hy_spread':
                    value_str = f"{result['value']:.0f} bps"
                elif key == 'net_liquidity':
                    value_str = f"${result['value']:.2f}T"
                elif key == 'rule_of_20':
                    value_str = f"{result['value']:.1f}"
                else:
                    value_str = str(result['value'])
                
                table_data.append([
                    result['name'],
                    result['threshold'],
                    value_str,
                    result['warning_level'],
                    result['status']
                ])
        
        if table_data:
            headers = ['指标', '预警线', '当前值', '状态', '判断']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("无有效数据")
    
    def print_data_sources(self) -> None:
        """打印数据来源"""
        if self.data_sources:
            print("\n" + "-" * 70)
            print("数据来源:")
            for name, source in self.data_sources.items():
                print(f"  {name}: {source}")


def main():
    """主函数"""
    # FRED API Key
    fred_key = os.environ.get('FRED_API_KEY', '1')
    
    try:
        calculator = MarketIndicators(fred_api_key=fred_key)
        calculator.run_all_indicators()
    except DataFetchError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
