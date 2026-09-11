---
name: paper
description: 精读学术论文并生成可独立分享、可独立运行的 Jupyter notebook (.ipynb)。高质量提取 PDF 文字与原图（arXiv LaTeX 源码 / MinerU / PyMuPDF 矢量图裁剪），将图片以 base64 attachment 压入 notebook，并在第一个代码单元格自举缺失依赖。用中文笔记（术语保留英文）讲解，从零实现核心算法与数据结构，并用 Python 画图和实验验证论文结论。覆盖深度学习、算法与数据结构、系统/数据库/分布式、理论与数学推导、量化金融论文。只要用户想读懂、精读、复现、实现或学习一篇论文，或者上传论文 PDF、给出 arXiv 链接/编号并说“帮我读一下”“讲讲这篇论文”“复现这个算法”“做个论文笔记”，都应使用此 skill，即使用户没有提到 notebook。Also use for requests like read/study/reproduce/implement a research paper, paper walkthrough, or turn a paper into a notebook.
---

# Paper → Notebook

目标：把一篇论文变成一个**单文件、可在任何电脑上独立运行**的 `.ipynb`。读者打开它，从上到下运行，就能理解论文在解决什么问题、方法为什么成立、核心算法怎么实现，并亲眼看到代码实验验证了论文的哪些结论（以及哪些没能验证）。

笔记是给人学习用的，不是论文翻译。好的笔记会先讲直觉和动机，再讲公式；会指出论文没说清楚的地方；会诚实交代简化了什么。

## 先判断：用户要的是完整 notebook 吗？

完整流程耗时较长（通常几十分钟）。如果用户只是问一个关于论文的具体问题（"这篇的主要贡献是什么""公式 3 怎么推出来的"），直接回答，然后一句话提出可以生成完整的学习 notebook。用户明确要读论文、做笔记、复现、实现时，走下面的完整流程。

如果论文是综述或包含大量独立方法，先问用户重点关注哪部分，而不是全部实现。

## 工作流

```
1. 获取与提取   → scripts/extract_paper.py
2. 质检提取结果 → 必须亲眼看图和关键公式
3. 精读与规划   → 按论文类型读 references/paper_types/*.md，写 plan.md
4. 编写 notebook 源文件（Markdown），代码边写边跑
5. 构建 + 隔离执行 + 修复 → scripts/build_notebook.py --execute
6. 交付前自查
```

临时工作空间约定：本流程产生的提取结果、模型缓存、页面图、规划文件和 Notebook 源文件全部放在系统临时目录，禁止写入用户当前工作目录。开始时创建一个任务专属目录，并在当前任务上下文中保留它的绝对路径：

```bash
PAPER_SLUG="raft"
PAPER_TMP="$(mktemp -d "${TMPDIR:-/tmp}/paper-notebook.XXXXXX")"
PAPER_DIR="$PAPER_TMP/$PAPER_SLUG"
mkdir -p "$PAPER_DIR"
```

后续所有 `extract_paper.py`、人工修图、`plan.md`、`notebook.md` 和分段 Markdown 的路径都必须位于 `$PAPER_DIR` 下。构建器唯一写入当前工作目录的文件是最终的 `$PWD/${PAPER_SLUG}_notes.ipynb`；不要在当前目录创建任何中间目录或文件，包括提取目录、Markdown、图片、日志或 checkpoint。验证交付物后删除整个 `$PAPER_TMP`；若需要保留中间结果供排查，只保留在临时目录，不要复制到当前目录。`paper-slug` 用简短英文，如 `raft`、`attention-is-all-you-need`。

### 1. 获取与提取

```bash
python <skill-dir>/scripts/extract_paper.py <PDF路径 | arXiv编号 | arXiv链接> -o "$PAPER_DIR/extract"
```

`--engine auto` 会按以下顺序尝试，并自动互补：

