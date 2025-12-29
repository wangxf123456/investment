# 标普500 Forward PE与未来收益率分析报告

## 数据范围概览

### 各期数据统计
1. **1年期**：{period_1y_start} 至 {period_1y_end}（{period_1y_count}个数据点）
2. **3年期**：{period_3y_start} 至 {period_3y_end}（{period_3y_count}个数据点）
3. **5年期**：{period_5y_start} 至 {period_5y_end}（{period_5y_count}个数据点）
4. **10年期**：{period_10y_start} 至 {period_10y_end}（{period_10y_count}个数据点）
5. **20年期**：{period_20y_start} 至 {period_20y_end}（{period_20y_count}个数据点）

## 当前市场估值

- 当前Forward PE：{current_pe:.1f}
- Forward PE百分位：{pe_percentile:.1f}%
- 历史Forward PE区间：{pe_min:.1f} - {pe_max:.1f}
- Forward PE均值：{pe_mean:.1f}
- Forward PE中位数：{pe_median:.1f}

## Forward PE与CAPE的区别

| 指标 | Forward PE | CAPE (席勒市盈率) |
|------|-----------|------------------|
| 定义 | 当前价格 / 未来12个月预期盈利 | 当前价格 / 过去10年平均通胀调整盈利 |
| 时间视角 | 前瞻性 | 回顾性 |
| 优点 | 反映市场对未来的预期 | 平滑经济周期影响，更稳定 |
| 缺点 | 预期可能不准确 | 可能滞后于结构性变化 |
| 适用场景 | 短期估值判断 | 长期估值比较 |

## 各期限Forward PE与收益率相关性分析

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

## Forward PE分位与收益率分析

### 低Forward PE时期（25%分位以下）vs 高Forward PE时期（75%分位以上）的平均收益率

#### 5年期
- 低PE时期平均收益率：{returns_when_pe_low_5y:.1f}%
- 高PE时期平均收益率：{returns_when_pe_high_5y:.1f}%
- 收益率差异：{returns_diff_5y:.1f}%

#### 10年期
- 低PE时期平均收益率：{returns_when_pe_low_10y:.1f}%
- 高PE时期平均收益率：{returns_when_pe_high_10y:.1f}%
- 收益率差异：{returns_diff_10y:.1f}%

#### 20年期
- 低PE时期平均收益率：{returns_when_pe_low_20y:.1f}%
- 高PE时期平均收益率：{returns_when_pe_high_20y:.1f}%
- 收益率差异：{returns_diff_20y:.1f}%

## 结论

1. **Forward PE与未来收益率的预测能力**：
   - 短期（1-3年）：Forward PE对短期收益的预测能力较弱，市场短期走势受多种因素影响
   - 中期（5-10年）：开始显示一定的负相关关系，高估值倾向于带来较低的未来收益
   - 长期（10-20年）：Forward PE对长期收益有一定的预测作用

2. **Forward PE vs CAPE**：
   - Forward PE更关注市场对未来的预期，适合判断短期市场情绪
   - CAPE更稳定，对长期收益的预测能力通常更强
   - 两者结合使用可以获得更全面的估值视角

3. **当前市场状况**：
   - 当前Forward PE处于历史{pe_percentile:.0f}%分位
   - 基于历史关系，预期未来10年年化收益率约为{predicted_return_10y:.1f}%

4. **投资建议**：
   - 低Forward PE时期的投资回报普遍优于高Forward PE时期
   - 投资者应结合多个估值指标（Forward PE、CAPE、股息收益率等）进行综合判断
   - 估值只是投资决策的一个因素，还需考虑宏观经济、利率环境等

## 数据可视化

### 标普500指数与Forward PE历史走势对比
![标普500与Forward PE历史走势](sp500_forward_pe_history.png)

### Forward PE与未来1年收益率关系
![Forward PE与未来1年收益率关系图](sp500_forward_pe_returns_1y.png)

### Forward PE与未来3年收益率关系
![Forward PE与未来3年收益率关系图](sp500_forward_pe_returns_3y.png)

### Forward PE与未来5年收益率关系
![Forward PE与未来5年收益率关系图](sp500_forward_pe_returns_5y.png)

### Forward PE与未来10年收益率关系
![Forward PE与未来10年收益率关系图](sp500_forward_pe_returns_10y.png)

### Forward PE与未来20年收益率关系
![Forward PE与未来20年收益率关系图](sp500_forward_pe_returns_20y.png)

## 数据来源
- 标普500价格数据：Yahoo Finance
- Forward PE数据：基于Shiller数据库的盈利数据计算
- 数据频率：月度数据
- 收益率计算：使用几何平均年化收益率
- 注意：历史Forward PE为估算值，基于历史盈利增长率计算预期盈利

