# CLAUDE.md

本仓库是巴利语翻译项目的文档库，不是代码仓库。

- 工作通过 wikipali 插件（skills: `wikipali:research` / `wikipali:citation` / `wikipali:write`，以及可选的 `wikipali-workspace`）连接 WikiPali。
- `workspace/` 为主要工作目录；`workspace/glossary/` 存术语文档；`workspace/projects/<项目名>/` 存各翻译项目文档。
- 文档用中文 Markdown 写作；引用原文时注明 WikiPali 坐标（`book-paragraph`）。
- 写入 WikiPali 前需向用户确认目标 channel。不要读取或提交 `~/.wikipali/credentials.json`。
- 插件安装与升级步骤见 `README.md`。

## 项目铁律

- patimokkha 项目：**只有工作目录 channel `c75c0c2d-9603-4509-b8a5-473b36e0bcdb`（草稿）可写**；参考译文 channel、巴利原文、nissaya 只读，严禁修改。详见 `workspace/projects/patimokkha/README.md`。
- 所有后台任务（subagent / workflow）都使用与聊天相同的模型，不降级、不换模型。
- 写入 WikiPali 的签名（`wikipali ensure-model --name/--model`）必须与实际产出译文的模型一致；写入前核对，不一致就重新 ensure-model。

## 术语规则（新建、修改译文时）

- 注入：待译段落里出现的**戒律术语**（`workspace/glossary/vinaya-terms.md`）和**本项目已用过的术语**（`workspace/projects/<项目>/terms.md`）都要挑出来注入提示词。
- 写法：译文里凡是这些术语，一律写成术语标记 `[[巴利词]]`，不直接写中文。之前译文用过的术语，后面遇到也直接用标记。
- 新术语：觉得是术语但两张表都没有的，**先提示用户要不要添加**，不要自己决定。用户同意后补进对应的表。
