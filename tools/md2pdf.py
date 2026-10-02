"""Сборка PDF из Markdown-сценария урока.

A4 портрет; широкие таблицы (>=5 колонок) автоматически переносятся на альбомные
страницы вместе с открывающим заголовком раздела. Шрифты DejaVu (полная кириллица).

Использование:
    .venv-pdf/bin/python tools/md2pdf.py docs/scenario-grade2.md docs/scenario-grade2.pdf "Сценарий открытого урока · 2-й класс"
"""
import re, sys, pathlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

FD = '/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DJV', f'{FD}/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DJV-Bold', f'{FD}/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DJV-Mono', f'{FD}/DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('DJV-Mono-Bold', f'{FD}/DejaVuSansMono-Bold.ttf'))
pdfmetrics.registerFontFamily('DJV', normal='DJV', bold='DJV-Bold', italic='DJV', boldItalic='DJV-Bold')

INK = colors.HexColor('#14161a')
MUTED = colors.HexColor('#5b6472')
ACCENT = colors.HexColor('#1f4fd8')
LINE = colors.HexColor('#c8ced8')
HEADBG = colors.HexColor('#e7ecf5')
ZEBRA = colors.HexColor('#f5f7fb')
CODEBG = colors.HexColor('#f2f4f8')

src = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
doc_title = sys.argv[3] if len(sys.argv) > 3 else src.stem

M_PORTRAIT = 17 * mm
M_LAND = 14 * mm
PW, PH = A4
LW, LH = landscape(A4)
PORT_W = PW - 2 * M_PORTRAIT
LAND_W = LW - 2 * M_LAND

styles = {
    'Title': ParagraphStyle('Title', fontName='DJV-Bold', fontSize=19, leading=24,
                            textColor=INK, spaceAfter=6),
    'H2': ParagraphStyle('H2', fontName='DJV-Bold', fontSize=13.5, leading=17, textColor=ACCENT,
                         spaceBefore=14, spaceAfter=6, keepWithNext=1),
    'H3': ParagraphStyle('H3', fontName='DJV-Bold', fontSize=11, leading=14.5, textColor=INK,
                         spaceBefore=10, spaceAfter=4, keepWithNext=1),
    'Body': ParagraphStyle('Body', fontName='DJV', fontSize=10, leading=14.5, textColor=INK,
                           spaceAfter=5, alignment=TA_LEFT),
    'Bullet': ParagraphStyle('Bullet', fontName='DJV', fontSize=10, leading=14,
                             textColor=INK, leftIndent=15, bulletIndent=3, spaceAfter=3,
                             bulletFontName='DJV', bulletFontSize=9.5),
    'Quote': ParagraphStyle('Quote', fontName='DJV', fontSize=10, leading=14.5, textColor=MUTED,
                            leftIndent=12, rightIndent=6, spaceBefore=3, spaceAfter=6),
    'Cell': ParagraphStyle('Cell', fontName='DJV', fontSize=7.6, leading=10.2, textColor=INK),
    'CellHead': ParagraphStyle('CellHead', fontName='DJV-Bold', fontSize=7.8, leading=10.4,
                               textColor=INK),
    'Code': ParagraphStyle('Code', fontName='DJV-Mono', fontSize=8.4, leading=11.6, textColor=INK),
}


