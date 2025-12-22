#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一键运行脚本
自动执行数据下载和Greeks计算
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """运行Python脚本"""
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True
        )
        print(f"\n✓ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} 失败: {e}")
        return False

def main():
    print("="*60)
    print("期权链数据获取与分析")
    print("="*60)
    
    # 步骤1: 下载期权链数据
    if not run_script("fetch_options_chain.py", "下载期权链数据"):
        print("\n数据下载失败，程序终止")
        return
    
    # 步骤2: 计算Greeks
    if not run_script("calculate_greeks.py", "计算期权Greeks"):
        print("\nGreeks计算失败")
        return
    
    print("\n" + "="*60)
    print("所有步骤执行完成!")
    print("="*60)
    print("\n数据文件位置:")
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    print(f"  {data_dir}")
    print("\n每个标的目录包含:")
    print("  - stock_info.json: 股价和波动率信息")
    print("  - all_options.csv: 所有期权数据")
    print("  - options_with_greeks.csv: 包含Greeks的完整期权数据")
    print("  - *_calls.csv / *_puts.csv: 按到期日分类的期权数据")

if __name__ == "__main__":
    main()
