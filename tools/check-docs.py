"""Проверка тайминга сценариев: блоки обязательной части должны идти подряд
без разрывов и наложений и в сумме покрывать ровно 15:00 (900 секунд)."""
import re, pathlib

FILES = [
    '/home/user/scool_shedule2026/docs/scenario-grade2.md',
    '/home/user/scool_shedule2026/docs/scenario-grade4.md',
]

def rows(path):
    out = []
    for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        m = re.match(r'^(\d+):(\d\d)\s*[–—-]\s*(\d+):(\d\d)$', cells[0])
        if m:
            h1, m1, h2, m2 = map(int, m.groups())
            out.append((cells[0], cells[1] if len(cells) > 1 else '', h1 * 60 + m1, h2 * 60 + m2))
    return out

ok = True
for p in FILES:
    rs = rows(p)
    print(f'\n=== {pathlib.Path(p).name} ===')
    total, prev = 0, 0
    for label, name, s, e in rs:
        gap = 'OK' if s == prev else f'РАЗРЫВ/НАЛОЖЕНИЕ (пред. конец {prev // 60}:{prev % 60:02d})'
        print(f'  {label:<13} {e - s:>3} с  {name[:46]:<46} {gap}')
        total += e - s
        prev = e
    uniq = sorted(set((r[2], r[3]) for r in rs))
    cov = sum(e - s for s, e in uniq)
    last = uniq[-1][1]
    print(f'  блоков {len(rs)} (уникальных {len(uniq)}), сумма {total} с, покрытие 0:00–{last // 60}:{last % 60:02d} = {cov} с')
    if cov != 900 or last != 900:
        ok = False
        print('  -> ПРОБЛЕМА: покрытие не равно 15:00')

print('\nИТОГ:', 'основная часть обоих сценариев = 15:00' if ok else 'есть расхождения тайминга')
