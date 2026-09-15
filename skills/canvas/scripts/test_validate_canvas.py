"""Run with python3 scripts/test_validate_canvas.py; no dependencies."""
from validate_canvas import TEMPLATE, validate
import re


def example(layout="docs", language="zh-CN"):
    chinese = language == "zh-CN"
    title = "Canvas HTML 标准" if chinese else "Canvas HTML standard"
    sections = ("生成流程", "输出参数") if chinese else ("Generation flow", "Output options")
    content = f'''<section id="flow" class="section">
      <h2>{sections[0]}</h2>
      <p>{"固定模板、填充内容、校验后交付。" if chinese else "Start from the template, fill content, validate, then deliver."}</p>
      <figure>
        <div class="chart-wrap" tabindex="0" role="region" aria-label="{sections[0]}"><svg class="chart" viewBox="0 0 600 100" role="img" aria-labelledby="flow-title">
          <title id="flow-title">{sections[0]}</title>
          <rect class="chart-node" x="10" y="10" width="160" height="60" rx="6"/>
          <path class="chart-axis" d="M170 40 H210 m-8 -5 8 5 -8 5" fill="none"/>
          <rect class="chart-node" x="210" y="10" width="160" height="60" rx="6"/>
          <path class="chart-axis" d="M370 40 H410 m-8 -5 8 5 -8 5" fill="none"/>
          <rect class="chart-node" x="410" y="10" width="180" height="60" rx="6"/>
          <text x="90" y="44" text-anchor="middle">{"模板" if chinese else "Template"}</text>
          <text x="290" y="44" text-anchor="middle">{"内容" if chinese else "Content"}</text>
          <text x="500" y="44" text-anchor="middle">{"校验与交付" if chinese else "Validate and deliver"}</text>
        </svg></div>
        <figcaption>{"来源：Canvas skill 工作流；静态流程，无时间范围。" if chinese else "Source: Canvas skill workflow; static process, no time range."}</figcaption>
      </figure>
      <details><summary>{"查看约束" if chinese else "View constraints"}</summary>
        <p>{"HTML 内嵌样式与数据，可离线打开。" if chinese else "HTML embeds styles and data and opens offline."}</p>
        <pre><code>&lt;script&gt; stays escaped &amp; readable</code></pre>
      </details>
    </section>
    <section id="options" class="section"><h2>{sections[1]}</h2>
      <div class="table-wrap" tabindex="0" role="region" aria-label="{sections[1]}"><table>
        <thead><tr><th scope="col">{"参数" if chinese else "Option"}</th><th scope="col">{"说明" if chinese else "Meaning"}</th></tr></thead>
        <tbody><tr><th scope="row"><code>output_path</code></th><td>{"输出文件或目录" if chinese else "Output file or directory"}</td></tr>
        <tr><th scope="row"><code>language</code></th><td>{"内容语言" if chinese else "Content language"}</td></tr></tbody>
      </table></div>
    </section>'''
    slots = {
        "LANG": language, "DIR": "ltr", "LAYOUT": layout, "TITLE": title,
        "SKIP_LABEL": "跳至正文" if chinese else "Skip to content",
        "OVERVIEW": '<p>' + ("面向生成可移植报告与文档的 agent；覆盖单文件 HTML 的生成与验收。" if chinese else "For agents creating portable reports and documentation; covers single-file HTML generation and review.") + '</p>',
        "TOC": f'<nav class="toc" aria-label="{"目录" if chinese else "Contents"}"><strong>{"目录" if chinese else "Contents"}</strong><ol><li><a href="#flow">{sections[0]}</a></li><li><a href="#options">{sections[1]}</a></li></ol></nav>' if layout == "docs" else "",
        "CONTENT": content,
        "REFERENCES": '<footer class="references"><h2>' + ("参考资料" if chinese else "References") + '</h2><ul><li><a href="https://github.com/cursor/plugins/tree/main/docs-canvas">Docs Canvas</a></li></ul></footer>',
        "SCRIPT": "",
    }
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: slots[match[1]], TEMPLATE.read_text(encoding="utf-8"))


def test_contract():
    good = example()
    assert not validate(good), validate(good)
    assert not validate(example("report", "en"))
    assert not validate(example(language="ar").replace('dir="ltr"', 'dir="rtl"'))
    for name, bad in {
        "changed tokens": good.replace("--bg: #ffffff", "--bg: #eeeeee", 1),
        "extra style": good.replace("</head>", "<style>h1 { font-size: 80px }</style></head>"),
        "inline style": good.replace('<h1>', '<h1 style="font-size:80px">'),
        "remote script": good.replace("</body>", '<script src="https://example.com/a.js"></script></body>'),
        "network call": good.replace("</body>", '<script>fetch("https://example.com")</script></body>'),
        "missing CSP": good.replace("default-src 'none'", "default-src *"),
        "bad link": good.replace('href="#flow"', 'href="javascript:alert(1)"'),
        "broken anchor": good.replace('href="#flow"', 'href="#missing"'),
        "unresolved slot": good.replace('<h1>', '<h1>{{TITLE}}'),
        "missing language": good.replace('lang="zh-CN"', ''),
        "duplicate IDs": good.replace('id="options"', 'id="flow"'),
        "missing shell": good.replace('class="layout"', ''),
        "missing TOC": good.replace('class="toc"', ''),
        "unlabelled SVG": good.replace('aria-labelledby="flow-title"', ''),
        "undefined token": good.replace('fill="none"', 'fill="var(--invented)"'),
    }.items():
        assert validate(bad), name
    print("PASS: docs/report/RTL contracts and 15 drift regressions")


if __name__ == "__main__":
    test_contract()
