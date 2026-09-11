# 金融 / 量化 / 金融计量论文

包括：资产定价与因子模型（CAPM、Fama-French）、衍生品定价（Black-Scholes、Heston、局部波动率）、波动率建模（GARCH 族、realized volatility）、组合优化（Markowitz、Black-Litterman、风险平价）、市场微观结构（订单簿、Kyle 模型、最优执行 Almgren-Chriss）、交易策略与异象、风险度量（VaR、CVaR）、机器学习用于金融预测。

金融论文的特殊难点：**实证结论依赖真实数据，而 notebook 要求独立运行**；以及**回测里极易出现让结果虚高的错误**。

## 数据策略

默认用**已知真实参数的合成数据**。这不是妥协，而是一种更强的验证：你知道真值，所以能检验方法是否把真值找回来了。

| 论文内容 | 合成数据生成 |
|---|---|
| 期权定价、Monte Carlo | GBM、Heston、Merton jump-diffusion 路径 |
| 波动率模型 | 按已知参数模拟 GARCH(1,1) / EGARCH，再用论文方法估计 |
| 因子模型 | 设定因子收益和 loadings，加噪声生成资产收益 |
| 交易策略 / 异象 | 在随机游走中注入已知强度的信号（如弱动量、均值回归），检验策略能否检测到 |
| 市场微观结构 | 泊松到达的限价/市价单模拟订单簿 |
| regime 类 | 马尔可夫切换模型 |

需要展示真实数据时：

```python
def load_prices(ticker="SPY", start="2015-01-01"):
    """尝试下载真实数据；失败（无网络/无 yfinance）时返回合成 GBM 数据。两种情况后续代码都能运行。"""
    try:
        import yfinance as yf
        px = yf.download(ticker, start=start, progress=False, auto_adjust=True)["Close"].squeeze()
        if len(px) > 250:
            return px, "real"
    except Exception as e:
        print(f"real data unavailable ({type(e).__name__}); using synthetic GBM")
    n = 2500
    r = rng.normal(0.07 / 252, 0.18 / np.sqrt(252), n)
    idx = pd.bdate_range(start, periods=n)
    return pd.Series(100 * np.exp(np.cumsum(r)), index=idx), "synthetic"
```

打印数据来源，结论解读要区分"合成数据上的结果"和"真实数据上的结果"。

## 正确性检查

- **闭式解交叉验证**：Monte Carlo 定价 vs Black-Scholes 闭式解（报告 MC 标准误和 95% 置信区间是否覆盖闭式解）；数值 PDE vs 闭式解。
- **无套利关系**：put-call parity、期权价格对行权价单调且凸、隐含波动率可以反解回原价格。
- **参数恢复**：在合成数据上估计模型，检查估计值是否接近真值，样本量增大时误差是否缩小。
- **量纲与年化约定**：明确日收益/年化（252 个交易日）、简单收益 vs 对数收益、百分比 vs 小数。在符号表中写清楚，这是金融代码最常见的错误来源。
- **会计恒等式**：组合权重和为 1（或按论文约定）、组合收益 = 权重 · 资产收益、PnL 累加与净值一致。

## 回测规范（策略类论文）

回测中的错误几乎总是让结果**看起来更好**，因此必须主动防范，并在笔记中逐项说明如何处理：

- **Look-ahead bias**：t 时刻的信号只能用 t 时刻及之前的信息，在 t+1 执行。实现时用 `signal.shift(1)`，并写一个断言测试：把未来数据打乱，策略在 t 时刻的决策不应改变。
- **交易成本**：加入按换手率计算的成本，展示结果对成本假设的敏感性（成本 0、5、10、20 bps 下的 Sharpe）。
- **过拟合 / data snooping**：参数在样本内选择、在样本外评估（walk-forward）；尝试了多少种参数组合要说出来。可以演示：在纯随机游走上搜索足够多的参数，也能找到"显著"的策略。
- **幸存者偏差**：说明论文数据是否包含退市股票，合成数据中可以模拟退市来展示偏差大小。
- **统计显著性**：Sharpe ratio 的标准误（近似 $\sqrt{(1 + SR^2/2)/T}$，T 为年数时对应年化 SR）；多重检验下需要更高门槛。

## 验证实验设计

- **复现论文的核心表格**：在合成数据上用论文方法生成同结构的表格（例如因子回归的 alpha、t 统计量），与论文数值对比时说明数据不同，重点比较方向和显著性。
- **敏感性分析**：关键参数（窗口长度、再平衡频率、风险厌恶系数）扫描。
- **Regime 稳健性**：在不同波动率 regime 的合成数据上测试方法，看结论是否依赖特定市场环境。
- **模型误设**：数据来自模型 A、用模型 B 估计，会怎样？（例如真实数据有 jump，用 GBM 假设定价）

## 高价值可视化

- 净值曲线 + 回撤曲线（上下两个子图），标出样本内/样本外分界
- 隐含波动率微笑/曲面
- 有效前沿 + 各组合位置
- 收益分布直方图 vs 正态分布（展示肥尾），QQ 图
- 滚动窗口统计量（rolling Sharpe、rolling beta）
- 参数估计值随样本量的收敛（带真值参考线）

## 常见陷阱

- 金融论文常在 SSRN 或期刊发表，没有 arXiv 源码；表格多、公式排版常用 Word 生成，PyMuPDF 提取公式质量差，关键公式务必对照页面图核对。
- 不同论文对收益、波动率、利率的约定不一致（连续复利 vs 离散复利、年化方式），实现前先确认。
- 数值稳定性：协方差矩阵求逆用 `np.linalg.solve` 或加 shrinkage，不要直接 `inv`；小概率事件和极端行权价用 log 空间或 `scipy.stats` 的 `logsf`。
- 在 notebook 开头加一句说明：本 notebook 仅用于学习论文方法，不构成投资建议。