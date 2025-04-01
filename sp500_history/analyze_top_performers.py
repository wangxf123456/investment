import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import os
import time

def load_historical_components():
    """加载历史成分股数据"""
    file_path = 'data/sp500_historical_components.json'
    print(f"正在从 {file_path} 加载历史成分股数据...")
    with open(file_path, 'r') as f:
        return json.load(f)

def get_stock_data(symbol, year):
    """获取单个股票的年度数据"""
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        df = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            progress=False
        )
        
        if df.empty or len(df) < 2:
            print(f"{symbol} 数据不足")
            return None
            
        # 计算回报率
        first_price = float(df['Close'].iloc[0].item())
        last_price = float(df['Close'].iloc[-1].item())
        return_rate = (last_price - first_price) / first_price * 100
        
        print(f"成功获取 {symbol} 的数据，回报率: {return_rate:.2f}%")
        return {
            'symbol': symbol,
            'start_price': first_price,
            'end_price': last_price,
            'return_rate': return_rate,
            'trading_days': len(df)
        }
    except Exception as e:
        print(f"获取 {symbol} 数据时出错: {str(e)}")
        return None

def analyze_year(year, components, output_dir):
    """分析特定年份的股票表现"""
    print(f"\n分析 {year} 年的数据...")
    
    # 获取该年的成分股
    symbols = components[str(year)]
    total_stocks = len(symbols)
    print(f"需要处理的股票数量：{total_stocks}")
    
    all_results = []
    processed = 0
    
    # 逐个处理股票
    for symbol in symbols:
        processed += 1
        print(f"\n处理第 {processed}/{total_stocks} 支股票: {symbol}")
        
        result = get_stock_data(symbol, year)
        if result:
            all_results.append(result)
    
    if not all_results:
        print(f"警告：{year}年没有获取到任何有效数据")
        return year, []
    
    # 按回报率排序
    all_results.sort(key=lambda x: x['return_rate'], reverse=True)
    top_10 = all_results[:10]
    
    # 生成报告
    report = f"=== {year}年表现最好的10支股票 ===\n\n"
    report += f"分析的股票总数：{total_stocks}\n"
    report += f"获取到数据的股票数：{len(all_results)}\n\n"
    
    for i, stock in enumerate(top_10, 1):
        report += f"{i}. {stock['symbol']}\n"
        report += f"   起始价格: ${stock['start_price']:.2f}\n"
        report += f"   结束价格: ${stock['end_price']:.2f}\n"
        report += f"   年度回报率: {stock['return_rate']:.2f}%\n"
        report += f"   交易天数: {stock['trading_days']}\n\n"
    
    # 保存报告
    os.makedirs(output_dir, exist_ok=True)
    report_file = os.path.join(output_dir, f"{year}_top_performers.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"已保存{year}年的分析结果到 {report_file}")
    return year, top_10[:3]

def main():
    try:
        # 创建输出目录
        output_dir = "analysis_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载历史成分股数据
        components = load_historical_components()
        
        # 分析每一年
        summary_report = "=== 标普500指数 年度最佳表现股票汇总 ===\n\n"
        years = sorted([int(y) for y in components.keys()], reverse=True)
        total_years = len([y for y in years if y >= 2000 and y <= datetime.now().year])
        current_year = 0
        
        for year in years:
            if year >= 2000 and year <= datetime.now().year:
                current_year += 1
                print(f"\n处理第 {current_year}/{total_years} 年: {year}")
                
                year, top_3 = analyze_year(year, components, output_dir)
                
                if top_3:
                    summary_report += f"{year}年前3名：\n"
                    for i, stock in enumerate(top_3, 1):
                        summary_report += f"{i}. {stock['symbol']} ({stock['return_rate']:.2f}%)\n"
                else:
                    summary_report += f"{year}年：数据不足\n"
                summary_report += "\n"
                
                # 年份间暂停
                if current_year < total_years:
                    print("暂停5秒后继续下一年...")
                    time.sleep(5)
        
        # 保存汇总报告
        summary_file = os.path.join(output_dir, "summary_report.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        print(f"\n分析完成！结果已保存到 {output_dir} 目录")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main()