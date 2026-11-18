#!/usr/bin/env python3
"""合并分批标注 → labels_<corpus>.tsv，并做校验与统计。

用法: python3 merge_labels.py <批次输出目录>
校验：每个切片恰好一行、主类在代码表内。统计：按语料×层级的主类分布、副标签、N: 新类。
"""
import collections, glob, json, os, sys

CODES = ['L1', 'L2', 'L3', 'L4', 'G1', 'G2', 'G3', 'D1', 'D2', 'D3', 'D4',
         'C1', 'C2', 'C3', 'A1', 'A2', 'M1', 'M2', 'M3', 'R', 'X']
HEADER = '# slice_id\t主类\t副标签\t备注\n'


def load_slices(path):
    out = {}
    for u in json.load(open(path)):
        for v in u['commentary'].values():
            for s in v:
                out[s['id']] = s
    return out


def main(outdir):
    stats = {}
    for corpus in ['vin1', 'mn1', 'abhi1']:
        sl = load_slices(f'slices_{corpus}.json')
        rows = {}
        for f in sorted(glob.glob(os.path.join(outdir, f'{corpus}_*.tsv'))):
            for line in open(f):
                if not line.strip() or line.startswith('#'):
                    continue
                r = line.rstrip('\n').split('\t') + ['', '', '']
                rows[r[0]] = r[:4]
        missing = [i for i in sl if i not in rows]
        extra = [i for i in rows if i not in sl]
        bad = [r for r in rows.values() if r[1] not in CODES]
        print(f'{corpus}: slices={len(sl)} labeled={len(rows)} missing={len(missing)} extra={len(extra)} badcode={len(bad)}')
        if missing or extra or bad:
            print('  missing', missing[:5], 'extra', extra[:5], 'bad', bad[:3])
        with open(f'labels_{corpus}.tsv', 'w') as w:
            w.write(HEADER)
            for i in sl:  # 按切片顺序
                if i in rows:
                    w.write('\t'.join(rows[i]) + '\n')
        by = collections.defaultdict(collections.Counter)
        tags = collections.defaultdict(collections.Counter)
        new = collections.Counter()
        for i, r in rows.items():
            if i not in sl:
                continue
            layer = sl[i]['layer']
            by[layer][r[1]] += 1
            for t in filter(None, (x.strip() for x in r[2].split(','))):
                (new if t.startswith('N:') else tags[layer])[t] += 1
        stats[corpus] = {'main': {k: dict(v) for k, v in by.items()},
                         'tags': {k: dict(v) for k, v in tags.items()}, 'new': dict(new)}
    json.dump(stats, open('label_stats.json', 'w'), ensure_ascii=False, indent=1)
    # 打印主类分布表（各层占比 %）
    for corpus, st in stats.items():
        print(f'\n## {corpus}')
        layers = list(st['main'])
        print('code\t' + '\t'.join(f'{l}(n={sum(st["main"][l].values())})' for l in layers))
        for c in CODES:
            vals = [st['main'][l].get(c, 0) for l in layers]
            if any(vals):
                print(c + '\t' + '\t'.join(f'{v} ({100 * v / max(1, sum(st["main"][l].values())):.0f}%)'
                                           for v, l in zip(vals, layers)))
        if st['new']:
            print('N:', sorted(st['new'].items(), key=lambda x: -x[1])[:15])


if __name__ == '__main__':
    main(sys.argv[1])
