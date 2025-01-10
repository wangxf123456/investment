import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

class RealEstateDCF:
    def __init__(self):
        self.rental_income = 0
        self.operating_expenses = 0
        self.property_tax_rate = 0  # 房产税率
        self.property_value = 0     # 房产评估价值
        self.growth_rate = 0
        self.discount_rate = 0
        self.projection_years = 10
        self.terminal_cap_rate = 0
        
        # 获取当前文件所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

    def set_parameters(self, rental_income, operating_expenses, growth_rate,
                      discount_rate, projection_years=10, terminal_cap_rate=0.05,
                      property_tax_rate=0.012, property_value=0):
        """
        设置DCF计算所需的参数
        
        参数:
            rental_income (float): 年租金收入
            operating_expenses (float): 年运营支出
            growth_rate (float): 预期年增长率 (例如: 0.03 表示 3%)
            discount_rate (float): 贴现率 (例如: 0.08 表示 8%)
            projection_years (int): 预测年数
            terminal_cap_rate (float): 最终资本化率
            property_tax_rate (float): 房产税率 (例如: 0.012 表示 1.2%)
            property_value (float): 房产评估价值，如果为0则使用当前租金收入的20倍
        """
        self.rental_income = rental_income
        self.operating_expenses = operating_expenses
        self.growth_rate = growth_rate
        self.discount_rate = discount_rate
        self.projection_years = projection_years
        self.terminal_cap_rate = terminal_cap_rate
        self.property_tax_rate = property_tax_rate
        self.property_value = property_value if property_value > 0 else rental_income * 20

    def calculate_cash_flows(self):
        """计算每年的现金流"""
        cash_flows = []
        current_income = self.rental_income
        current_expenses = self.operating_expenses
        current_property_value = self.property_value

        for year in range(self.projection_years):
            # 计算房产税
            property_tax = current_property_value * self.property_tax_rate
            
            # 计算当年的净运营收入 (NOI)
            noi = current_income - current_expenses - property_tax
            cash_flows.append(noi)
            
            # 应用增长率
            current_income *= (1 + self.growth_rate)
            current_expenses *= (1 + self.growth_rate)
            current_property_value *= (1 + self.growth_rate)  # 房产价值也随增长率增长

        return cash_flows

    def calculate_terminal_value(self, final_year_noi):
        """计算终值"""
        return final_year_noi * (1 + self.growth_rate) / self.terminal_cap_rate

    def calculate_present_value(self):
        """计算现值"""
        cash_flows = self.calculate_cash_flows()
        terminal_value = self.calculate_terminal_value(cash_flows[-1])
        
        # 计算每年现金流的现值
        present_values = []
        for i, cf in enumerate(cash_flows):
            pv = cf / ((1 + self.discount_rate) ** (i + 1))
            present_values.append(pv)
        
        # 计算终值的现值
        terminal_value_pv = terminal_value / ((1 + self.discount_rate) ** self.projection_years)
        
        # 总现值
        total_value = sum(present_values) + terminal_value_pv
        return total_value, present_values, terminal_value_pv

    def print_report(self):
        """打印报告"""
        total_value, yearly_pvs, terminal_value_pv = self.calculate_present_value()
        print("\n=== 房地产DCF估值报告 ===")
        print(f"初始年租金收入: ¥{self.rental_income:,.2f}")
        print(f"初始年运营支出: ¥{self.operating_expenses:,.2f}")
        print(f"增长率: {self.growth_rate*100:.1f}%")
        print(f"贴现率: {self.discount_rate*100:.1f}%")
        print(f"预测年数: {self.projection_years}年")
        print(f"最终资本化率: {self.terminal_cap_rate*100:.1f}%")
        print("\n估值结果:")
        print(f"现金流现值总和: ¥{sum(yearly_pvs):,.2f}")
        print(f"终值现值: ¥{terminal_value_pv:,.2f}")
        print(f"总价值: ¥{total_value:,.2f}")

    def generate_report(self, save_markdown=True):
        """生成分析报告"""
        total_value, yearly_pvs, terminal_value_pv = self.calculate_present_value()
        
        # 控制台输出
        print("\n=== 房地产DCF估值报告 ===")
        print(f"初始年租金收入: ¥{self.rental_income:,.2f}")
        print(f"初始年运营支出: ¥{self.operating_expenses:,.2f}")
        print(f"增长率: {self.growth_rate*100:.1f}%")
        print(f"贴现率: {self.discount_rate*100:.1f}%")
        print(f"预测年数: {self.projection_years}年")
        print(f"最终资本化率: {self.terminal_cap_rate*100:.1f}%")
        print("\n估值结果:")
        print(f"现金流现值总和: ¥{sum(yearly_pvs):,.2f}")
        print(f"终值现值: ¥{terminal_value_pv:,.2f}")
        print(f"总价值: ¥{total_value:,.2f}")

        # 生成图表
        years = range(1, self.projection_years + 1)
        plt.figure(figsize=(10, 6))
        plt.bar(years, yearly_pvs, label='Present Value of Annual Cash Flow')
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.2)
        plt.xlabel('Year')
        plt.ylabel('Present Value (¥)')
        plt.title('DCF Cash Flow Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 保存图表
        if save_markdown:
            if not os.path.exists('reports'):
                os.makedirs('reports')
            plt.savefig('reports/dcf_chart.png')
        plt.show()
        
        if save_markdown:
            self._generate_markdown_report(total_value, yearly_pvs, terminal_value_pv)

    def _generate_markdown_report(self, total_value, yearly_pvs, terminal_value_pv):
        """生成Markdown格式的报告"""
        # 创建现金流数据表格
        cash_flow_table = "| 年份 | 现金流现值 |\n|------|------------|\n"
        for year, pv in enumerate(yearly_pvs, 1):
            cash_flow_table += f"| {year} | ¥{pv:,.2f} |\n"

        # 计算年度房产税
        annual_property_tax = self.property_value * self.property_tax_rate

        # 准备报告数据
        report_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rental_income': self.rental_income,
            'operating_expenses': self.operating_expenses,
            'property_tax_rate': self.property_tax_rate * 100,
            'property_value': self.property_value,
            'annual_property_tax': annual_property_tax,
            'growth_rate': self.growth_rate * 100,
            'discount_rate': self.discount_rate * 100,
            'projection_years': self.projection_years,
            'terminal_cap_rate': self.terminal_cap_rate * 100,
            'total_cash_flows': sum(yearly_pvs),
            'terminal_value': terminal_value_pv,
            'total_value': total_value,
            'cash_flow_table': cash_flow_table
        }

        # 读取模板文件（使用绝对路径）
        template_path = os.path.join(self.script_dir, 'report_template.md')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"错误：找不到报告模板文件 '{template_path}'")
            return

        # 使用模板生成报告
        report_content = template.format(**report_data)
        
        # 保存报告（使用绝对路径）
        reports_dir = os.path.join(self.script_dir, 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            
        report_path = os.path.join(reports_dir, 'dcf_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\nMarkdown报告已生成在 {report_path}")

def main():
    # 使用示例
    dcf = RealEstateDCF()
    
    # 设置参数（示例数据）
    dcf.set_parameters(
        rental_income=2600*12,        # 年租金收入：7.2万
        operating_expenses=500,     # 年运营支出：0.1万
        growth_rate=0.0,            # 增长率：0%
        discount_rate=0.015,        # 贴现率：4.5%
        projection_years=50,        # 预测期：50年
        terminal_cap_rate=0.05,     # 最终资本化率：5%
        property_tax_rate=0.0,    # 房产税率：1.2%
        property_value=2600*12*20      # 房产评估价值：144万（约为年租金的20倍）
    )
    
    # 生成报告
    # dcf.print_report()
    dcf.generate_report(save_markdown=True)

if __name__ == "__main__":
    main() 