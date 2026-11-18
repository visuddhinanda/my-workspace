#!/usr/bin/env python3
"""分层抽样：每个语料选 N 个连续 cs_para 区块，均匀分布在全书，合计根本文本约 TARGET 字符。

只考虑"有注释"的 cs_para（相关段落里有义注/复注），排除注释段落异常多的（如 vin1 cs1 外缘因缘）。
用法: python3 sample.py  → 打印并写入 samples.json
"""
import json, random
from extract import conn, CORPORA

TARGET = 65000      # ≈ 巴拉基咖篇根本 650,997 字符的 10%
BLOCKS = 10
MAX_COMM_PARAS = 60
EXCLUDE = {'vin1': set(range(3, 8))}   # 试点已做
SEED = 20261118


def main():
    db = conn(); cur = db.cursor()
    rnd = random.Random(SEED)
    out = {}
    for corpus, books in CORPORA.items():
        mula = [b for b, d in books.items() if d == 0][0]
        comm = [b for b, d in books.items() if d > 0]
        cur.execute("""
          with m as (select r.cs_para cs, sum(length(p.text)) mc from related_paragraphs r
                     join pali_texts p on p.book=r.book and p.paragraph=r.para
                     where r.book_name=%s and r.book=%s group by 1),
               c as (select cs_para cs, count(*) np from related_paragraphs
                     where book_name=%s and book = any(%s) group by 1)
          select m.cs, m.mc, c.np from m join c using(cs) order by m.cs""", (corpus, mula, corpus, comm))
        rows = [r for r in cur.fetchall() if r[2] <= MAX_COMM_PARAS and r[0] not in EXCLUDE.get(corpus, ())]
        seg = len(rows) // BLOCKS
        per = TARGET / BLOCKS
        blocks = []
        for i in range(BLOCKS):
            part = rows[i * seg:(i + 1) * seg]
            # 从段内随机起点开始累加，直到够 per 字符
            j = rnd.randrange(max(1, len(part) // 2))
            blk, acc = [], 0
            while j < len(part) and acc < per:
                blk.append(part[j][0]); acc += part[j][1]; j += 1
            blocks.append({'cs': blk, 'mula_chars': acc})
        out[corpus] = {'blocks': blocks, 'mula_chars': sum(b['mula_chars'] for b in blocks),
                       'eligible_cs': len(rows), 'eligible_chars': sum(r[1] for r in rows)}
        print(corpus, out[corpus]['mula_chars'], [f"{b['cs'][0]}-{b['cs'][-1]}" for b in blocks])
    json.dump(out, open('samples.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
