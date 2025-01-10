# 标普500席勒市盈率与收益率分析

这个项目分析了标普500的席勒市盈率（CAPE）与未来10年收益率之间的关系。

## 功能
- 获取标普500历史数据
- 获取Robert Shiller的CAPE数据
- 计算10年期年化收益率
- 生成CAPE与收益率的散点图和趋势线

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法
直接运行Python脚本：
```bash
python sp500_cape_returns.py
```

脚本会自动下载数据并生成一个名为`sp500_cape_returns.png`的图表文件。

## 数据来源
- 标普500数据：Yahoo Finance
- CAPE数据：Robert Shiller的数据库 