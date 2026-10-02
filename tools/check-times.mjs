// Проверка реального кода index.html без его переписывания:
// извлекаем исходный текст функций (от констант начала уроков до renderSchedule)
// и исполняем его в node.
// Ожидаемый результат: 0 расхождений вычисленного времени и schedule.json;
// среда, урок 8 -> name пустой, picto 📘, время 14:50–15:30;
// при SCHOOL_START_M = 0 вторник = 8:00–8:40 … 13:30–14:10.
import { readFileSync } from 'node:fs';

const html = readFileSync('/home/user/scool_shedule2026/index.html', 'utf8');
const lines = html.split('\n');
// не привязываемся к номерам строк: берём фрагмент от констант начала уроков до renderSchedule
const a = lines.findIndex(l => l.includes('const SCHOOL_START_H'));
const b = lines.findIndex(l => l.includes('function renderSchedule'));
if (a < 0 || b < 0 || b <= a) throw new Error('не найден фрагмент кода в index.html');
const src = lines.slice(a, b).join('\n');

function run(source) {
  return eval(source + '\n; ({ generateTimes, lessonRow, fmtTime, SCHOOL_START_H, SCHOOL_START_M, LESSON_DURATION, BREAKS });');
}

const api = run(src);
const schedule = JSON.parse(readFileSync('/home/user/scool_shedule2026/schedule.json', 'utf8'));
const dayNames = { pn: 'Понедельник', vt: 'Вторник', sr: 'Среда', cht: 'Четверг', pt: 'Пятница' };

console.log('Константы из index.html:', {
  SCHOOL_START_H: api.SCHOOL_START_H,
  SCHOOL_START_M: api.SCHOOL_START_M,
  LESSON_DURATION: api.LESSON_DURATION,
  BREAKS: api.BREAKS.join(',')
});

let mismatches = 0;
for (const [key, lessons] of Object.entries(schedule)) {
  const times = api.generateTimes(lessons.length);
  lessons.forEach((l, i) => {
    const ok = times[i] === l[1];
    if (!ok) mismatches++;
    console.log(`${dayNames[key]} урок ${l[0]}: вычислено ${times[i]} | в JSON ${l[1]} | ${ok ? 'OK' : 'НЕ СОВПАЛО'} | предмет="${l[2]}"`);
  });
}
console.log('\nРасхождений вычисленного времени и schedule.json:', mismatches);

const sr = schedule.sr;
const srTimes = api.generateTimes(sr.length);
sr.forEach((l, i) => {
  const htmlRow = api.lessonRow(l, i, srTimes[i]);
  const name = /<div class="name">([^<]*)<\/div>/.exec(htmlRow)[1];
  const time = /<div class="time">([^<]*)<\/div>/.exec(htmlRow)[1];
  const picto = /aria-hidden="true">([^<]*)<\/div>/.exec(htmlRow)[1];
  console.log(`Ср урок ${l[0]}: name="${name}" (длина ${name.length}), picto="${picto}", time="${time}"`);
});

const oldApi = run(src.replace('const SCHOOL_START_M = 30;', 'const SCHOOL_START_M = 0;'));
console.log('\nТот же код при SCHOOL_START_M = 0 (8:00), вторник:');
console.log(' было :', api.generateTimes(7).join('  '));
console.log(' стало:', oldApi.generateTimes(7).join('  '));
