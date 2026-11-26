# tools

## termsync.py：本地术语文件与 WikiPali 同步

适用于任何项目里「一个 md 文件 = 一条 WikiPali 术语」的文档（百科词条等）。按 git 的逻辑走：

| 三方 | 是什么 | 相当于 git 的 |
|---|---|---|
| 快照 | 上次推送 / 拉取成功时服务器的记录，含乐观锁 etag | 上游分支 |
| 本地 | md 文件：YAML 头部（可改的字段）+ 正文（术语的 note） | 工作区 |
| 远端 | 服务器当前的记录 | 远端最新提交 |

```bash
python3 tools/termsync.py status   <md…>                 # 只读：一致 / 本地改了 / 线上改了 / 两边都改了
python3 tools/termsync.py pull     <md…>                 # 拉远端三方合并进 md，快照前移到远端
python3 tools/termsync.py push     <md…>                 # 预演
python3 tools/termsync.py push     <md…> -y              # 以快照 etag 加锁推送，成功后更新快照
python3 tools/termsync.py baseline <md> --guid <guid> [--root <同步根>]   # 已发布的术语纳入同步
```

### 文件格式

```markdown
---
word: sukkavissaṭṭhisikkhāpada
meaning: 故意出精学处
summary: …
quality: standard
channels:
- 311a835d-723e-44ec-957a-2d1127695d95
---
{{ai}}
正文……
```

- 可同步的字段：meaning、other_meaning、summary、quality、content_type、redirect。
  **头部里没写的字段不纳入同步**；写了键而值为空 = 要清空。word / tag 建立后不能改，只作标识。
- channels：发布到哪些 channel，每个 channel 各有一份快照、各自加锁。
- 快照在同步根下：`.snapshots/<channel 前 8 位>/<md 相对同步根的路径>.json`。同步根是从 md 往上
  最近的含 `.snapshots/` 的目录；某个项目第一次用 baseline 时用 `--root` 指定（缺省 md 所在目录）。
  快照要提交进 git。

### 流程

1. 改 md → `push`（先预演，用户确认后 `-y`）。
2. push 报「远端有更新」→ `pull`：
   - 字段：只有一边改了就取那边，两边改得不一样算冲突；
   - 正文：`git merge-file` 三方合并；
   - 冲突处留 `<<<<<<< local / ======= / >>>>>>> remote` 标记（字段的冲突也写在头部里），
     由 LLM / 人解决，**给用户看过后**再 push。有冲突标记时 push 会拒绝。
3. 合并进来的修改，push 到其他 channel 时也会带过去。

### 规矩

- 带头部的文件**不要再用** `wikipali term-edit --note "$(cat 文件)"`：会把头部传进正文，也绕过了乐观锁。
- 写入前确认目标 channel、核对签名（`wikipali ensure-model`）与实际产出的模型一致，见 CLAUDE.md。
- `baseline` 报「本地与线上不一致」时，以线上为基准，直接 push 会覆盖线上——先决定以哪边为准。
  上传后线上被改过、本地也可能改过时，加 `--merge-base <上传时的 git 版本>`：以那个版本为基准，
  把线上的修改三方合并进正文（如 `--merge-base HEAD`）。
- 新建术语（term-add）暂不经本工具：建好后用 `baseline` 纳入同步。

依赖：wikipali 插件（`term-get`、`term-edit --if-match --json`，冲突退出码 3）、PyYAML、git。
退出码：0 正常，1 有待处理（status 有改动、pull 有冲突），2 出错。
