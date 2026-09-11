# 论文精读：{论文标题}

| | |
|---|---|
| 作者 | {作者} |
| 发表 | {会议/期刊 年份} |
| 链接 | {arXiv 或官方链接} |
| 类型 | {领域 · 子领域} |

**本 notebook 包含**：{实现了什么；验证了哪些结论；复现了哪些图}

**运行需求**：{依赖} · CPU 约 {N} 分钟 · 首次运行自动安装缺失依赖；不依赖外部图片、论文或数据文件

**提取说明**：原图来自 {arXiv LaTeX 源码 / MinerU / PDF 裁剪}

## 1. 环境设置

```python
# PAPER_NOTEBOOK_DEPENDENCY_BOOTSTRAP
import importlib.util
import subprocess
import random, sys, time

# Keep this map in sync with imports used by the notebook.
REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "matplotlib": "matplotlib",
}
missing = [
    pip_name
    for module_name, pip_name in REQUIRED_PACKAGES.items()
    if importlib.util.find_spec(module_name) is None
]
if missing:
    print("Installing missing packages:", ", ".join(missing))
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (7, 4), "axes.grid": True, "grid.alpha": 0.3})
print(f"Python {sys.version.split()[0]} | numpy {np.__version__} | matplotlib {matplotlib.__version__}")
```

## 2. TL;DR 与问题背景

**一句话总结**：{…}

### 2.1 问题是什么

{在这篇论文之前人们怎么做，痛点是什么，举具体例子}

### 2.2 核心洞察

{作者的关键想法}

![Figure 1: {图注中文}](extract/figures/figure_1_pN.png)

*图源：原论文 Figure 1*

**怎么看这张图**：{…}

## 3. 前置知识速补

> 熟悉 {X、Y} 的读者可以跳到第 4 节。

### 3.1 {概念}

{…}

## 4. 符号表

| 论文符号 | 含义 | 代码变量 | shape / 类型 |
|---|---|---|---|
| $…$ | … | `…` | … |

## 5. 方法详解

### 5.1 {组件 1}

**要解决的子问题**：{…}

**直觉**：{…}

**形式化**：

$$ … \tag{1}$$

- {逐项解释}

**为什么这样设计**：{…}

## 6. 核心实现

### 6.1 {组件 1}

```python
# 对应论文 §{x}，Eq. (1)
```

```python
# 小输入演示
```

```python
# 正确性检查
print("✓ all checks passed")
```

## 7. 验证实验

### 实验 1：{问题形式的标题}

**论文 claim**（§{x}）：{…}

**实验设置**：{…}

**预期**：{…}

```python
t0 = time.time()
# …
print(f"elapsed: {time.time() - t0:.1f}s")
```

**结果解读**：{基于实际输出：看到了什么 → 是否支持 claim → 意外之处}

## 8. 论文结果 vs 本 notebook

| 结论 / 指标 | 论文 | 本 notebook | 是否一致 | 差异原因 |
|---|---|---|---|---|
| … | … | … | ✅ / ⚠️ / ❌ / ➖ | … |

## 9. 批判性思考

### 9.1 隐含假设与失效场景

### 9.2 实验设计

### 9.3 审稿人可能会问

## 10. 自测题

**Q1.** {…}

<details><summary>点击查看答案</summary>

{…}

</details>

## 11. 延伸阅读

- **{文献}**：{为什么值得读}
