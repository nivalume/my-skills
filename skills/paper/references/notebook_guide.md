# 论文笔记写作指南

本指南同时适用于 Markdown 与 notebook。先从用户请求解析 `output`（默认 `markdown`）和 `language`（默认 `zh`），再按目标语言撰写所有面向读者的文字。图表内部文字始终使用英文。

目录：
1. 整体结构
2. 各节写法
3. 笔记写作风格
4. 公式与代码对应
5. 原图嵌入
6. 自绘解释图
7. 实验与结果对照
8. 篇幅与节奏

---

## 1. 整体结构

```
0. 标题 + 论文信息 + 本笔记导读
1. 环境设置
2. TL;DR 与问题背景
3. 前置知识速补（按需）
4. 符号表
5. 方法详解（可拆成多个 5.x 小节）
6. 核心实现
7. 验证实验
8. 论文结果 vs 本笔记
9. 批判性思考
10. 自测题
11. 延伸阅读
```

第 5 节和第 6 节可以交织：讲完一个组件就立刻实现它，通常比"先全部讲完再全部实现"更好理解。组件之间耦合很紧的论文（例如一个完整的共识协议）适合先讲整体再逐块实现。按论文特点选择，不要机械套用。

## 2. 各节写法

### 0. 标题与导读

```markdown
# 论文精读：In Search of an Understandable Consensus Algorithm (Raft)

| | |
|---|---|
| 作者 | Diego Ongaro, John Ousterhout |
| 发表 | USENIX ATC 2014 |
| 链接 | arXiv / 官网链接 |
| 类型 | 分布式系统 · 共识算法 |

**本笔记包含**：Raft leader election 与 log replication 的完整离散事件模拟实现；
随机故障注入下对 5 条 safety property 的验证；复现论文 Figure 15 的选举耗时分布。

**运行需求**：numpy, matplotlib · CPU 约 2 分钟
```

notebook 模式再补充“首次运行自动安装缺失依赖；不依赖外部图片、论文或数据文件”。Markdown 模式不要声称回复中的代码会自动安装依赖。

### 1. 环境设置

notebook 模式的第一个代码单元格必须先用当前 kernel 的 `sys.executable -m pip` 安装缺失依赖，再导入全部依赖、打印版本、固定随机种子、设置绘图默认样式。把实际使用的 import module 与 pip 包名维护在 `REQUIRED_PACKAGES` 中；不要写死 `pip` 或使用另一个 Python。Markdown 模式只列出运行代码所需依赖，不包含自动安装单元格。

```python
# PAPER_NOTEBOOK_DEPENDENCY_BOOTSTRAP
import importlib.util
import subprocess
import random, sys

REQUIRED_PACKAGES = {"numpy": "numpy", "matplotlib": "matplotlib"}
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

### 2. TL;DR 与问题背景

三部分：
- **一句话总结**：这篇论文做了什么，为什么重要。
- **问题是什么**：在它之前，人们怎么做？痛点在哪？用具体例子说明，而不是抽象描述。
- **核心洞察**：作者的关键想法是什么。好的洞察通常能用一两句话说清，例如 Raft 的"用 strong leader 和 randomized timeout 把共识问题分解成可独立理解的子问题"。

这一节通常配论文的概览图（Figure 1 或架构图）。

### 3. 前置知识速补

只补**读懂这篇论文真正需要的**，每项 1–3 段，能用小代码演示就用代码演示。不要写成教科书章节。读者如果已经懂，可以直接跳过，所以这一节开头说明"熟悉 X、Y 的读者可跳过"。

### 4. 符号表

把论文的符号映射到代码变量名，这是读论文和读代码之间的桥梁。

```markdown
| 论文符号 | 含义 | 代码变量 | shape / 类型 |
|---|---|---|---|
| $d_{model}$ | 模型隐藏维度 | `d_model` | int |
| $Q, K, V$ | query / key / value 矩阵 | `Q, K, V` | `(batch, seq, d_k)` |
| $\text{currentTerm}$ | 节点见过的最大 term | `self.current_term` | int |
```

### 5. 方法详解

每个组件按这个顺序讲：
1. **要解决什么子问题**（动机）
2. **直觉**：不用公式，用类比、小例子或图说明它怎么工作
3. **形式化**：公式或伪代码，逐项解释每个符号
4. **为什么这样设计**：有没有别的做法？作者为什么不选？（论文里常有答案，找出来）

### 6. 核心实现

- 一个类/函数对应论文的一个组件，docstring 写明对应论文的哪一节/哪个公式。
- 关键行尾注释公式编号：`scores = Q @ K.T / np.sqrt(d_k)  # Eq. (1)`
- 实现后立刻跟一个**小的演示单元格**：用手算可验证的小输入跑一遍，打印中间结果。
- 实现后跟**正确性检查**单元格（assert），并打印 "✓ all checks passed" 之类的明确信号。
- **长类拆分到多个单元格**：一个类有很多方法时（例如协议节点、复杂数据结构），不要塞进一个 200 行的单元格。用一个小装饰器把方法分散定义，每个方法前穿插对应论文段落的讲解：

  ```python
  def add_to(cls):
      def deco(fn):
          setattr(cls, fn.__name__, fn)
          return fn
      return deco

  @add_to(RaftNode)
  def on_RequestVote(self, m):
      ...
  ```

