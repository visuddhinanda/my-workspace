#!/usr/bin/env python3
"""注疏切片抽取：根本 → 义注 → 复注 (→ 随复注)。

用法:
  python3 extract.py 3 4 5 6 7                      # 兼容旧用法：vin1，输出 slices_cs3-7.json
  python3 extract.py --corpus mn1 --cs 10-14,80-85 --out slices_mn1.json

- 句子来自 sentences 表 (channel 巴利原文)
- 黑体(被解释词)来自 wbw_templates.style='bld'，wid 与句子 word_start/word_end 对齐
- 切片 = 含黑体词的句子 + 其后不含黑体词的句子，直到下一个含黑体词的句子
  · 只含小词(anu/api 等 <4 字母)黑体的句子不另起切片
  · 前一片以 "–" 结尾、本片只有一句短引语且后面还有切片 → 并回前一片（引语尾巴）
- 锚定 = 黑体词在下层文本中做去空格子串匹配；复注先找义注再找根本，随复注先找复注。
  对复注同时记录根本层候选 alt_mula（复注可能直接解释根本）。
"""
import argparse, json, re, sys, unicodedata
import psycopg2

ENV = '/home/deploy/workspace/mint/api-v13/.env'
CH = 'f4d07a00-8a5f-11ed-a044-a7a26c844686'

# depth: 0=mula 1=attha 2=tika 3=anutika
CORPORA = {
    'vin1': {213: 0, 138: 1, 204: 2, 209: 2, 210: 2},      # 205 数据疑似挂错，暂不收
    'mn1': {164: 0, 130: 1, 192: 2},
    'abhi1': {73: 0, 96: 1, 172: 2, 175: 3},
}
LAYER_NAME = {0: 'mula', 1: 'attha', 2: 'tika', 3: 'anutika'}
TITLE = {213: '(vn)pārājikapāḷi', 138: 'samantapāsādikā', 204: 'sāratthadīpanī-ṭīkā',
         209: 'vajirabuddhi-ṭīkā', 210: 'vimativinodanī-ṭīkā',
         164: 'majjhimanikāya(mūlapaṇṇāsa)', 130: 'papañcasūdanī', 192: 'līnatthappakāsanā',
         73: 'dhammasaṅgaṇīpāḷi', 96: 'dhammasaṅgaṇī-aṭṭhakathā', 172: 'dhammasaṅgaṇī-mūlaṭīkā',
         175: 'dhammasaṅgaṇī-anuṭīkā'}


def conn():
    env = dict(l.strip().split('=', 1) for l in open(ENV) if '=' in l and not l.startswith('#'))
    g = lambda k: env[k].strip('"')
    return psycopg2.connect(host=g('DB_HOST'), port=g('DB_PORT'), dbname=g('DB_DATABASE'),
                            user=g('DB_USERNAME'), password=g('DB_PASSWORD'))


def norm(s):
    s = unicodedata.normalize('NFC', s.lower())
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'[^a-zāīūṃṅñṭḍṇḷ]', '', s)


LOOSE = str.maketrans('āīūṃ', 'aium')


def loose(s):
    """匹配用：再去掉长短音、ṃ/m 之别"""
    return norm(s).translate(LOOSE)


def hkey(h):
    """黑体词匹配键：loose + 词尾 -n（vacanan·ti）还原为 -m"""
    return re.sub(r'n$', 'm', loose(h))


