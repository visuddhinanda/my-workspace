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

判断以“判断要点”（这一片的目的、功能）为准。“典型句式”只是常见的表达方式，供参考：同一功能可以有完全不同的说法。比如转述异说，也可能写成“某长老这样说，某长老那样说”，并不一定出现 keci、vadanti。

| 代码 | 类 | 判断要点（目的、功能） | 典型句式（举例，不限于此） |
|---|---|---|---|
| **L 词义** | | | |
| L1 | 同义替换 | 用意义相同或相近的词替换被解释词，让读者懂这个词 | X ti Y（Y 为一两个词）；X ti Y, Z |
| L2 | 指称／范围限定 | 说明被解释词具体指哪个、哪些，或包括到哪里为止：代词所指、ādi 所含、“其余”是哪些、物件和处所的界限 | X ti khattiyādi…；ādi-saddena … saṅgaṇhāti；sesā nāma …；ettha / tena / so ti …；… tathārūpassa … adhivacanaṃ |
| L3 | 多义辨析 | 列出一个词的几种意义，并确定此处取哪一义 | X-saddo A-B-C-esu vattati … idha A-yaṃ；… ādīsu … attho |
| L4 | 实质定义 | 说明所指之法的本质、特相，或戒律术语的技术定义，而不只是换一个词 | atthato / lakkhaṇato / sabhāvato pana …；X nāma …；… cetanā veditabbā |
| **G 语法** | | | |
| G1 | 词源／构词（nirutti, vigraha） | 通过拆解词形、给出构词理由来解释词义 | …tīti X；…assāti X；…aṭṭhena X；X-ssa Y X-Y |
| G2 | 格位、性数、虚词作用 | 说明某个词的语法功能：格、性数、虚词或不变词的作用 | karaṇe sāmivacanaṃ；upayogatthe；api / ca / vā-saddena …；nipāto |
| G3 | 分词、复合词形、异读 | 说明词怎么切分、复合词怎么构成、连声怎么变，或文本有哪些异读 | padacchedo；majjhepadalopa；paranipāta；…tipi pāṭho；sandhivasena |
| **D 义理** | | | |
| D1 | 法义展开 | 超出词义，展开教义内容：支分、轻重、加行、哪一道断何烦恼、因缘关系等 | tassa pañca sambhārā；appasāvajjo … mahāsāvajjo；… maggena pahīyati |
| D2 | 譬喻 | 借喻体来说明所喻之法 | yathā hi … evaṃ …；seyyathāpi；X viya Y daṭṭhabbo；upamā |
| D3 | 判定／抉择（vinicchaya）【新增】 | 对具体情形作出判定：律是犯罪与否、犯何罪；论是某法是否属于某类、能否为某所缘 | sace … āpatti / anāpatti / dukkaṭaṃ；… vaṭṭati / na vaṭṭati；ayamettha vinicchayo |
| D4 | 分类摄属（saṅgaha）【新增】 | 把法按类归属、计数，说明某类包括几种、哪些 | kusalato cattāro, kiriyato …；… saṅgahitā；ettha katī … |
| **C 语境** | | | |
| C1 | 意图、动机 | 说明说话者、行事者心里想什么，为什么这样说、这样做 | adhippāyo；maññamāno；sampassamāno；sandhāya vadati |
| C2 | 叙事衔接 | 交代情节、场景、人物，或引出下文 | atha …；tiādimāha；evaṃ vutte … āha |
| C3 | 整句释意 | 把整句或整段的意思换个说法讲清楚 | evamattho daṭṭhabbo；kiṃ vuttaṃ hoti；…ti attho；idaṃ vuttaṃ hoti |
| **A 论辩** | | | |
| A1 | 设问解答 | 预先提出疑问或反驳，再给出回答 | kasmā / kiṃ pana …? … vuccate；nanu …；codanā-parihāra |
| A2 | 评破他说、转述异说 | 转述别人的不同理解（可以只是并列），或对它们加以评判、驳斥 | keci / eke vadanti；aparo nayo；某长老说…，某长老说…；X-aṭṭhakathāyaṃ vuttaṃ, taṃ na yuttaṃ |
| **M 元注释** | | | |
| M1 | 说明措辞的理由 | 解释上一层（被注文本）为什么这样措辞、为什么用这个词或说这句话 | …ti āha ‘X’ti；tena vuttaṃ ‘X’ti；sarūpato dassento āha；…bhāsitattā |
| M2 | 指出语句的作用 | 指出某句话在文中起什么作用：显示什么、排除什么、属于哪种问或答 | etena … dasseti / dassito；nivattanatthaṃ；… pucchā |
| M3 | 方法指引 | 不直接解释，而是让读者按前面或别处的方法类推、参照 | vuttanayeneva；eseva nayo；heṭṭhā vuttanayena；visuddhimagge vuttaṃ |
| **其他** | | | |
| R | 引证 | 主要功能是引用别处经文或出处作为依据；一般作副标签，整片几乎就是引文时才作主类 | ti vuttaṃ (ma. ni. …)；yathāha … |
| X | 切片残片 | 切分产生的碎片，本身没有独立的解释功能 | 只有段号的句子；孤立的引语尾巴 |

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
