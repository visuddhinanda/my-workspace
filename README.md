# my-workspace

我的 WikiPali 巴利语翻译项目文档库。日常工作通过 Claude Code + [wikipali-plugins](https://github.com/iapt-platform/wikipali-plugins) 连接 [WikiPali](https://www.wikipali.org) 网站完成（检索原文、翻译、审稿、写回句子与术语）。

## 目录结构

```
workspace/              主要工作目录
├── glossary/           术语相关文档（术语表、译名讨论、取舍记录）
└── projects/           各翻译项目的文档，一个项目一个子目录
    └── patimokkha/     波罗提木叉
```

各目录的约定见其下的 `README.md`。

## 工具：wikipali-plugins

- 上游仓库：<https://github.com/iapt-platform/wikipali-plugins>
- 两个插件：
  - `wikipali` —— 底层：检索、阅读、引用缩写解析、以 AI 模型身份写入句子/术语/批注
  - `wikipali-workspace` —— 应用层（可选）：translate / review / revise / harmonize / note / glossary / discuss / encyclopedia / commentary-align / paper / style

### 安装（新机器）

在 Claude Code 里执行：

```
/plugin marketplace add iapt-platform/wikipali-plugins
/plugin install wikipali@wikipali
/plugin install wikipali-workspace@wikipali   # 可选，应用层
```

装完**重启会话**，插件命令和 skill 才会加载。

登录（写入 WikiPali 时需要）由独立的 `wikipali-login` 完成，密码不经过 AI；凭据保存在 `~/.wikipali/credentials.json`（0600），**绝不要提交进 git**。

### 升级

第三方 marketplace 默认不自动更新，需手动两步，**顺序不能颠倒**：

```bash
claude plugin marketplace update wikipali              # 1. 先刷新 marketplace 目录
claude plugin update wikipali@wikipali                 # 2. 再升级插件
claude plugin update wikipali-workspace@wikipali       # 装了应用层的话也升
```

然后**重启会话**。不先刷新目录，`plugin update` 拿到的仍是旧版。

确认版本：

```bash
claude plugin details wikipali
ls ~/.claude/plugins/cache/wikipali/wikipali/
```

> SSH 远程工作时，插件装在远端主机的 `~/.claude`，升级命令也要在远端执行。

各版本更新内容见上游 [CHANGELOG.md](https://github.com/iapt-platform/wikipali-plugins/blob/main/CHANGELOG.md)。

## 翻译风格

`wikipali-workspace` 按以下顺序查找译文风格文件：

1. 项目：从当前目录往上找 `.wikipali/styles/translation.md`（可提交进本仓库，作为统一标准）
2. 个人：`~/.wikipali/styles/translation.md`
3. 插件默认

需要时用 `wikipali-style init` 在本仓库建立项目级风格文件。