def clean_html(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+([,.;?!’])', r'\1', s)
    s = re.sub(r'([‘])\s+', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def load_para(cur, book, para):
    cur.execute("select word_start,word_end,content from sentences where channel_uid=%s and book_id=%s "
                "and paragraph=%s and deleted_at is null order by word_start", (CH, book, para))
    sents = cur.fetchall()
    cur.execute("select wid,word,style from wbw_templates where book=%s and paragraph=%s order by wid",
                (book, para))
    words = cur.fetchall()
    out = []
    for ws, we, content in sents:
        runs, cur_run = [], []
        for wid, w, st in words:
            if ws <= wid <= we and st == 'bld':
                m = re.match(r'^\{(.*)\}', w)
                cur_run.append(m.group(1) if m else w)
                if m:  # {X}ti 形式，自带结束
                    runs.append(cur_run); cur_run = []
            elif cur_run:
                runs.append(cur_run); cur_run = []
        if cur_run:
            runs.append(cur_run)
        heads = []
        for r in runs:
            t = ' '.join(x for x in r if norm(x))
            if norm(t):
                heads.append(t)
        out.append({'id': f'{book}-{para}-{ws}-{we}', 'book': book, 'para': para, 'ws': ws, 'we': we,
                    'text': clean_html(content or ''), 'heads': heads})
    return out


def slice_sents(sents):
    slices = []
    for s in sents:
        starts = any(len(norm(h)) >= 4 for h in s['heads'])
        if starts or not slices:
            slices.append({'sents': [s], 'heads': list(s['heads'])})
        else:
            slices[-1]['sents'].append(s)
            slices[-1]['heads'] += s['heads']
    # 引语尾巴并回前一片
    merged = []
    for i, sl in enumerate(slices):
        prev = merged[-1] if merged else None
        if prev and len(sl['sents']) == 1 and prev['sents'][-1]['text'].rstrip().endswith('–') \
                and len(sl['sents'][0]['text']) < 120 and i + 1 < len(slices):
            prev['sents'] += sl['sents']; prev['heads'] += sl['heads']; prev['merged_tail'] = True
        else:
            merged.append(sl)
    for sl in merged:
        f, l = sl['sents'][0], sl['sents'][-1]
        sl['id'] = f"{f['book']}-{f['para']}-{f['ws']}" + (f"~{l['para']}-{l['we']}" if l is not f else f"-{f['we']}")
        sl['text'] = ' '.join(s['text'] for s in sl['sents'])
        sl['book'] = f['book']
        sl['sent_ids'] = [s['id'] for s in sl['sents']]
        del sl['sents']
    return merged


def find_anchor(head, targets, start=0):
    """head 在 targets(句子列表) 里的位置。
    依次尝试：全词 → 截尾 1-4 字母（连声/词尾变化）→ 多词头的各词同句出现。
    比较时忽略长短音与 ṃ/m。优先目标句黑体含 head（黑体对黑体），再取离上一个锚点最近者。"""
    parts = [p for p in re.split(r'…pe…|\.\.\.|…|\bpe\b', head) if norm(p)]
    if not parts:
        return None
    key = hkey(parts[0])
    if len(key) < 4:
        return None  # anu / api 之类的小词：是讲解内部的子词，不做锚定
    T = [loose(t['text']) for t in targets]

    def pick(hits, method, k):
        bold = [i for i in hits if any(len(hkey(h)) >= 4 and (k in hkey(h) or hkey(h) in k)
                                       for h in targets[i]['heads'])]
        pool = bold or hits
        i = min(pool, key=lambda j: abs(j - start) + (0 if j >= start else 0.5))
        return {'sent': targets[i]['id'], 'idx': i, 'method': method}

    for cut in range(0, min(4, max(len(key) - 4, 0)) + 1):
        k = key[:len(key) - cut] if cut else key
        hits = [i for i, t in enumerate(T) if k in t]
        if hits:
            return pick(hits, 'exact' if not cut else f'trim{cut}', k)
    ws = [loose(w)[:-2] for w in parts[0].split() if len(loose(w)) >= 5]
    if len(ws) >= 2:
        hits = [i for i, t in enumerate(T) if all(w in t for w in ws)]
        if hits:
            return pick(hits, 'words', ws[0])
    return None


def head_role(head, text):
    """lemma=句首被解释词；quoted=句末引出（…āha ‘X’ti，复注常见）；inner=讲解内部提到的子词"""
    k, t = norm(head), norm(text)
    if t.startswith(k[:max(4, len(k) - 2)]) or t[:12].find(k[:6]) >= 0:
        return 'lemma'
    if re.search(r"(āha|vuttaṃ)\s*[‘“]", text):
        return 'quoted'
    return 'inner'


def make_units(cur, corpus, cs_list):
    """把共享注释段落的 cs_para 合并成一个单元（一段注释常对应多个 cs_para，避免重复切片）。"""
    books = CORPORA[corpus]
    cur.execute("select cs_para,book,para from related_paragraphs where book_name=%s and cs_para = any(%s)",
                (corpus, cs_list))
    m = {}
    for cs, b, p in cur.fetchall():
        if b in books:
            m.setdefault(cs, set()).add((b, p))
    units, owner = [], {}
    for cs in cs_list:
        keys = {k for k in m.get(cs, ()) if books[k[0]] > 0}
        hit = {owner[k] for k in keys if k in owner}
        if hit:
            u = min(hit)
            for o in sorted(hit - {u}, reverse=True):  # 合并多个已有单元
                units[u]['cs'] += units[o]['cs']; units[u]['paras'] |= units[o]['paras']
                for k in units[o]['paras']: owner[k] = u
                units[o] = None
        else:
            units.append({'cs': [], 'paras': set()}); u = len(units) - 1
        units[u]['cs'].append(cs); units[u]['paras'] |= m.get(cs, set())
        for k in m.get(cs, ()):
            if books[k[0]] > 0: owner[k] = u
    return [u for u in units if u]


def build_cs(cur, corpus, unit):
    books = CORPORA[corpus]
    cs = unit['cs'][0] if len(unit['cs']) == 1 else f"{min(unit['cs'])}~{max(unit['cs'])}"
    paras = {}
    for b, p in sorted(unit['paras']):
        paras.setdefault(b, []).append(p)
    layers = {}
    for b, ps in paras.items():
        sents = [s for p in ps for s in load_para(cur, b, p)]
        layers[b] = {'sents': sents, 'slices': slice_sents(sents) if books[b] > 0 else []}
    by_depth = {}
    for b, L in layers.items():
        by_depth.setdefault(books[b], []).extend(L['sents'])
    for b, L in layers.items():
        d = books[b]
        pos = {}
        for sl in L['slices']:
            sl['cs_para'] = cs
            sl['layer'] = LAYER_NAME[d]
            sl['anchors'] = []
            for h in sl['heads']:
                a = None; lvl = None
                for td in range(d - 1, -1, -1):
                    a = find_anchor(h, by_depth.get(td, []), pos.get(td, 0))
                    if a:
                        lvl = td; pos[td] = a['idx']; break
                rec = {'head': h, 'role': head_role(h, sl['text']),
                       'target_layer': LAYER_NAME[lvl] if a else None,
                       'target': a['sent'] if a else None, 'method': a['method'] if a else None}
                if a and lvl > 0 and d >= 2:  # 复注：根本层也有就记下
                    alt = find_anchor(h, by_depth.get(0, []), pos.get(0, 0))
                    if alt:
                        rec['alt_mula'] = alt['sent']
                sl['anchors'].append(rec)
    return {'cs_para': cs, 'cs_list': sorted(unit['cs']), 'paras': {str(k): v for k, v in paras.items()},
            'mula': by_depth.get(0, []),
            'commentary': {TITLE[b]: L['slices'] for b, L in sorted(layers.items(), key=lambda x: (books[x[0]], x[0]))
                           if L['slices']}}


def parse_cs(spec):
    out = []
    for part in spec.split(','):
        if '-' in part:
            a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        corpus, cs_list = 'vin1', [int(x) for x in sys.argv[1:]]
        out = f"slices_cs{cs_list[0]}-{cs_list[-1]}.json"
    else:
        ap = argparse.ArgumentParser()
        ap.add_argument('--corpus', required=True, choices=CORPORA)
        ap.add_argument('--cs', required=True, help='如 10-14,80-85')
        ap.add_argument('--out', required=True)
        a = ap.parse_args()
        corpus, cs_list, out = a.corpus, parse_cs(a.cs), a.out
    db = conn(); cur = db.cursor()
    data = [build_cs(cur, corpus, u) for u in make_units(cur, corpus, cs_list)]
    json.dump(data, open(out, 'w'), ensure_ascii=False, indent=1)
    sl = [s for d in data for v in d['commentary'].values() for s in v]
    an = [a for s in sl for a in s['anchors'] if len(norm(a['head'])) >= 4]
    print(f"{out}: cs={len(cs_list)} units={len(data)} mula_sents={sum(len(d['mula']) for d in data)} "
          f"slices={len(sl)} heads(>=4)={len(an)} anchored={sum(1 for a in an if a['target'])}")


if __name__ == '__main__':
    main()
