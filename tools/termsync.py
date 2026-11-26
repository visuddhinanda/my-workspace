#!/usr/bin/env python3
"""本地术语文件（YAML 头部 + 正文）与 WikiPali 术语条目的同步，按 git 的逻辑走。

适用于任何项目里「一个 md 文件 = 一条 WikiPali 术语」的文档（百科词条等）。

三方：
- 快照（snapshot）：上次推送 / 拉取成功时服务器的记录，含乐观锁 etag —— 相当于 git 的上游
- 本地（local）  ：md 文件，YAML 头部放可改的字段，正文就是术语的 note —— 相当于工作区
- 远端（remote） ：服务器当前的记录

子命令：
  status   <md…>                    看本地、远端相对快照各自有没有改
  pull     <md…>                    拉远端，三方合并进 md；有冲突就留冲突标记并停下
  push     <md…> [-y]               以快照 etag 加锁推送（不加 -y 只预演）；成功后更新快照
  baseline <md> --guid <guid>       给已发布的术语建快照、补头部（不改正文）

快照位置：从 md 所在目录往上找最近的 `.snapshots/` 目录，所在目录即同步根；
快照在 `<根>/.snapshots/<channel 前 8 位>/<md 相对根的路径，.md 换成 .json>`。
第一次在某个项目里用 baseline 时，用 --root 指定同步根（缺省是 md 所在目录）。

依赖：wikipali 命令（插件提供的 term-get / term-edit --if-match --json），PyYAML，git（合并正文）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

# 头部里可改、会同步的字段（顺序即写出顺序）。word / tag 建立后不能改，只作标识。
# 头部里**没写的字段不纳入同步**（比较、合并、推送都跳过）；写了键而值为空 = 要清空这个字段。
SYNC_FIELDS = ('meaning', 'other_meaning', 'summary', 'quality', 'content_type', 'redirect')
HEAD_ORDER = ('word', 'tag') + SYNC_FIELDS + ('channels',)
# 服务端渲染 / 计算出来的字段，不进快照
DERIVED = ('body', 'summary_text', 'abilities')
CONFLICT_MARK = '<<<<<<< '
EXIT_CONFLICT = 3  # wikipali 插件约定：乐观锁冲突的退出码


class SyncError(Exception):
    pass


# ---------------------------------------------------------------------------
# wikipali 命令
# ---------------------------------------------------------------------------


def wikipali_bin():
    path = os.environ.get('WIKIPALI_BIN') or shutil.which('wikipali')
    if not path:
        raise SyncError('找不到 wikipali 命令：装好 wikipali 插件并重启会话，或用环境变量 WIKIPALI_BIN 指定。')
    return path


def term_get(guid):
    proc = subprocess.run([wikipali_bin(), 'term-get', guid, '--json'],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SyncError(f'读取术语 {guid} 失败：{proc.stderr.strip()}')
    return json.loads(proc.stdout)


def term_edit(guid, patch, if_match, yes):
    cmd = [wikipali_bin(), 'term-edit', guid, '--if-match', if_match, '--json']
    for field, value in patch.items():
        cmd += [f'--{field.replace("_", "-")}', '' if value is None else value]
    cmd.append('-y' if yes else '--dry-run')
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)  # 回显走 stderr，直接给用户看
    if proc.returncode == EXIT_CONFLICT:
        raise SyncError('远端在上次同步之后有更新（乐观锁冲突）。先 pull 合并，再 push。')
    if proc.returncode != 0:
        raise SyncError(f'term-edit 失败（退出码 {proc.returncode}），见上面的输出。')
    return json.loads(proc.stdout) if proc.stdout.strip() else None


# ---------------------------------------------------------------------------
# md 文件：YAML 头部 + 正文
# ---------------------------------------------------------------------------


def read_md(path):
    with open(path, encoding='utf-8') as f:
        return read_text_md(f.read(), path)


def git_show(path, rev):
    """取某个 git 版本里这个文件的内容。"""
    d, name = os.path.split(os.path.abspath(path))
    proc = subprocess.run(['git', 'show', f'{rev}:./{name}'], cwd=d, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SyncError(f'取不到 {rev} 版本的 {path}：{proc.stderr.strip()}')
    return proc.stdout


def read_text_md(text, path='(文本)'):
    if text.startswith('---\n'):
        end = text.find('\n---\n', 4)
        if end < 0:
            raise SyncError(f'{path}：头部以 --- 开始却没有结束的 ---。')
        head = yaml.safe_load(text[4:end + 1]) or {}
        body = text[end + 5:]
        return head, body
    return None, text


def write_md(path, head, body):
    # 头部里有的键都保留（值为空也留着：表示要清空）；tag 为空就不写
    ordered = {k: head[k] for k in HEAD_ORDER if k in head and not (k == 'tag' and is_empty(head[k]))}
    ordered.update({k: v for k, v in head.items() if k not in ordered and k not in HEAD_ORDER})
    text = '---\n' + yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False, width=10 ** 6) + '---\n'
    if not body.endswith('\n'):
        body += '\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text + body)


def is_empty(value):
    return value is None or value == '' or value == []


def same(a, b):
    return (a or '') == (b or '')


def same_body(a, b):
    # 服务端会去掉正文末尾的换行
    return (a or '').rstrip() == (b or '').rstrip()


def has_conflict(head, body):
    texts = [body] + [str(head.get(f) or '') for f in SYNC_FIELDS if f in head]
    return any(line.startswith(CONFLICT_MARK) for t in texts for line in t.splitlines())


# ---------------------------------------------------------------------------
# 快照
# ---------------------------------------------------------------------------


def find_root(md_path, explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    d = os.path.dirname(os.path.abspath(md_path))
    while True:
        if os.path.isdir(os.path.join(d, '.snapshots')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def snapshot_path(md_path, channel_id, root):
    rel = os.path.relpath(os.path.abspath(md_path), root)
    if rel.startswith('..'):
        raise SyncError(f'{md_path} 不在同步根 {root} 之下。')
    return os.path.join(root, '.snapshots', channel_id[:8], os.path.splitext(rel)[0] + '.json')


def load_snapshot(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_snapshot(path, record):
    record = {k: v for k, v in record.items() if k not in DERIVED}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write('\n')


def channels_of(md_path, head, only):
    channels = (head or {}).get('channels') or []
    if not channels:
        raise SyncError(f'{md_path}：头部没有 channels，先用 baseline 建立同步。')
    if only:
        picked = [c for c in channels if c.startswith(only)]
        if not picked:
            raise SyncError(f'{md_path}：头部的 channels 里没有 {only}。')
        return picked
    return channels


def contexts(md_path, only_channel):
    """逐个 channel 给出 (channel, 快照路径, 快照)。"""
    head, body = read_md(md_path)
    if head is None:
        raise SyncError(f'{md_path}：没有 YAML 头部，先用 baseline 建立同步。')
    root = find_root(md_path)
    if root is None:
        raise SyncError(f'{md_path}：往上找不到 .snapshots/ 目录，先用 baseline 建立同步。')
    for channel in channels_of(md_path, head, only_channel):
        spath = snapshot_path(md_path, channel, root)
        if not os.path.exists(spath):
            raise SyncError(f'{md_path}：channel {channel[:8]} 没有快照（{spath}），先用 baseline 建立同步。')
        yield head, body, channel, spath, load_snapshot(spath)


def local_changes(head, body, base):
    changed = [f for f in SYNC_FIELDS if f in head and not same(head[f], base.get(f))]
    if not same_body(body, base.get('note')):
        changed.append('note')
    return changed


# ---------------------------------------------------------------------------
# 三方合并
# ---------------------------------------------------------------------------


def merge_text(local, base, remote):
    """git merge-file：返回 (合并结果, 冲突块数)。"""
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, text in (('local', local), ('base', base), ('remote', remote)):
            p = os.path.join(tmp, name)
            with open(p, 'w', encoding='utf-8') as f:
                f.write((text or '').rstrip() + '\n')
            paths.append(p)
        proc = subprocess.run(['git', 'merge-file', '-p', '-L', 'local', '-L', 'base', '-L', 'remote', *paths],
                              capture_output=True, text=True)
        if proc.returncode < 0 or proc.returncode > 127:
            raise SyncError(f'git merge-file 失败：{proc.stderr.strip()}')
        return proc.stdout, proc.returncode


def merge_field(local, base, remote):
    """返回 (值, 是否冲突)。冲突时值写成带冲突标记的文本，push 会拒绝。"""
    if same(local, base):
        return remote, False
    if same(remote, base) or same(remote, local):
        return local, False
    return f'{CONFLICT_MARK}local\n{local or ""}\n=======\n{remote or ""}\n>>>>>>> remote', True


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------


def cmd_status(args):
    worst = 0
    for md in args.files:
        for head, body, channel, spath, base in contexts(md, args.channel):
            remote = term_get(base['id'])
            mine = local_changes(head, body, base)
            theirs = remote.get('etag') != base.get('etag')
            if has_conflict(head, body):
                state = '有未解决的冲突标记'
            elif mine and theirs:
                state = '两边都改了 → pull 合并'
            elif theirs:
                state = '线上改了 → pull'
            elif mine:
                state = f'本地改了（{", ".join(mine)}）→ push'
            else:
                state = '一致'
            worst = max(worst, 0 if state == '一致' else 1)
            print(f'{md}  [{channel[:8]}]  {state}')
    return worst


def cmd_pull(args):
    code = 0
    for md in args.files:
        for head, body, channel, spath, base in contexts(md, args.channel):
            remote = term_get(base['id'])
            if remote.get('etag') == base.get('etag'):
                print(f'{md}  [{channel[:8]}]  线上没有更新。')
                continue
            if has_conflict(head, body):
                raise SyncError(f'{md}：还有未解决的冲突标记，先处理完再 pull。')

            conflicts = []
            for field in (f for f in SYNC_FIELDS if f in head):
                value, clash = merge_field(head.get(field), base.get(field), remote.get(field))
                head[field] = value
                if clash:
                    conflicts.append(field)
            merged, hunks = merge_text(body, base.get('note'), remote.get('note'))
            if hunks:
                conflicts.append(f'note（{hunks} 处）')

            write_md(md, head, merged)
            save_snapshot(spath, remote)  # 快照前移到远端：之后 push 带的是新 etag
            if conflicts:
                code = 1
                print(f'{md}  [{channel[:8]}]  已合并，有冲突：{", ".join(conflicts)}。'
                      '冲突处留了 <<<<<<< local / ======= / >>>>>>> remote 标记，处理后再 push。')
            else:
                print(f'{md}  [{channel[:8]}]  已合并线上更新，无冲突。')
            if len(head.get('channels') or []) > 1:
                print('  注意：合并进来的修改，push 到其他 channel 时也会带过去。')
    return code


def cmd_push(args):
    for md in args.files:
        for head, body, channel, spath, base in contexts(md, args.channel):
            if has_conflict(head, body):
                raise SyncError(f'{md}：还有未解决的冲突标记，处理完再 push。')
            changed = local_changes(head, body, base)
            if not changed:
                print(f'{md}  [{channel[:8]}]  与快照一致，无需推送。')
                continue
            patch = {f: (body.rstrip() if f == 'note' else head.get(f)) for f in changed}
            print(f'{md}  [{channel[:8]}]  推送字段：{", ".join(changed)}', file=sys.stderr)
            saved = term_edit(base['id'], patch, base['etag'], args.yes)
            if saved is None:
                print(f'{md}  [{channel[:8]}]  预演完毕，未写入（确认后加 -y）。')
                continue
            if not same_body(saved.get('note'), body) and 'note' in changed:
                print('  ⚠ 服务端保存的正文与本地不完全相同（除末尾换行外），快照以服务端为准。')
            save_snapshot(spath, saved)
            print(f'{md}  [{channel[:8]}]  已推送，快照已更新（etag {saved.get("etag")}）。')
    return 0


def cmd_baseline(args):
    md = args.files[0]
    remote = term_get(args.guid)
    channel = remote.get('channel_id')
    if not channel:
        raise SyncError('这条术语不属于任何 channel，AI 无法写入，不能纳入同步。')
    root = find_root(md, args.root) or os.path.dirname(os.path.abspath(md))
    spath = snapshot_path(md, channel, root)
    if os.path.exists(spath) and not args.force:
        raise SyncError(f'快照已存在：{spath}。要重建加 --force（会以线上为新基准）。')

    head, body = read_md(md)
    if head is None:
        head = {'word': remote.get('word'), 'tag': remote.get('tag')}
        for field in SYNC_FIELDS:
            if not is_empty(remote.get(field)):
                head[field] = remote[field]
        head['channels'] = []
    elif head.get('word') != remote.get('word') or not same(head.get('tag'), remote.get('tag')):
        raise SyncError(f'头部是 {head.get("word")}@{head.get("tag")}，线上是 '
                        f'{remote.get("word")}@{remote.get("tag")}，guid 给错了？')
    if channel not in (head.get('channels') or []):
        head['channels'] = (head.get('channels') or []) + [channel]

    hunks = 0
    if args.merge_base:
        # 上传时的本地版本作基准，把上传后线上的修改三方合并进正文
        _, base_body = read_text_md(git_show(md, args.merge_base))
        body, hunks = merge_text(body, base_body, remote.get('note'))

    write_md(md, head, body)
    save_snapshot(spath, remote)
    print(f'{md}  [{channel[:8]}]  已建立同步：快照 {os.path.relpath(spath)}')
    if args.merge_base:
        print(f'  已以 {args.merge_base} 版本为基准合并线上修改'
              + (f'，正文有 {hunks} 处冲突，处理后再 push。' if hunks else '，无冲突。'))
        return 1 if hunks else 0
    diff = local_changes(head, body, remote)
    if diff:
        print(f'  ⚠ 本地与线上不一致：{", ".join(diff)}。现在以线上为基准，'
              '直接 push 会用本地覆盖线上；不想覆盖就先把本地改成线上的内容。')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('status', help='本地、远端相对快照各自有没有改（只读）')
    p.add_argument('files', nargs='+')
    p.add_argument('--channel', help='只看某个 channel（uid 或前缀）')
    p.set_defaults(func=cmd_status)

    p = sub.add_parser('pull', help='拉远端，三方合并进 md，快照前移到远端')
    p.add_argument('files', nargs='+')
    p.add_argument('--channel', help='只拉某个 channel（uid 或前缀）')
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser('push', help='以快照 etag 加锁推送；不加 -y 只预演')
    p.add_argument('files', nargs='+')
    p.add_argument('--channel', help='只推某个 channel（uid 或前缀）')
    p.add_argument('-y', '--yes', action='store_true', help='真的写入（用户已确认本次写入时才加）')
    p.set_defaults(func=cmd_push)

    p = sub.add_parser('baseline', help='给已发布的术语建快照、补头部（不改正文）')
    p.add_argument('files', nargs=1)
    p.add_argument('--guid', required=True, help='该 channel 里这条术语的 guid')
    p.add_argument('--merge-base', dest='merge_base', metavar='GIT_REV',
                   help='上传时本地文件所在的 git 版本（如 HEAD、某个 commit）：以它为基准，'
                        '把上传后线上的修改三方合并进正文')
    p.add_argument('--root', help='同步根（.snapshots/ 建在这里）；缺省往上找已有的，找不到用 md 所在目录')
    p.add_argument('--force', action='store_true', help='快照已存在时重建')
    p.set_defaults(func=cmd_baseline)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SyncError as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
