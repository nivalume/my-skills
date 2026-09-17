# 真实 LLM 论文实验

适用于模型参与决策的论文实现，以及用户要求把现有 notebook 接入真实 LLM 的任务。实现内联在 notebook 中；依赖自举映射包含 `litellm` 和 `dotenv: python-dotenv`。使用 LiteLLM 调用 OpenAI-compatible Chat Completions，除非用户指定其他接口。

## 共享配置与凭据

先复用项目已有命名与配置位置。没有约定时使用下列共享模板，放在 notebook 集合目录（例如 `papers/.env.example`）；同目录的 notebook 共用一份 `.env`，不按论文名创建 `REACT_*` 等前缀。

```dotenv
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=your-model-name
LLM_CONTEXT_WINDOW=128000
LLM_MAX_OUTPUT_TOKENS=1024
LLM_CONTEXT_RESERVE=512
LLM_TEMPERATURE=0
LLM_REQUEST_TIMEOUT_S=60
LLM_MAX_STEPS=6
```

这些预算是示例，须按实际模型调整。`context_window` 是本地输入预算，并非服务端请求参数；为输出与安全余量预留空间，超限时明确裁剪策略。推理模型的输出预算可能包含 reasoning token，检查 `finish_reason`，避免把截断误诊为 parser 错误。

- 使用 `load_dotenv(path, override=False)`，已有进程环境变量优先。路径解析支持实际使用的启动位置（如仓库根目录与 `papers/`），明确选择共享配置位置，不盲目加载其他目录的 `.env`。notebook 没有可靠的 `__file__`。
- 提示用户从模板复制并填写 `.env`；保留已配置的文件，添加并验证精确 Git 忽略规则（如 `/papers/.env`）。已有跟踪文件不会因 `.gitignore` 自动移出版本管理，需单独报告。
- 只输出模型、非敏感预算和 `api_key_configured`；密钥不进入代码、模板、对象 repr、日志或保存的输出。凭据字段可用 `dataclasses.field(repr=False)`；不要打印整个配置/响应。清理交付 notebook 中的敏感输出。
- 将 `MODEL` 映射到 LiteLLM 的 `openai/<model>` 路由，显式传 `api_key` 与 `api_base=OPENAI_BASE_URL`。保留用户网关路径，不强制改成 `/v1`，也不拼接 `/chat/completions`。
- 缺少凭据时给出配置文件与变量名的可操作错误；真实运行单元格不静默跳过，也不回退到 mock。

## 正文、thinking 与动作

先检查实际 endpoint 返回的字段名、类型、是否非空和 `finish_reason`，再写适配器。不要只依据 API 调用成功便假定正文格式，更不要在尚未看到响应时断言“模型加了代码围栏”。

LiteLLM 响应中，`message.content` 可能只有 `Action:`，而可用的 thinking 在 `message.reasoning_content`。读取并分别传递正文与 reasoning；其他 provider 的 thinking 字段只按观察到的结构适配。服务端未返回 reasoning 时明确标记缺失，不编造、也不承诺所有模型都会暴露。若作为论文的 `Thought` 展示，说明这是服务端返回的 reasoning，不等同于原论文的显式 Thought prompting；已有正文 Thought 也应保留来源区分。

动作仍仅从约定的正文或结构化工具字段解析，不从 reasoning 中提取执行。对于 ReAct 文本接口：

- 容忍常见的代码围栏、空白、Markdown 标签及 action-only 响应；不要把完整响应锁死为“恰好两行”。
- 单步只执行一个明确动作，验证名称白名单和参数。出现多个候选动作或格式歧义时明确报错，或在有限次数内请求格式修正，不能随意挑第一个/最后一个动作。
- 错误区分空内容、输出截断、格式错误与服务端错误；诊断只包含必要的脱敏摘要，避免把凭据或完整敏感上下文保存进 traceback。
- 提示词描述工具的真实语义。例如精确标题匹配的 `search`、仅检索当前页的 `lookup`、候选标题如何使用及何时 `finish`。模型应依据 observation 决策，而非依赖写死的答案/动作序列。

## 验证与交付

先用少量自检覆盖真实观察到的变体：正文 Thought + Action、action-only + reasoning、无 reasoning、Markdown 包装、非法/多个动作和截断。固定字符串用于 parser 自检，不能充当模型实验的成功证据。

配置与模型调用分别验证：从约定工作目录检查 `.env` 加载及环境变量优先级；再用已有凭据、当前 kernel 环境进行有步数、超时和输出预算上限的真实运行。核对请求 → 响应字段 → parser → 工具 → observation → finish 整条链路；记录实际调用次数、停止原因与任务结果。无异常退出但耗尽 `max_steps`、未 finish 或 reward 未达标，仍是未完成的任务。模型正常返回失败结果时如实报告，不能改奖励标准或挑选成功运行掩盖失败。

隔离执行目录不会自动带上 `.env`。可先在验证进程内加载配置再由 kernel 继承环境变量，避免把密钥复制进临时源码。独立验证路径解析；隔离调用成功不代表用户启动目录下配置已验证。没有凭据或网络时继续完成结构检查与离线自检，清楚报告“真实 LLM 未验证”，不声称全文 Run All 成功。静态 `check` 的 `ok: true`、parser 自检通过、真实任务成功、论文基准复现是不同证据层次。

修改已有 notebook 后，保留用户其他单元格与内容，清除被修改代码的旧输出/执行状态。用户重复贴出旧错误时，对照 traceback 的函数体、当前磁盘代码和打开的文件路径：若 traceback 仍使用已删除的 `fullmatch`，优先排查编辑器缓冲区或旧 kernel 定义。先保护未保存编辑并比较文件，再指导从磁盘重载、Restart Kernel、Run All；重启 kernel 本身不会刷新旧编辑器内容。
