# Anki 输出约定

固定 note type：`KaTeX and Markdown Basic (Color)`。
用户原始模板完整存于 [card-template.md](card-template.md)。编写含公式、代码或图片的卡片时读它；
它是渲染参考，不是待安装的脚本。未提供 `_style.css` / `_user_style.css` 内容，不能假设具体字体、配色或宽度。

## 内容适配

- 正面只包含自足的问题与必要情境；背面模板已重复正面，因此 `back` 不再抄问题。
- 背面首句是可评分答案，随后按需给简短解释、关键条件或反例。来源由导出脚本加在最后。
- 使用普通 Markdown 段落、列表、带语言的 fenced code，以及 `$...$` / `$$...$$` 公式。
  不使用 Cloze 语法、Obsidian 链接或依赖插件的 Mermaid 块。
- **公式先于 Markdown 渲染。** 模板先去掉 `<pre>` 再调用 KaTeX，Markdown 代码围栏此时还没有保护作用。
  所有字面美元符号（包括代码、shell、价格和 URL 中的）写成 `\$`；真正公式的定界符保留 `$`。
  JSON 中需要写 `\\$` 来表达这一个反斜杠。导出器不会猜哪些 `$` 是公式。
- 模板会暂存 `\:`，再还原为 `:`。公式间距用 `\,` 或 `\;`，不要依赖 `\:` 的间距含义。
  数学比较符优先 `\lt` / `\gt`，KaTeX 使用模板指定的旧版本，复杂宏需要先验证。
- `<`、`>`、`&` 按原始文本写入 JSON，导出器仅在 HTML 边界转义一次，不预先写 HTML 实体。
  源代码中的 HTML 放在 fenced code 中；保持内容为 Markdown，不能从材料复制可执行标签。
- 模板以 ⛳、🉐、➿、➰ 作为内部占位符；正文改用这些符号的文字名称，避免被模板替换。
- 必要图片采用 `![说明](qataker-source-figure-01.png)`，文件平铺放到交付的 `media/` 中；
  文件名不含空格且在整个卡组内唯一。不能把绝对路径或远程图像作为唯一学习依据。
  媒体另行复制到 Anki 的 `collection.media`，CSV 不内嵌二进制。非必要图片省略。
  Markdown 图片由模板动态生成，Anki 的媒体引用检查可能不识别；交付带图卡时单独验证显示与同步，
  不根据「未使用文件」检查结果删除这类图片。

## JSON → CSV

`cards.json` 是非空数组，每项必需 `front`、`back`、`source` 三个非空字符串，`tags` 可省略或为字符串数组。
`source` 是可读的定位信息，允许安全的 Markdown 来源链接；多个来源在同一字符串逐行列明。
每张卡至少有一处能支撑答案的定位：视频时间段、PDF 页/图/节、网页章节，或代码文件与行范围。
来源不是把标题机械附在后面：实际证据需要先在内容审核中验证。

```json
[
  {
    "front": "采用 cache-aside，写请求只更新数据库且旧缓存仍有效。下一次读取为什么可能得到旧值？",
    "back": "读取命中旧缓存，绕过了已更新的数据库。\n\nTTL 限制旧值可能存活的时间，但不保证写后立即一致。",
    "source": "缓存讲义，第 3 页，读取与写入流程（示例定位，实际使用时替换为已核实来源）",
    "tags": ["缓存::一致性", "能力::机制"]
  }
]
```

示例用于说明格式，不能原样作为真实来源导出。`tags` 采用无空白的标签，可用 `::` 表示层级。
按任务选择少量主题与能力标签，不把整句答案放进标签。

```bash
python scripts/export_anki.py /task/cards.json /task/cards.csv
python scripts/test_export_anki.py
```

导出器使用标准库 `csv`，将所有字段加引号，保留真实换行、中文、逗号和引号。
输出 UTF-8，无普通表头行，文件前置指令为：

```text
#separator:Comma
#html:true
#notetype:KaTeX and Markdown Basic (Color)
#columns:Front,Back,Tags
#tags column:3
```

三列映射为 Front、Back、Anki Tags，来源在 Back 末尾。自动指令要求 Anki 2.1.54+；
旧版本需要在导入界面手工选择同样的分隔符、HTML、note type 和字段映射。
导出器拒绝空字段、重复正面（忽略首尾和连续空白）及非法标签，并拒绝覆盖已有文件。
需要修订时输出新文件名；语义近似题仍需 agent 在导出前去重。

## 导入与交付核对

导入前确保 Anki 已有指定 note type，含 Front/Back 字段，以及其依赖的 `collection.media` 资源。
CSV 中的 `#notetype` 只选择既有类型，不会创建它。模板从本地资源加载失败时会尝试 CDN；
离线可用性取决于本地资源是否齐全，CSV 不能解决资源缺失。

给用户的导入说明包含：选择目标牌组；确认 note type 和三列映射；启用 HTML；如有媒体则先复制；
检查预览中的公式、代码、换行和来源链接。Anki 通常以同 note type 的第一字段判重，
导入前核对更新/忽略/新增选项，避免意外更新已有笔记。

至少检查一张普通卡和每一种实际使用的特殊内容卡。CSV 回读只能证明格式，
模板 DOM 渲染只能证明该模板与样例兼容，只有实际 Anki 导入后才能声称导入成功。

规范来源：[Anki 文本导入](https://docs.ankiweb.net/importing/text-files.html)。
