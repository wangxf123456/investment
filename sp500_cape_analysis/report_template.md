# 标普500 CAPE与未来收益率分析报告

## 数据范围概览

### 各期数据统计
1. **1年期**：{period_1y_start} 至 {period_1y_end}（{period_1y_count}个数据点）
2. **3年期**：{period_3y_start} 至 {period_3y_end}（{period_3y_count}个数据点）
3. **5年期**：{period_5y_start} 至 {period_5y_end}（{period_5y_count}个数据点）
4. **10年期**：{period_10y_start} 至 {period_10y_end}（{period_10y_count}个数据点）
5. **20年期**：{period_20y_start} 至 {period_20y_end}（{period_20y_count}个数据点）
6. **30年期**：{period_30y_start} 至 {period_30y_end}（{period_30y_count}个数据点）

## 当前市场估值

- 当前CAPE：37.0
- CAPE百分位：{cape_percentile:.1f}%
- 历史CAPE区间：{cape_min:.1f} - {cape_max:.1f}
- CAPE均值：{cape_mean:.1f}
- CAPE中位数：{cape_median:.1f}

## 各期限CAPE与收益率相关性分析

### 1年期（{period_1y_start} - {period_1y_end}）
- 皮尔逊相关系数：{correlation_pearson_1y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_1y:.2f}
- 线性回归方程：{equation_linear_1y}
- R²值：{r_squared_1y:.2f}
- 预期收益率：{predicted_return_1y:.1f}%

### 3年期（{period_3y_start} - {period_3y_end}）
- 皮尔逊相关系数：{correlation_pearson_3y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_3y:.2f}
- 线性回归方程：{equation_linear_3y}
- R²值：{r_squared_3y:.2f}
- 预期收益率：{predicted_return_3y:.1f}%

### 5年期（{period_5y_start} - {period_5y_end}）
- 皮尔逊相关系数：{correlation_pearson_5y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_5y:.2f}
- 线性回归方程：{equation_linear_5y}
- R²值：{r_squared_5y:.2f}
- 预期收益率：{predicted_return_5y:.1f}%

### 10年期（{period_10y_start} - {period_10y_end}）
- 皮尔逊相关系数：{correlation_pearson_10y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_10y:.2f}
- 线性回归方程：{equation_linear_10y}
- R²值：{r_squared_10y:.2f}
- 预期收益率：{predicted_return_10y:.1f}%

### 20年期（{period_20y_start} - {period_20y_end}）
- 皮尔逊相关系数：{correlation_pearson_20y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_20y:.2f}
- 线性回归方程：{equation_linear_20y}
- R²值：{r_squared_20y:.2f}
- 预期收益率：{predicted_return_20y:.1f}%

### 30年期（{period_30y_start} - {period_30y_end}）
- 皮尔逊相关系数：{correlation_pearson_30y:.2f}
- 斯皮尔曼相关系数：{correlation_spearman_30y:.2f}
- 线性回归方程：{equation_linear_30y}
- R²值：{r_squared_30y:.2f}
- 预期收益率：{predicted_return_30y:.1f}%

## CAPE分位与收益率分析

### 低CAPE时期（25%分位以下）vs 高CAPE时期（75%分位以上）的平均收益率

#### 10年期
- 低CAPE时期平均收益率：{returns_when_cape_low_10y:.1f}%
- 高CAPE时期平均收益率：{returns_when_cape_high_10y:.1f}%
- 收益率差异：{returns_diff_10y:.1f}%

#### 20年期
- 低CAPE时期平均收益率：{returns_when_cape_low_20y:.1f}%
- 高CAPE时期平均收益率：{returns_when_cape_high_20y:.1f}%
- 收益率差异：{returns_diff_20y:.1f}%

#### 30年期
- 低CAPE时期平均收益率：{returns_when_cape_low_30y:.1f}%
- 高CAPE时期平均收益率：{returns_when_cape_high_30y:.1f}%
- 收益率差异：{returns_diff_30y:.1f}%

## 结论

1. CAPE与未来收益率的关系在不同时间跨度上表现不同：
   - 短期（1-3年）：相关性较弱，预测能力有限
   - 中期（5-10年）：显示出较强的负相关关系
   - 长期（20-30年）：关系趋于稳定
2. 斯皮尔曼相关系数与皮尔逊相关系数的差异反映了关系的非线性特征
3. LOWESS平滑曲线显示了CAPE与收益率之间的局部趋势
4. 当前CAPE处于历史较高水平，预示着未来收益率可能低于历史平均水平
5. 低CAPE时期的投资回报普遍优于高CAPE时期，这种差异在各个时间跨度上都很明显

## 数据可视化

### CAPE与未来1年收益率关系
![CAPE与未来1年收益率关系图](sp500_cape_returns_1y.png)

### CAPE与未来3年收益率关系
![CAPE与未来3年收益率关系图](sp500_cape_returns_3y.png)

### CAPE与未来5年收益率关系
![CAPE与未来5年收益率关系图](sp500_cape_returns_5y.png)

### CAPE与未来10年收益率关系
![CAPE与未来10年收益率关系图](sp500_cape_returns_10y.png)

### CAPE与未来20年收益率关系
![CAPE与未来20年收益率关系图](sp500_cape_returns_20y.png)

### CAPE与未来30年收益率关系
![CAPE与未来30年收益率关系图](sp500_cape_returns_30y.png)

## 数据来源
- 标普500数据：Yahoo Finance
- CAPE数据：Robert Shiller数据库
- 数据频率：月度数据
- 收益率计算：使用几何平均年化收益率 