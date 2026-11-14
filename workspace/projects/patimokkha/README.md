# patimokkha — 波罗提木叉翻译

目的：翻译。

## 底本范围

| 书 | WikiPali 起始坐标 | 范围 |
|---|---|---|
| Bhikkhupātimokkhapāḷi | 207:3 | **全译**（主） |
| Bhikkhunīpātimokkhapāḷi | 207:524 | **全译**（主） |
| Kaṅkhāvitaraṇī-aṭṭhakathā | 207:1215 | **全译**（主） |
| Kaṅkhāvitaraṇīpurāṇa-ṭīkā | 212:2 | 局部翻译 |
| Kaṅkhāvitaraṇī-abhinavaṭīkā | 212:671 | 局部翻译 |

（坐标为 `wikipali books` 给出的书首段落，全书标题用 `wikipali toc 207` / `wikipali toc 212` 查看。）

## Channel

| 用途 | channel | 名称 | 权限 |
|---|---|---|---|
| 主要参考译文 | `73c03e1a-f333-11f0-808a-438f0af4b9e9` | Claude | **只读** |
| 备用参考译文 | `877ae5ee-4a92-11f0-808a-6b8433850072` | deepseek | **只读** |
| 工作目录（草稿存储） | `c75c0c2d-9603-4509-b8a5-473b36e0bcdb` | 草稿 | **唯一可写** |

## 铁律

1. **只有工作目录 channel（草稿 `c75c0c2d-9603-4509-b8a5-473b36e0bcdb`）可以写入。**
2. 「修改译文」= 把译文写入工作目录 channel。
3. 参考译文（主、备用）、巴利原文、nissaya 等一切参考资料**只能读取，严禁修改**。
   - 例外：**百科词条**以术语条目（term-add，带 tag 与 note）写入 Claude channel `73c03e1a…`，不违反本条。本地副本存 `encyclopedia/`。
   - 百科体例：按 wikipali-workspace 的 encyclopedia skill；「相关条目」一律用术语标记 `[[巴利词]]`，隔离术语带 `@十七要素分析`。
4. 所有后台任务都使用与聊天相同的模型。
5. 写入签名必须与实际使用的模型相同。

## 进度

- 《疑惑度脱》（Kaṅkhāvitaraṇī-aṭṭhakathā）：草稿已译 207:1216–1434（序论 → 僧始终品），2026-11-14 统计。

待办事项见 [`TODO.md`](TODO.md)。

## 工作流程

1. 读巴利原文，并参考主要参考译文、备用参考译文、nissaya 等资料。
2. 挑出段落中的术语注入提示词：戒律术语查 [`../../glossary/vinaya-terms.md`](../../glossary/vinaya-terms.md)，其他已用术语查 [`terms.md`](terms.md)。
3. 拟定 / 修改译文，术语一律写成 `[[巴利词]]` 标记；表里没有、但像术语的词，先问用户要不要添加。
4. 写入工作目录 channel（草稿）。