1. **arXiv LaTeX 源码**（输入是 arXiv 编号/链接时）：拿到作者上传的原始图片文件和一字不差的公式、图注。这是质量最高的来源，能用就用。TikZ 画的图和表格没有图片文件，会自动回退到 PDF 裁剪。
2. **MinerU**（本机已安装 `mineru` 命令时）：版面分析 + LaTeX 公式识别 + HTML 表格 + OCR。GPU 和 Apple Silicon 会自动加速。
3. **PyMuPDF**（总是可用）：以图注为锚点裁剪图区域。关键点在于论文里大量配图是**矢量图**，在 PDF 内部是绘图指令而不是图片对象，直接提取图片会漏掉它们，所以要按区域渲染。

用户只给了论文标题时，先搜索找到 arXiv 编号或 PDF。非 arXiv 来源（期刊、SSRN、会议官网）只有 PDF，走 2 或 3。

MinerU 的安装、Mac/GPU 配置、模型下载问题见 `references/extraction.md`。如果 MinerU 没装且论文公式很多，告诉用户安装它能明显提升公式质量，但不要因此停下来，先用 PyMuPDF 继续。

输出（所有引擎一致）：

| 文件 | 内容 |
|---|---|
| `paper.md` | 全文。MinerU 输出含 LaTeX 公式；PyMuPDF 输出的公式常常是乱码 |
| `latex/main_flat.tex` | arXiv 源码，所有 `\input` 已展开。**有它时，公式以它为准** |
| `figures/` + `figures.json` | 图表文件、图号、图注、页码、bbox |
| `figures_overview.png` | 所有图的缩略图总览 |
| `pages/page_NNN.png` | 每页渲染图（110 dpi），用于视觉核对 |
| `extraction_report.json` | 使用的引擎、是否扫描件、警告 |

### 2. 质检提取结果

提取工具都会出错，而错误的图和公式会让后面的笔记和代码全部建立在错误基础上，所以这一步不能跳过。

- **读 `extraction_report.json` 的 warnings。**
- **查看 `figures_overview.png`**（用图片查看工具真正看一眼）。检查有没有裁掉一半、混进正文、漏图。对照 `paper.md` 里出现过的所有 "Figure N"，确认没有遗漏关键图。
- **修复有问题的图**：先看对应页面 `pages/page_NNN.png` 定位区域，再手动裁剪。页面图是 110 dpi，像素坐标换算成 PDF 坐标：`pt = px × 72 / 110`。
  ```bash
  python <skill-dir>/scripts/extract_paper.py crop "$PAPER_DIR/extract/paper.pdf" --page 5 --bbox 320 80 545 175 -o "$PAPER_DIR/extract/figures/figure_4_fixed.png"
  python <skill-dir>/scripts/extract_paper.py render "$PAPER_DIR/extract/paper.pdf" --pages 5 --dpi 200 -o "$PAPER_DIR/extract/hires"   # 需要看清细节时
  ```
- **核对关键公式**：对于将要实现的每个核心公式，打开它所在页面的渲染图亲眼确认（上下标、求和范围、转置、负号最容易错）。有 LaTeX 源码时直接用源码。
- **扫描件**（report 里 `scanned: true`）：没有文字层。有 MinerU 就用它 OCR；否则直接逐页查看 `pages/` 图像来阅读，必要时用更高 dpi 渲染。

### 3. 精读与规划

通读全文（不要只读摘要和方法部分，实验和附录里常有关键的实现细节和超参数）。然后判断论文类型，**阅读对应的参考文件**，它们包含该类论文的验证策略和常见陷阱：

| 类型 | 文件 |
|---|---|
| 深度学习 / 模型架构 | `references/paper_types/deep_learning.md` |
| 经典算法 / 数据结构 / 概率数据结构 | `references/paper_types/algorithms.md` |
| 系统 / 数据库 / 分布式 | `references/paper_types/systems.md` |
| 理论 / 数学推导 / 统计 | `references/paper_types/theory.md` |
| 金融 / 量化 / 金融计量 | `references/paper_types/finance.md` |

一篇论文常常横跨多类（例如带收敛性证明的优化器论文 = 深度学习 + 理论），读所有相关的文件。

然后写 `$PAPER_DIR/plan.md`，内容简短即可：

- **一句话核心思想**，以及读者需要的前置知识
- **要实现的组件**：每个对应论文的哪个公式/算法编号
- **验证实验清单**：每个实验对应论文的哪个 claim，toy 规模设置，预估运行时间
- **要嵌入的原图**：挑 3–8 张最有助于理解的，不是全部
- **要自绘的解释图**：每张图想让读者看懂什么