- **标注实现选择**：论文未明确之处用 `> ⚠️ 论文未明确：...`，为 toy 规模做的简化用 `> 🔧 简化：...`，写在对应代码单元格的前后。

### 7. 验证实验

每个实验单元格组前面用一个 markdown 单元格写明：

```markdown
### 实验 2：随机化超时能否避免 split vote？

**论文 claim**（§5.2, Figure 15）：选举超时在 150–300ms 范围内随机化后，leader 通常能在几百毫秒内选出；
超时范围太窄时会反复出现 split vote。

**实验设置**：5 节点，模拟 leader 崩溃 1000 次，比较超时范围 150–151ms 与 150–300ms。

**预期**：窄范围的选举耗时分布有长尾。
```

实验跑完后，紧跟一个 markdown 单元格解读结果：**看到了什么 → 是否支持 claim → 有什么意外**。解读必须基于实际输出，先跑再写。

### 8. 论文结果 vs 本笔记

```markdown
| 结论 / 指标 | 论文 | 本笔记 | 是否一致 | 差异原因 |
|---|---|---|---|---|
| 选举超时 150–300ms 时 leader 选出耗时 | 多数 < 300ms | 中位数 212ms | ✅ 定性一致 | 模拟网络延迟分布与真实环境不同 |
| BLEU on WMT14 EN-DE | 28.4 | 未复现 | ➖ | 需要大规模训练，toy 实验只验证了机制 |
```

### 9. 批判性思考

避免空泛的"本文也存在一定局限性"。回答具体问题：
- 方法依赖哪些**隐含假设**？在什么场景下会失效？（最好用笔记里的代码构造一个失效例子）
- 实验设计有没有漏洞？baseline 是否公平？
- 如果你是审稿人，会问哪 2–3 个问题？
- 后续工作（如果了解）改进了什么？

### 10. 自测题

3–6 道，覆盖概念理解和实现细节。答案用可折叠的 HTML，Jupyter 中能正常渲染：

```markdown
**Q1.** 为什么 Raft 要求 leader 只能通过当前 term 的日志条目来提交之前 term 的条目？

<details><summary>点击查看答案</summary>

参考 Figure 8 的场景：……

</details>
```

也可以出"改代码题"：例如"把 `election_timeout` 改成固定值重新运行实验 2，你预期会看到什么？"

### 11. 延伸阅读

3–5 条，每条一句话说明为什么值得读。不确定是否存在的文献不要写。

## 3. 笔记写作风格

- **使用目标语言，术语可保留英文**：`language=zh` 时写 “attention”“log replication”“Sharpe ratio”，不要硬译；其他语言也遵循该语言的自然表达习惯。术语第一次出现时可以用目标语言解释。
- **先直觉后公式**。读者看到公式之前，应该已经大致知道它想表达什么。
- **用"你"和读者对话**，语气像一位耐心的学长讲解，不像论文翻译。
- **具体胜过抽象**。"leader 崩溃后，S2 和 S3 同时超时，各自拿到 2 票，谁也没过半"比"可能出现选票分裂"好理解得多。
- **不要逐段翻译论文**。重组内容，按理解顺序讲。

对比示例：

> ❌ 本文提出了一种新的注意力机制，该机制通过缩放点积的方式计算注意力权重，有效提升了模型性能。
>
> ✅ 点积 $q \cdot k$ 衡量 query 和 key 有多"对齐"。但维度 $d_k$ 很大时，点积的方差也会随 $d_k$ 线性增长（下面的代码会验证这一点），softmax 会被推到饱和区，梯度几乎为零。除以 $\sqrt{d_k}$ 正好把方差拉回 1。

## 4. 公式与代码对应

对于核心公式，用"公式 → 逐项拆解 → 代码"的三段式：

