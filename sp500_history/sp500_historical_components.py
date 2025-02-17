import pandas as pd
import requests
from datetime import datetime
import os
import json
from bs4 import BeautifulSoup
import time
import io
import sys

def parse_date(date_str):
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str.strip(), '%B %d, %Y')
    except Exception as e:
        print(f"无法解析日期: {date_str}")
        raise e

def get_current_sp500_companies():
    """获取当前的标普500成分股列表"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        print(f"正在从 {url} 获取数据...")
        response = requests.get(url)
        response.raise_for_status()
        print("成功获取网页内容")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'})
        
        if not table:
            raise ValueError("未找到包含当前成分股的表格")
        
        # 获取表头
        headers = []
        for th in table.find_all('th'):
            headers.append(th.text.strip())
        
        # 获取数据行
        rows = []
        for tr in table.find_all('tr')[1:]:  # 跳过表头行
            row = []
            for td in tr.find_all('td'):
                row.append(td.text.strip())
            if row:  # 确保行不为空
                rows.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(rows, columns=headers)
        print("成功提取当前成分股表格")
        return df
    except Exception as e:
        print(f"获取当前成分股数据时出错: {str(e)}", file=sys.stderr)
        raise

def get_historical_changes():
    """获取历史变更记录"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        print(f"正在从 {url} 获取历史变更数据...")
        response = requests.get(url)
        response.raise_for_status()
        print("成功获取网页内容")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        if len(tables) < 2:
            raise ValueError("未找到历史变更表格")
        
        changes_table = tables[1]
        
        # 获取表头
        headers = []
        for th in changes_table.find_all('th'):
            headers.append(th.text.strip())
        
        print("\n表头:", headers)
        
        # 获取数据行
        rows = []
        skipped_rows = []
        
        # 创建公司名称到代码的映射
        company_to_ticker = {}
        
        # 首先从当前成分股表格获取映射关系
        current_table = tables[0]
        for tr in current_table.find_all('tr')[1:]:
            cells = tr.find_all('td')
            if cells and len(cells) >= 2:
                ticker = cells[0].text.strip()
                company = cells[1].text.strip()
                company_to_ticker[company] = ticker
        
        print(f"\n从当前成分股表格获取了 {len(company_to_ticker)} 个公司名称映射")
        
        for tr in changes_table.find_all('tr')[1:]:  # 跳过表头行
            cells = tr.find_all('td')
            if cells:  # 确保行不为空
                date = cells[0].text.strip()
                added = cells[1].text.strip()
                removed = cells[2].text.strip()
                reason = cells[3].text.strip() if len(cells) > 3 else ""
                
                # 如果有更多的列，可能包含股票代码和公司名称的对应关系
                if len(cells) > 4:
                    for i in range(4, len(cells), 2):
                        if i + 1 < len(cells):
                            ticker = cells[i].text.strip()
                            company = cells[i+1].text.strip()
                            if ticker and company:
                                company_to_ticker[company] = ticker
                
                # 处理公司名称和代码
                added_ticker = added
                removed_ticker = removed
                
                # 如果是公司名称，尝试从映射中获取代码
                if ' ' in added:
                    added_ticker = company_to_ticker.get(added, '')
                    if not added_ticker:
                        print(f"\n警告：无法找到公司的股票代码: {added}")
                
                if ' ' in removed:
                    removed_ticker = company_to_ticker.get(removed, '')
                    if not removed_ticker:
                        print(f"\n警告：无法找到公司的股票代码: {removed}")
                
                try:
                    parsed_date = parse_date(date)
                    row_data = {
                        'Date': parsed_date,
                        'Added': added_ticker,
                        'Removed': removed_ticker,
                        'Reason': reason
                    }
                    rows.append(row_data)
                    
                    # 打印前几行数据作为示例
                    if len(rows) <= 5:
                        print(f"\n处理的数据 {len(rows)}:")
                        print(f"日期: {date}")
                        print(f"添加: {added} -> {added_ticker}")
                        print(f"移除: {removed} -> {removed_ticker}")
                        print(f"原因: {reason}")
                except Exception as e:
                    print(f"\n跳过无效日期行: {date}")
                    skipped_rows.append({
                        'Date': date,
                        'Added': added,
                        'Removed': removed,
                        'Reason': reason
                    })
                    continue
        
        print(f"\n跳过的行数: {len(skipped_rows)}")
        if skipped_rows:
            print("示例跳过的行:")
            for row in skipped_rows[:5]:
                print(row)
        
        # 创建DataFrame
        changes_df = pd.DataFrame(rows)
        print(f"\n成功提取历史变更记录，共 {len(changes_df)} 条")
        
        # 分析变更记录的时间分布
        year_counts = changes_df['Date'].dt.year.value_counts().sort_index()
        print("\n每年的变更记录数量:")
        print(year_counts)
        
        return changes_df
    except Exception as e:
        print(f"获取历史变更数据时出错: {str(e)}", file=sys.stderr)
        raise