规划的价值在于确保每个实验都在验证论文的某个具体说法，而不是为了画图而画图。

### 4. 编写 notebook 源文件

复制 `assets/notebook_template.md` 为 `$PAPER_DIR/notebook.md` 作为骨架，然后逐节填写。**写之前先读 `references/notebook_guide.md`**，里面有每一节的写法、示例和格式约定。

源文件格式（由 `build_notebook.py` 编译）：

- 普通 Markdown → markdown 单元格；每个标题行（`#`–`####`）或单独一行 `<!-- cell -->` 处开始新单元格
- ` ```python ` 代码块 → 可执行代码单元格
- 其他语言的代码块（` ```text `、` ```pseudo `）→ 保留在 markdown 中，不执行
- `![图注](extract/figures/xxx.png)` 本地图片 → 自动转成 base64 后写入对应 Markdown cell 的 `attachments`，并改写为 `attachment:<name>`；交付的 ipynb 不得依赖外部图片路径或远程 URL

第一个代码单元格必须包含 `PAPER_NOTEBOOK_DEPENDENCY_BOOTSTRAP`：维护实际 import module 到 pip 包名的映射，使用当前 kernel 的 `sys.executable -m pip install` 安装缺失依赖，然后再导入依赖。缺依赖且无网络时要让安装错误明确失败，不能静默跳过。

**代码边写边跑。** 每写完一个实现或实验，就把相关代码拼到一个临时 `.py` 里运行确认，而不是写完几百行再统一调试。

**先跑实验，再写解读。** 实验结果（数字、曲线形状）要先跑出来再写对应的解读文字，不要凭预期写结论。实用做法：写实验代码时，在解读位置先放 `{{INTERP_实验名}}` 这样的占位符；构建执行后读取输出、查看生成的图，再替换占位符。构建前确认没有残留的 `{{`。

**长 notebook 分段写。** 源文件较长时，按章节写成 `$PAPER_DIR/part1.md`、`$PAPER_DIR/part2.md`… 再合并成 `$PAPER_DIR/notebook.md`。每完成一两个部分就构建执行一次，尽早发现错误。

实现原则：

- **忠于论文。** 变量名尽量沿用论文符号（`W_q`、`beta1`），在注释里标公式编号，如 `# Eq. (3)`。
- **论文没说清的地方**，自己做合理选择，并在笔记里用 `> ⚠️ 论文未明确：...` 标出你的选择和理由。
- **为了 toy 规模做的简化**，用 `> 🔧 简化：...` 标出，并说明对结论可能的影响。
- 可以参考官方代码来消除歧义，但实现应从论文出发，并在笔记中说明参考了什么。

### 5. 构建、隔离执行、修复

```bash
python <skill-dir>/scripts/build_notebook.py "$PAPER_DIR/notebook.md" -o "$PWD/${PAPER_SLUG}_notes.ipynb" --execute
python <skill-dir>/scripts/build_notebook.py check "$PWD/${PAPER_SLUG}_notes.ipynb"
```

脚本会在一个**空的临时目录**里执行 notebook，因此任何偷偷依赖本地文件的代码都会报错，这正是我们要的效果。输出 JSON 中 `ok: true` 才算通过。报错就修改 `notebook.md` 后重新构建，直到通过。同时检查报告中的 `exec_seconds`、`plot_outputs`、`embedded_images`、`dependency_bootstrap` 和 `invalid_attachments` 是否合理。图片 attachment 必须是可解码的 base64，Markdown 中不能留下外部图片引用。

### 6. 交付前自查

- [ ] `build_notebook.py --execute` 报告 `ok: true`，无警告或警告已处理
- [ ] 每个核心公式/算法都有对应实现，且代码注释标注了公式编号
- [ ] 每个验证实验都写明对应论文的哪个 claim，并对结果给出了解读（包括与预期不符的情况）
- [ ] 有"论文结果 vs 本 notebook 结果"对照，差异给出了原因
- [ ] 所有简化和论文未明确之处都已标注
- [ ] 嵌入的原图都有中文说明"这张图该看什么"
- [ ] 批判性思考部分不是空话，指向了这篇论文具体的假设和局限
- [ ] 自测题答案和解读中的每个具体断言（"会发生 X""数值约为 Y"）都实际运行验证过
- [ ] 查看过所有自绘图的实际渲染结果（图例遮挡、坐标范围、空白子图）
- [ ] 全文中文，术语保留英文
- [ ] 本次流程在当前目录只新增了最终 `.ipynb`，所有中间文件仍在 `$PAPER_TMP` 并已按需清理

交付时向用户简要说明：用了哪个提取引擎、实现了哪些内容、哪些论文结论得到了验证、哪些没有及原因、运行时长和依赖。

## 独立运行的硬性要求

这些要求的共同目的是：用户把 `.ipynb` 发给任何人，对方打开就能跑。

- **不依赖外部论文、图片或数据文件。** 原图必须由构建器压入 notebook 的 base64 attachments；实验数据在 notebook 内合成或生成。真实数据下载只能作为可选增强，失败时自动回退到合成数据。
- **依赖可自举。** 第一个代码单元格必须用当前 kernel 的 `sys.executable -m pip` 安装缺失依赖；网络只可能用于首次补齐依赖，不得把安装失败伪装成成功。依赖安装完成后，notebook 的论文内容、图片和实验应可离线运行。
- **依赖最小化。** 默认只用 `numpy`、`scipy`、`matplotlib`、`pandas`、`sympy`；深度学习论文需要时才用 `torch`。第一个代码单元格先声明 module 到 pip 包名的映射并自举安装，再导入全部依赖和打印版本。
- **在普通笔记本电脑 CPU 上运行完。** 整本 notebook 目标 5 分钟内，深度学习论文最多 10 分钟。可以自动检测 CUDA/MPS 加速，但结论不能依赖加速器。
- **可复现。** 固定所有随机种子（`numpy`、`random`、`torch`）。
- **图表文字用英文。** 各系统中文字体差异很大，matplotlib 渲染中文常出现方框乱码。图的标题、坐标轴、图例用英文（术语本来就保留英文），中文解读写在 markdown 里。

## 验证的层次

"写了代码"不等于"验证了论文"。按从低到高的层次组织验证，每一层都尽量覆盖：

1. **正确性检查**：`assert` 形状、不变量、边界情况（排序结果有序、概率和为 1、日志 term 单调不减）
2. **独立交叉验证**：数值梯度 vs 解析梯度、高效算法 vs 暴力 oracle、Monte Carlo vs 闭式解
   - **验证你的检查本身有效**：一个从不失败的测试毫无意义。故意破坏实现的关键部分（去掉论文强调的某条规则、改错一个符号），确认检查能报错。这种变异测试本身往往就是很好的教学实验，能说明"这条规则到底在保护什么"
3. **复现定性结论**：用 toy 实验复现论文的核心说法（"A 比 B 收敛快""复杂度是 O(n log n)""崩溃后仍能选出唯一 leader"），多个随机种子
4. **与论文数字对照**：列表对比论文报告值和本 notebook 结果，诚实解释差异（规模、数据、简化）

没能复现的结论要如实写出来，这对读者同样有价值。复现结果与论文偏差较大时，先找出是哪个建模假设导致的（论文往往没有交代全部实验细节），尝试合理的替代假设，把两种结果**都**展示出来并分析原因。这通常比只展示调得最像的结果更有启发。

## 参考文件索引

- `references/extraction.md` — 提取工具安装与配置（MinerU on CUDA / Apple Silicon）、疑难问题、手动修图流程
- `references/notebook_guide.md` — notebook 各节写法、示例、格式约定（**第 4 步前必读**）
- `references/paper_types/*.md` — 五类论文的实现与验证策略（第 3 步按类型读取）
- `assets/notebook_template.md` — notebook 源文件骨架
- `scripts/extract_paper.py` — 提取（子命令 `crop`、`render` 用于手动修图）
- `scripts/build_notebook.py` — 构建、隔离执行、校验（子命令 `check` 校验已有 ipynb）