```markdown
$$\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V \tag{1}$$

- $QK^\top$：每个 query 和每个 key 的相似度，shape `(n_q, n_k)`
- $/\sqrt{d_k}$：方差归一化（原因见上）
- softmax 按行：每个 query 对所有 key 的权重和为 1
- 乘 $V$：按权重加权求和 value
```

代码中保持相同的分解顺序，每一步一行，行尾标注。

## 5. 原图使用

notebook 模式的源 Markdown 可以引用临时工作空间 `$PAPER_DIR/extract/figures/` 下的本地图片，但最终 `.ipynb` 必须只使用 notebook 内的 base64 数据。`build_notebook.py` 会把每个本地图片字节写入对应 Markdown cell 的 `attachments`，并把引用改成 `attachment:<name>`；不要在交付文件中留下 `extract/`、`figures/` 或其他相对图片路径，也不要使用远程图片 URL。当前工作目录只保留最终 `.ipynb`。

Markdown 模式直接在回复中交付内容，不得引用 `$PAPER_DIR` 或 `extract/figures/...`。如果没有稳定且可访问的图片 URL，用目标语言概述图中的关键观察并注明论文图号，不要输出失效的本地图片链接。

格式：

```markdown
![Figure 7: 新 leader 上任时 follower 日志可能出现的各种情况](extract/figures/figure_7_p7.png)

*图源：原论文 Figure 7*

**怎么看这张图**：每一行是一个 follower 的日志，方框里的数字是 term。注意 (d) 比 leader 多出了
term 7 的条目，(f) 则有 leader 从未见过的 term 2、3 条目。Raft 的处理方式是让 leader 强制覆盖
follower 的冲突日志，下面 6.3 节的 `append_entries` 实现正是这个逻辑。
```

每张原图都要有目标语言的“怎么看这张图”说明，指出读者该关注的具体细节，并尽量连接到后面的代码。

notebook 模式交付前用 `python <skill-dir>/scripts/build_notebook.py check <output>.ipynb` 检查 `embedded_images`、base64 attachment、引用完整性和 `dependency_bootstrap`。本节“只保留最终 `.ipynb`”指论文内容与图片；涉及 LLM 时，共享配置文件与执行要求见 [llm_notebooks.md](llm_notebooks.md)。

## 6. 自绘解释图

每张图只传达**一个信息**，在图前的 markdown 里说明这张图要看什么。

约定：
- 图中文字全部英文（标题、坐标轴、图例），避免非英文字体兼容问题
- 坐标轴带单位；对数坐标要明确标注
- 比较多组结果时用多个随机种子，画均值 ± 标准差（`fill_between`）
- 重复用到的画图逻辑封装成小函数，放在实现部分附近
- 优先选择能揭示机制的图：中间状态可视化、参数扫描、有/无关键组件的对比，而不是只画最终 loss

常用的高价值图：
- **机制可视化**：数据结构的状态演变、attention 热力图、消息时序图
- **参数扫描**：关键超参数 vs 指标，看出论文选择的合理性
- **消融对比**：去掉论文的关键设计后发生了什么
- **理论 vs 经验**：理论界/复杂度曲线与实测散点画在同一张图上

## 7. 实验与结果对照

- 实验规模要让单个实验在几十秒内完成。需要多次运行时减少规模而不是减少重复次数。
- 耗时较长的实验在单元格开头打印预计时间，结尾打印实际耗时。
- 结果数字用 `print(f"...")` 格式化输出，便于读者对照 markdown 里的解读。
- 实验结果与预期不符时，不要调参直到"符合预期"然后隐瞒。如实记录，分析原因（toy 规模不够？实现有误？论文 claim 依赖特定条件？）。
- **统计口径要有意义**：例如同一个错误在后续每一步都会被重复检测到时，统计"出现错误的运行次数"比统计"错误事件总数"更能说明问题。
- **检查画出来的图**：构建后把输出中的图片保存下来逐张查看，常见问题有图例遮挡数据、对数坐标下曲线缺失（值为 inf 或 0）、子图坐标范围不一致导致无法对比。

## 8. 篇幅与节奏

- notebook 模式的一般论文：60–120 个单元格，markdown 与代码大约各半。
- Markdown 模式保持同样的章节与验证深度，但直接输出连续 Markdown，不使用 cell 分隔标记或 notebook 专属操作说明。
- notebook 模式中，单个 markdown 单元格不超过一屏；单个代码单元格尽量不超过 40 行，长实现拆成多个单元格，中间穿插说明。
- notebook 模式避免连续三个以上的代码单元格没有任何文字说明。