def inline(text):
    """Markdown-инлайн -> разметка reportlab."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'`([^`]+)`', r'<font face="DJV-Mono" size="8.6">\1</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    return text


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def is_sep(line):
    return bool(re.fullmatch(r'\|[\s:\-|]+\|', line.strip()))


def table_block(rows, wide):
    """rows: список списков строк (первая — заголовок)."""
    ncols = len(rows[0])
    avail = LAND_W if wide else PORT_W
    header = rows[0]
    # ширина колонки пропорциональна объёму текста, с ограничением минимума
    weights = []
    for i in range(ncols):
        longest = max(len(r[i]) if i < len(r) else 0 for r in rows)
        weights.append(max(8, min(longest, 46)))
    total = sum(weights)
    widths = [max(26, avail * w / total) for w in weights]
    # фиксированные минимумы для служебных колонок: время и номер кадра не должны рваться
    MINW = {'Время': 62, 'Кадр': 28}
    fixed = {}
    for i, h in enumerate(header):
        if h in MINW:
            fixed[i] = MINW[h]
    if fixed:
        fixed_sum = sum(fixed.values())
        others = [i for i in range(ncols) if i not in fixed]
        others_sum = sum(widths[i] for i in others) or 1
        for i in fixed:
            widths[i] = fixed[i]
        for i in others:
            widths[i] = max(24, widths[i] * (avail - fixed_sum) / others_sum)

    data = []
    for ri, row in enumerate(rows):
        style = styles['CellHead'] if ri == 0 else styles['Cell']
        data.append([Paragraph(inline(c) or '&nbsp;', style) for c in row])

    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADBG),
        ('GRID', (0, 0), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]
    for r in range(1, len(data)):
        if r % 2 == 0:
            cmds.append(('BACKGROUND', (0, r), (-1, r), ZEBRA))
    t.setStyle(TableStyle(cmds))
    return t


def code_block(lines):
    body = '<br/>'.join(l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') or '&nbsp;'
                        for l in lines)
    inner = Table([[Paragraph(body, styles['Code'])]], colWidths=[PORT_W - 12])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODEBG),
        ('BOX', (0, 0), (-1, -1), 0.4, LINE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return inner


def tokenize(md):
    blocks = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('```'):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith('```'):
                buf.append(lines[j])
                j += 1
            blocks.append(('code', buf))
            i = j + 1
            continue
        if s.startswith('|') and i + 1 < len(lines) and is_sep(lines[i + 1]):
            rows = [cells(s)]
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('|'):
                rows.append(cells(lines[j]))
                j += 1
            blocks.append(('table', rows, len(rows[0]) >= 5))
            i = j
            continue
        if s.startswith('# '):
            blocks.append(('h1', s[2:]))
        elif s.startswith('## '):
            blocks.append(('h2', s[3:]))
        elif s.startswith('### '):
            blocks.append(('h3', s[4:]))
        elif s.startswith('> '):
            blocks.append(('quote', s[2:]))
        elif re.fullmatch(r'-{3,}', s):
            blocks.append(('hr',))
        elif (m := re.match(r'^- \[[ x]\] (.*)$', s)):
            blocks.append(('check', m.group(1), '[x]' in s))
        elif s.startswith('- '):
            blocks.append(('bullet', s[2:]))
        elif (m := re.match(r'^(\d+)\. (.*)$', s)):
            blocks.append(('num', m.group(2)))
        elif s == '':
            pass
        else:
            blocks.append(('para', s))
        i += 1
    return blocks


def land_start_marks(blocks):
    """Индексы заголовков, после которых (через абзацы) идёт широкая таблица:
    такой заголовок переезжает на альбомную страницу вместе с таблицей."""
    marks = set()
    for i, b in enumerate(blocks):
        if b[0] == 'table' and b[2]:
            j = i - 1
            while j >= 0 and blocks[j][0] in ('para', 'quote'):
                j -= 1
            if j >= 0 and blocks[j][0] in ('h2', 'h3'):
                marks.add(j)
    return marks


def build_flow(md):
    flow = []
    blocks = tokenize(md)
    marks = land_start_marks(blocks)
    num_counter = 0
    first_h1 = True
    land_open = False
    for idx, b in enumerate(blocks):
        kind = b[0]

        if kind in ('h2', 'h3') and idx in marks:
            flow.append(NextPageTemplate('land'))
            flow.append(PageBreak())
            land_open = True

        if kind == 'code':
            flow.append(Spacer(1, 3))
            flow.append(code_block(b[1]))
            flow.append(Spacer(1, 6))
        elif kind == 'table':
            rows, wide = b[1], b[2]
            if wide:
                if not land_open:
                    flow.append(NextPageTemplate('land'))
                    flow.append(PageBreak())
                flow.append(table_block(rows, wide))
                flow.append(NextPageTemplate('port'))
                flow.append(PageBreak())
                land_open = False
            else:
                flow.append(table_block(rows, wide))
                flow.append(Spacer(1, 8))
        elif kind == 'h1':
            if first_h1:
                flow.append(Paragraph(inline(b[1]), styles['Title']))
                first_h1 = False
            else:
                flow.append(Paragraph(inline(b[1]), styles['H2']))
        elif kind == 'h2':
            flow.append(Paragraph(inline(b[1]), styles['H2']))
            num_counter = 0
        elif kind == 'h3':
            flow.append(Paragraph(inline(b[1]), styles['H3']))
            num_counter = 0
        elif kind == 'quote':
            flow.append(Paragraph(inline(b[1]), styles['Quote']))
        elif kind == 'hr':
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width='100%', thickness=0.5, color=LINE,
                                   spaceBefore=2, spaceAfter=6))
        elif kind == 'check':
            flow.append(Paragraph(inline(b[1]), styles['Bullet'], bulletText=('☑' if b[2] else '☐')))
        elif kind == 'bullet':
            flow.append(Paragraph(inline(b[1]), styles['Bullet'], bulletText='•'))
            num_counter = 0
        elif kind == 'num':
            num_counter += 1
            flow.append(Paragraph(inline(b[1]), styles['Bullet'], bulletText=f'{num_counter}.'))
        elif kind == 'para':
            flow.append(Paragraph(inline(b[1]), styles['Body']))
    return flow


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('DJV', 8)
    canvas.setFillColor(MUTED)
    w, h = (LW, LH) if canvas._pagesize == landscape(A4) else (PW, PH)
    m = M_LAND if canvas._pagesize == landscape(A4) else M_PORTRAIT
    canvas.drawCentredString(w / 2, 9 * mm, f'{doc_title}  ·  стр. {canvas.getPageNumber()}')
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(m, 12 * mm, w - m, 12 * mm)
    canvas.restoreState()


md = src.read_text(encoding='utf-8')
doc = BaseDocTemplate(str(out), pagesize=A4, title=doc_title,
                      leftMargin=M_PORTRAIT, rightMargin=M_PORTRAIT,
                      topMargin=M_PORTRAIT, bottomMargin=M_PORTRAIT,
                      author='scool_shedule2026')
port_frame = Frame(M_PORTRAIT, M_PORTRAIT, PORT_W, PH - 2 * M_PORTRAIT, id='port')
land_frame = Frame(M_LAND, M_LAND, LAND_W, LH - 2 * M_LAND, id='land')
doc.addPageTemplates([
    PageTemplate(id='port', frames=[port_frame], pagesize=A4, onPage=footer),
    PageTemplate(id='land', frames=[land_frame], pagesize=landscape(A4), onPage=footer),
])
doc.build(build_flow(md))
print('PDF:', out, out.stat().st_size, 'байт')
