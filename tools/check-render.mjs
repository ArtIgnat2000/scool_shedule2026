// Настоящая проверка рабочего кода: запускаем index.html в DOM (jsdom) и отдаём
// реальный schedule.json через шим fetch. Исполняется сам shipped-код:
// loadSchedule -> fetch -> renderSchedule -> lessonRow -> DOM.
// Запуск: cd tools && npm i jsdom && node check-render.mjs
// Ожидаемо: 37 строк уроков; Ср урок 8 -> пустое название, picto 📘, 14:50–15:30;
// при SCHOOL_START_M = 0 все времена сдвигаются на 8:00, а карточка «8:30» остаётся.
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const baseHtml = readFileSync('/home/user/scool_shedule2026/index.html', 'utf8');
const scheduleText = readFileSync('/home/user/scool_shedule2026/schedule.json', 'utf8');

async function render(html, label) {
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    url: 'http://localhost:8080/',
    beforeParse(window) {
      window.fetch = async (url) => {
        if (String(url).includes('schedule.json')) {
          return { ok: true, status: 200, json: async () => JSON.parse(scheduleText) };
        }
        return { ok: false, status: 404, json: async () => ({}) };
      };
      window.matchMedia = window.matchMedia || (() => ({ matches: false, addEventListener() {} }));
    }
  });
  const { window } = dom;
  await new Promise((r) => setTimeout(r, 300));
  const doc = window.document;

  console.log(`\n=== ${label} ===`);
  console.log('Карточка начала уроков:', JSON.stringify(doc.querySelector('.start-card .sub')?.textContent));
  console.log('Карточка ошибки видима:', doc.getElementById('errorMsg')?.classList.contains('show'));
  console.log('Заголовок дня:', doc.getElementById('dayTitle')?.textContent,
    '| чип «Сегодня»:', doc.getElementById('todayChip')?.classList.contains('show'));

  for (const [key, name] of [['pn', 'Пн'], ['vt', 'Вт'], ['sr', 'Ср'], ['cht', 'Чт'], ['pt', 'Пт']]) {
    const rows = [...doc.querySelectorAll(`#${key} .lesson`)];
    const last = rows[rows.length - 1];
    console.log(`${name}: строк=${rows.length} | 1-й ${rows[0]?.querySelector('.time')?.textContent}` +
      ` | последний: №${last?.querySelector('.tile')?.textContent} "${last?.querySelector('.name')?.textContent}"` +
      ` (${last?.querySelector('.picto')?.textContent}) ${last?.querySelector('.time')?.textContent}`);
  }
  const sr8 = [...doc.querySelectorAll('#sr .lesson')][7];
  console.log('Ср 8-й: name длина', (sr8?.querySelector('.name')?.textContent ?? '').length,
    '| picto', sr8?.querySelector('.picto')?.textContent,
    '| время', sr8?.querySelector('.time')?.textContent);
  console.log('Всего строк на странице:', doc.querySelectorAll('.lesson').length);
  return doc;
}

await render(baseHtml, 'Рабочий сайт как есть');
const html800 = baseHtml.replace('const SCHOOL_START_M = 30;', 'const SCHOOL_START_M = 0;');
if (html800 === baseHtml) throw new Error('замена константы не сработала');
await render(html800, 'Та же страница при SCHOOL_START_M = 0 (8:00)');
