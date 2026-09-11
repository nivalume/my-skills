# 论文提取参考

目录：
1. 引擎选择
2. MinerU 安装与配置
3. 手动修图流程
4. 公式核对
5. 疑难情况

---

## 1. 引擎选择

| 情况 | 推荐 |
|---|---|
| arXiv 论文 | `--engine auto`（先取 LaTeX 源码，再用 MinerU/PyMuPDF 补全） |
| 公式密集的 PDF（理论、金融、物理） | MinerU，公式输出 LaTeX |
| 扫描件（老论文） | MinerU（OCR）；没有 MinerU 时直接看 `pages/` 页面图 |
| 图多、公式少的系统/算法论文 | PyMuPDF 通常就够了，速度快 |
| 表格数值需要精确引用 | MinerU（表格输出 HTML，在 `figures.json` 的 `table_html` 字段） |

各工具简要对比（2026 年状态）：
- **MinerU**（OpenDataLab）：学术论文综合质量高，公式转 LaTeX、表格转 HTML，支持 OCR。3.1 起改为基于 Apache 2.0 的开源协议。支持 CUDA 和 Apple MPS 加速，也能纯 CPU 运行。
- **Docling**（IBM）：MIT 协议，CPU 友好，输出结构化文档对象。可作为 MinerU 的备选，本 skill 的脚本未内置，需要时手动运行后把结果整理为同样的目录结构。
- **Marker**（Datalab）：质量好、速度快，但代码 GPL-3.0、模型权重有商业使用限制。
- **PyMuPDF**：无模型、秒级完成，文字层完好的 PDF 上文本和图表裁剪都可靠，公式提取质量差。

## 2. MinerU 安装与配置

```bash
pip install -U "mineru[all]"        # 或 uv pip install -U "mineru[all]"
mineru --help                       # 确认安装与可用的 backend
```

首次运行会自动下载模型（几个 GB）。可以提前下载：`mineru-models-download`。

**模型源**：默认从 HuggingFace 下载。网络受限时：

```bash
export MINERU_MODEL_SOURCE=modelscope
```

**Backend 选择**（`extract_paper.py --mineru-backend ...` 传给 `mineru -b`）：

| backend | 说明 |
|---|---|
| 不指定（默认 `hybrid-auto-engine`） | 精度高；文字型 PDF 直接取文字层，幻觉少；自动选择本机推理引擎 |
| `vlm-auto-engine` | 纯 VLM；Apple Silicon 上可走 MLX |
| `pipeline` | 传统多模型流水线，最稳定、资源占用最低，可纯 CPU |

- **NVIDIA GPU**：默认即可，自动使用 CUDA。
- **Apple Silicon (M 系列)**：默认即可，自动尝试 MPS；如果 hybrid/vlm 后端报错或很慢，改用 `--mineru-backend pipeline`。
- MinerU 版本迭代很快，backend 名称和参数以本机 `mineru --help` 为准。

**输出结构**：MinerU 写入临时工作空间下的 `extract/_mineru/<文件名>/<backend目录>/`，关键文件是 `*_content_list.json`（按阅读顺序的内容块）、`*.md`、`images/`，以及用于排查问题的 `*_layout.pdf`（版面检测框可视化）。`extract_paper.py` 会自动整理到统一目录结构；这些文件不要写入用户当前工作目录。

**失败时**：脚本会记录警告并回退到 PyMuPDF，不会中断。查看 `extraction_report.json` 中的错误信息。

## 3. 手动修图流程

自动裁剪可能出现：裁掉一部分、混入正文、子图被拆开、漏掉没有标准图注的图。

1. 查看 `figures_overview.png` 找到问题图，记下页码。
2. 查看 `pages/page_NNN.png`，估计目标区域的像素坐标。
3. 换算为 PDF 坐标（原点左上角，单位 pt）：`pt = px × 72 / dpi`，`pages/` 默认 dpi 为 110。
4. 裁剪并查看结果，不对就调整坐标重试：

```bash
python scripts/extract_paper.py crop "$PAPER_DIR/extract/paper.pdf" --page 7 --bbox 325 78 540 225 -o "$PAPER_DIR/extract/figures/figure_7_fixed.png"
```

5. 在 notebook 源文件中引用修复后的文件名。

需要精细定位时，先用 `render --dpi 200` 生成高清页面，对应换算用 `pt = px × 72 / 200`。

## 4. 公式核对

文本提取出的公式常见错误：上下标错位、求和上下限丢失、`\top`/`'` 混淆、分式结构错乱、希腊字母识别错误、负号丢失。

核对方式：
1. 有 `latex/main_flat.tex` 时，搜索公式的 `\label` 或周围文字定位原始 LaTeX，直接使用。
2. 否则打开公式所在页的页面图（必要时 `render --dpi 200`），逐个符号对照写出 LaTeX。
3. 对要实现的公式，核对完成后再写代码。有疑问的地方（例如页面图也看不清），在笔记中标注。

## 5. 疑难情况

- **补充材料 / 附录单独成文件**：分别提取，输出到临时工作空间下的 `extract_supp/`。
- **图注不以 "Figure N:" 开头**（例如 "Fig. 3." 已支持；"图 3" 或无编号不支持）：自动裁剪会漏掉，走手动修图流程。
- **一个图注对应跨页的图**：分别裁剪各页部分，在 notebook 中依次展示。
- **arXiv 源码里图片是 EPS**：本机有 Ghostscript（`gs`）时自动转换，否则回退到 PDF 裁剪。
- **arXiv 只提供 PDF**（作者未上传源码）：report 中会有警告，自动走 MinerU/PyMuPDF。
- **加密或受保护的 PDF**：PyMuPDF 通常仍可读取；无法读取时请用户提供其他版本。
- **引用原图**：notebook 用于个人学习时嵌入原图没有问题；如果用户打算公开发布 notebook，提醒注明出处，并注意论文的版权许可。