def process_historical_data(current_df, changes_df):
    """处理历史数据，重建每年的成分股列表"""
    try:
        # 初始化数据结构
        historical_components = {}
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 获取当前成分股列表
        current_companies = set(current_df['Symbol'].tolist())
        print(f"当前成分股数量: {len(current_companies)}")
        print("示例成分股:", list(current_companies)[:5])
        
        # 按照日期降序排序变更记录（从最近的开始）
        changes_df = changes_df.sort_values('Date', ascending=False)
        
        print(f"处理从{current_year}年到2000年的数据...")
        print(f"历史变更记录数量: {len(changes_df)}")
        
        # 从当前状态开始
        companies = current_companies.copy()
        
        # 初始化所有年份的成分股
        for year in range(current_year, 1999, -1):
            year_str = str(year)
            
            # 处理这一年发生的所有变更
            year_changes = changes_df[changes_df['Date'].dt.year == year]
            for _, change in year_changes.iterrows():
                # 如果有公司被添加，说明在这之前它不在列表中
                if pd.notna(change['Added']) and change['Added']:
                    companies.discard(change['Added'])
                
                # 如果有公司被移除，说明在这之前它在列表中
                if pd.notna(change['Removed']) and change['Removed']:
                    companies.add(change['Removed'])
            
            # 保存这一年的成分股列表
            historical_components[year_str] = sorted(list(companies))
            print(f"处理{year}年的数据，成分股数量：{len(companies)}")
            
            # 检查数量是否合理
            if len(companies) < 450 or len(companies) > 550:
                print(f"警告：{year}年的成分股数量（{len(companies)}）不在合理范围内！")
        
        return historical_components
    except Exception as e:
        print(f"处理历史数据时出错: {str(e)}", file=sys.stderr)
        raise

def save_results(data, filename='sp500_historical_components.json'):
    """保存结果到JSON文件"""
    try:
        output_dir = 'data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        filepath = os.path.join(output_dir, filename)
        
        # 将datetime对象转换为字符串
        formatted_data = {}
        for year, companies in data.items():
            formatted_data[year] = companies
        
        with open(filepath, 'w') as f:
            json.dump(formatted_data, f, indent=4)
        
        print(f"数据已保存到: {filepath}")
        
        # 打印一些统计信息
        print("\n数据统计：")
        print(f"总年份数量：{len(data)}")
        sample_year = list(data.keys())[0]
        print(f"示例年份（{sample_year}）的成分股数量：{len(data[sample_year])}")
    except Exception as e:
        print(f"保存结果时出错: {str(e)}", file=sys.stderr)
        raise

def main():
    try:
        print("开始获取标普500历史成分股数据...")
        
        # 获取当前成分股
        current_df = get_current_sp500_companies()
        print("已获取当前成分股列表")
        
        # 获取历史变更记录
        changes_df = get_historical_changes()
        print("已获取历史变更记录")
        
        # 处理数据
        historical_components = process_historical_data(current_df, changes_df)
        print("已处理历史数据")
        
        # 保存结果
        save_results(historical_components)
        
        print("处理完成！")
    except Exception as e:
        print(f"程序执行出错: {str(e)}", file=sys.stderr)
        sys.exit(1)

def check_company_in_year(data_file, company_symbol, year):
    """检查特定公司在特定年份是否在标普500中"""
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        if str(year) in data:
            companies = data[str(year)]
            is_present = company_symbol in companies
            print(f"{company_symbol} {'在' if is_present else '不在'} {year}年的标普500成分股中")
            return is_present
        else:
            print(f"没有{year}年的数据")
            return None
    except Exception as e:
        print(f"查询出错: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if len(sys.argv) == 4:
            check_company_in_year("data/sp500_historical_components.json", sys.argv[2], int(sys.argv[3]))
        else:
            print("用法: python sp500_historical_components.py --check <公司代码> <年份>")
    else:
        main() 