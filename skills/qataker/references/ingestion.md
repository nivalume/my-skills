# 解析与安装

## 运行环境

本 skill 随 my-skills 插件安装，依赖相邻 `../notetaker/scripts/extract_pdf.py` 和
`../notetaker/scripts/extract_transcript.py`；单独复制 qataker 文件夹不能获得这两个入口。
复用脚本的提取能力，不触发 notetaker 的笔记合成或自演进流程。

下列命令从 qataker 文件夹执行。将工作产物放在用户任务目录，不写入 skill 本身。
先检查已有环境，缺什么装什么；用户已经授权准备依赖时直接执行，不重复确认。

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
python scripts/check_environment.py
```

已有 `.venv` 时跳过创建。没有 uv 时可用 `python3.12 -m venv .venv` 和激活环境后的
`python -m pip install -r requirements.txt`。在插件目录不可写的安装环境，把 venv 建到用户指定的可写工作目录，
使用它的解释器运行本 skill 的绝对路径脚本即可。所有解析脚本使用同一个已检查的解释器和 PATH。

FFmpeg/ffprobe 是系统依赖：macOS 用 `brew install ffmpeg`，Debian/Ubuntu 用
`sudo apt-get install ffmpeg`，Windows 用 `winget install Gyan.FFmpeg`，安装后重新检查 PATH。
代码的 Python AST 解析只用标准库；其他基础 Python 依赖列在 `requirements.txt`。

检查入口只验证导入、二进制与相邻脚本，不下载模型或语法库。
包可导入不等于权重已缓存，更不等于提取成功。按下列对应分支准备资源，再开始材料处理。

## 视频 / 音频

```bash
python ../notetaker/scripts/extract_transcript.py check
python ../notetaker/scripts/extract_transcript.py url "VIDEO_URL" --lang "zh.*,en.*" --out /task/source-01
# 本地视频或音频：
python ../notetaker/scripts/extract_transcript.py media /task/lecture.mp4 --model small --language zh --out /task/source-01
```

为每份来源使用新的输出目录，避免旧字幕被误选。在线路径优先字幕，失败会自动下载音频并转录；
如果当前任务不允许音频下载，先单独用 `yt-dlp --skip-download --write-subs --write-auto-subs`
取得字幕，不运行这个带自动回退的 `url` 入口。核对实际字幕语言，不根据文件名推断人工/自动字幕来源。

需要 Whisper 时，提前准备选定模型，例如激活环境后执行
`python -c 'import whisper; whisper.load_model("small", device="cpu")'`。
正常采用 `small`，CPU 较慢时按任务精度选 `base`；只有实测可用的 CUDA 才自动使用 GPU。
Apple Silicon 默认 CPU。模型下载失败时保留错误并说明缺口，不能把未转录的视频视为已读。

读取 `transcript.txt` 和 `transcript.srt`；Whisper 路径另有 `segments.json`。
从真实时间戳定位来源，校对重复字幕、说话者切换、否定词、公式读音和数字。
讲解依赖屏幕时查看相关画面，按需要取帧，例如：

```bash
ffmpeg -n -ss 00:02:15 -i /task/lecture.mp4 -frames:v 1 /task/frame-135.png
```

在线字幕路径不包含画面；需要画面时取得可访问的视频或用户提供的讲义后再核实。
只读过字幕就把覆盖范围表述为「字幕」，不声称检查了画面。

## PDF

```bash
python ../notetaker/scripts/extract_pdf.py check
python ../notetaker/scripts/extract_pdf.py inspect /task/source.pdf
python ../notetaker/scripts/extract_pdf.py extract /task/source.pdf --tool pymupdf4llm --out /task/pdf-01
```

`inspect` 只抽样页面；同时查看与问答相关的原页。简单文本适合 PyMuPDF4LLM，需页级文本和坐标时用
`--tool pymupdf`（输出带页码的 `content.txt` 和 `blocks.json`）。双栏、公式和复杂表格按实际质量选择
MinerU，扫描件、结构化报告可用 Docling。检查器的推荐是线索，不是已验证的提取质量。

重型引擎仅在选用时提前安装：

```bash
uv pip install --python .venv/bin/python 'mineru[core]'
# 或：
uv pip install --python .venv/bin/python docling
```

在处理用户材料前，先用小型非敏感样例预热所选引擎、下载所需模型并验证输出。
MinerU 的 `--backend pipeline` 可用于 CPU；按实际安装版本确认后端支持。
模型准备会占用额外磁盘和网络，未获该项安装授权时先说明实际所需资源；已有授权则继续执行。
缺引擎不能默默降级为没有 OCR 的空文本解析。

提取后抽查公式符号、上下标、表格行列和阅读顺序。来源使用 PDF 页序（从 1 开始）；
若引用印刷页码同时明确标注。Markdown 提取结果未保留页码时回到 PDF 定位，不从输出行数猜页数。
图表题必须看过图表，不能只依据邻近正文生成图中数值。

## 网页

激活基础环境后使用 Trafilatura CLI：

```bash
trafilatura -u "PAGE_URL" --markdown --links --with-metadata --no-comments
# 保存的 HTML 可用标准输入：
trafilatura --markdown --links --with-metadata --no-comments < /task/page.html
```

将提取结果保存到任务目录；保留原始 URL、标题、章节及访问日期。
对照可见页面核对代码块、公式、图片说明和折叠内容；正文提取可能遗漏它们。
动态页面或正文为空时用当前环境可用的浏览器读取实际加载内容。
登录墙、权限错误和加载失败要报告；搜索摘要不是正文，也不绕过访问限制。

工具参数参考：[Trafilatura CLI](https://trafilatura.readthedocs.io/en/latest/usage-cli.html)。

## 代码

先检查是否有可用且已初始化的 CodeGraph：结构问题用 context/explore/callers，字面文本用源码读取。
没有索引时遵循项目自身初始化约定；若不能初始化，继续用以下只读路径处理用户提供的文件。

- Python：用 `ast.parse(source)` 获取定义、参数、分支和调用的语法位置，用 `lineno`/`end_lineno` 回看源码。
- 其他支持的语言：用 `tree_sitter_language_pack.get_parser(language)` 的 `parse(source_bytes)` 获取语法树。
  在处理该语言文件前先用一个短片段确认 parser 可用；部分版本首次加载会下载语法资源。
  安装了包但语法资源不可用时报告实际错误，不视为解析成功。
- 未支持的语言：逐段读取源码，明确没有结构索引；不伪造 AST 或跨文件调用关系。

Python 的最小静态检查（只解析，不执行）：

```python
import ast
from pathlib import Path
source = Path('/task/example.py').read_text(encoding='utf-8')
tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        print(node.name, node.lineno, node.end_lineno)
```

结合源码和必要调用者追踪输入 → 状态变化 → 输出/错误，确认关键不变量和边界。
只看到调用表达式不等于确定了运行时目标；缺依赖文件时缩小问题范围或报告缺口。
将注释当作解释线索，和实现冲突时说明冲突。保存文件相对路径、符号、行范围，仓库可用时再附 commit。
不要为了出题执行、导入用户源码或安装该项目的依赖；预测结果明确标注静态推演。
