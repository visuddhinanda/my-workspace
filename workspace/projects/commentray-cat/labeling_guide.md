# 注疏切片分类标注指南

你在给巴利注疏（义注 aṭṭhakathā / 复注 ṭīkā / 随复注 anuṭīkā）的切片做功能分类。
切片已由程序切好：一片 = 一个黑体被解释词开头的一句或几句。你只负责判断**这一片在做什么**。

## 输入格式（批次文件）

```
========== cs_para 18 ==========          ← 一组相互注释的段落（根本 + 其各层注释）
[138-650-2-30] attha · samantapāsādikā    ← 切片 id、层级、书名
  黑体: X[lemma→mula]; Y[quoted→attha]    ← 黑体词[角色→锚定到的下层]；"-" 表示未锚定
  根本原句: …                              ← 若锚到根本，给出根本原句
  切片正文…
```
黑体词角色：lemma=句首被解释词（X ti …）；quoted=句末被引出（…āha ‘X’ti，多为元注释）；inner=讲解中途出现的黑体。

## 分类代码（主类只能取一个；副标签可多个，逗号分隔）

| 代码 | 类 | 典型句式 / 判断要点 |
|---|---|---|
| L1 | 同义替换 | X ti Y，Y 为一两个词的同义词 |
| L2 | 指称／范围限定 | X 具体指什么（代词所指、ādi 所含、"其余"是哪些）；khattiyādi… |
| L3 | 多义辨析 | X-saddo A-B-C-esu vattati … idha A；列举词义并定此处义 |
| L4 | 实质定义 | atthato／lakkhaṇato／sabhāvato pana …；说明法的本质（如 = cetanā） |
| G1 | 词源／构词（nirutti, vigraha） | …tīti X；…assāti X；X 的拆解与命名理由 |
| G2 | 格位、性数、虚词作用 | karaṇe sāmivacanaṃ；upayogatthe；api/ca/vā-saddena；nipāta |
| G3 | 分词、复合词形、异读 | padacchedo；majjhepadalopa；paranipāta；…tipi pāṭho；sandhi |
| D1 | 法义展开 | 支分、轻重、加行、哪一道断何烦恼、缘起关系等教义阐述 |
| D2 | 譬喻 | yathā hi … evaṃ …；upamā |
| D3 | 判定／抉择（vinicchaya）【新增】 | 律：sace…āpatti/anāpatti/dukkaṭa…；何种情形如何判；论：何者是/不是某法的判定 |
| D4 | 分类摄属（saṅgaha）【新增】 | 把法按类计数、归属：kusalato cattāro, kiriyato…；"此中几种是…" |
| C1 | 意图、动机 | adhippāyo；maññamāno；sampassamāno；为何说（就说话者而言） |
| C2 | 叙事衔接 | 交代情节、谁对谁说、引出下文：tiādimāha；atha… |
| C3 | 整句释意 | evamattho daṭṭhabbo；kiṃ vuttaṃ hoti；…ti attho（对整句/整段意译） |
| A1 | 设问解答 | kasmā／kiṃ pana …? … vuccate／na；codanā-parihāra |
| A2 | 评破他说、转述异说 | keci／vadanti／aparo nayo；"X 中说…，那不对"；引某师、某注之说 |
| M1 | 说明上一层注释措辞的理由 | …ti āha ‘X’ti；tena vuttaṃ ‘X’ti；sarūpato dassento āha |
| M2 | 指出语句的作用 | etena … dassito／dasseti／nivattetī（此语用来显示/排除什么） |
| M3 | 方法指引 | vuttanayeneva；eseva nayo；heṭṭhā vuttanayena；imināva nayena |
| R | 引证 | 主要功能是引别处经文/出处（ti vuttaṃ (ma.ni.…)）；一般作副标签，只有整片几乎就是引文时才作主类 |
| X | 切片残片 | 切分碎片，本身无独立解释功能 |

判断原则：
- 主类按**这片主要在干什么**（篇幅最大或最核心的功能），其余功能放副标签。
- 被解释词是书名、地名、论师名、章节名（如 bhaddālisutte、Khandhake、mahāsumatthero、Andhakaṭṭhakathāyaṃ、Sanidassanattike）时，它不是"被解释词"，要按整片实际功能分类（引某师说 → A2，引经 → R，章节导入 → C2 或 M3），备注写"黑体为出处/章节"。
- 复注、随复注中"…ti āha ‘X’ti"（先讲后引）几乎都是 M1；"etena…dasseti" 是 M2。
- 如果你认为现有代码都不贴切，主类先选最接近的，副标签写 `N:简短名`（如 `N:读诵指示`），备注里说明。不要随意造新码；只有在多处都需要时才提。

## 示例

先读 `labels_cs3-7.tsv`（115 条试点标注，作为口径），
对应切片原文在同目录 `slices_cs3-7.json`。对齐它的口径。

## 输出

写一个 TSV 文件（UTF-8，Tab 分隔，无表头，每个切片 id 恰好一行，顺序同输入）：

```
slice_id<TAB>主类<TAB>副标签<TAB>备注
```
- 副标签可空；多个用英文逗号分隔。
- 备注用简短中文（≤40 字），写出判断依据或要点，例如"pariyāya 三义并引经，定此处=因"。
- 写完用下面命令自检：输出 id 数必须与输入相同、无重复、主类都在代码表内。

```
python3 -c "
import re,sys
b,o=sys.argv[1],sys.argv[2]
ids=re.findall(r'^\[([^\]]+)\]',open(b).read(),re.M)
rows=[l.rstrip('\n').split('\t') for l in open(o) if l.strip()]
ok={'L1','L2','L3','L4','G1','G2','G3','D1','D2','D3','D4','C1','C2','C3','A1','A2','M1','M2','M3','R','X'}
got=[r[0] for r in rows]
print('in',len(ids),'out',len(got),'missing',len(set(ids)-set(got)),'extra',len(set(got)-set(ids)),'dup',len(got)-len(set(got)),'badcode',[r for r in rows if len(r)<2 or r[1] not in ok][:5])
" <批次文件> <输出文件>
```
