"""Проверка сценариев: 1) одинаковое число колонок в каждой Markdown-таблице;
2) объём речи ведущих в каждом блоке укладывается в бюджет блока (110 слов/мин)."""
import re, pathlib

FILES = [
    '/home/user/scool_shedule2026/docs/scenario-grade2.md',
    '/home/user/scool_shedule2026/docs/scenario-grade4.md',
]

def check_tables(path):
    print(f'\n=== таблицы: {pathlib.Path(path).name} ===')
    lines = pathlib.Path(path).read_text(encoding='utf-8').splitlines()
    i, problems, tables, in_code = 0, 0, 0, False
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            in_code = not in_code
        if not in_code and line.startswith('|'):
            start = i
            counts = []
            while i < len(lines) and lines[i].startswith('|'):
                counts.append((i + 1, lines[i].count('|')))
                i += 1
            tables += 1
            base = counts[0][1]
            bad = [(n, c) for n, c in counts if c != base]
            print(f'  таблица на строке {start + 1}: колонок {base - 1}, строк {len(counts)} -> '
                  + ('OK' if not bad else f'РАЗНОЕ ЧИСЛО КОЛОНОК: {bad}'))
            problems += 1 if bad else 0
        else:
            i += 1
    print(f'  всего таблиц: {tables}, проблем: {problems}')
    return problems

def check_speech(path):
    print(f'\n=== объём речи: {pathlib.Path(path).name} ===')
    text = pathlib.Path(path).read_text(encoding='utf-8')
    for b in text.split('\n### ')[1:]:
        head = b.splitlines()[0]
        m = re.search(r'(\d+):(\d\d)\s*[–—-]\s*(\d+):(\d\d)', head)
        if not m:
            continue
        h1, m1, h2, m2 = map(int, m.groups())
        budget = (h2 * 60 + m2) - (h1 * 60 + m1)
        words = 0
        for line in b.splitlines():
            if line.startswith('**[ВЗР]**') or line.startswith('**[ВИТЯ]**'):
                clean = re.sub(r'\*\*|\(.*?\)|⟦.*?', ' ', line)
                words += len(clean.split())
        est = round(words / 110 * 60)
        verdict = 'OK' if est <= budget else f'ПЕРЕБОР на {est - budget} с'
        print(f'  {head[:52]:<52} бюджет {budget:>3}с | слов {words:>3} | ~{est:>3}с -> {verdict}')

p = 0
for f in FILES:
    p += check_tables(f)
for f in FILES:
    check_speech(f)
print('\nИТОГ по таблицам:', 'без ошибок' if p == 0 else f'{p} проблем')
