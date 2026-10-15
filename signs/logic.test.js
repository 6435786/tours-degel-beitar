// הרצה: node --test signs/logic.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const L = require('./logic.js');

test('מחיר לפי הדוגמאות במסמך', () => {
  assert.equal(L.price(1.5, 3).gross, 56.64);
  assert.equal(L.price(1, 3.7).gross, 69.86);
  assert.equal(L.price(2, 3).gross, 123.9);
  assert.equal(L.price(3, 5).net, 175);
  assert.equal(L.price(3, 5).gross, 206.5);
  assert.equal(L.price(5, 3).gross, 206.5, 'הסדר גובה/רוחב לא משנה');
});

test('גבולות מדרגה', () => {
  assert.equal(L.price(1.6, 2).perMeter, 16);
  assert.equal(L.price(1.61, 2).perMeter, 35);
  assert.equal(L.price(3.2, 4).perMeter, 35);
  assert.equal(L.price(5, 6).perMeter, 45);
  assert.equal(L.price(5.1, 6).special, true);
  assert.equal(L.price(0, 3), null);
  assert.equal(L.price('', ''), null);
});

test('מחירון מותאם', () => {
  const p = { vat: 0.17, tiers: [{ max: 2, price: 10 }, { max: 4, price: 20 }] };
  assert.equal(L.price(1.8, 3, p).perMeter, 10);
  assert.equal(L.price(1.8, 3, p).gross, 35.1);
  assert.equal(L.price(4.5, 5, p).special, true);
});

test('ייעוץ', () => {
  assert.match(L.advice(1.5, 3).text, /אין מה לייעל/);
  const a = L.advice(2, 3);
  assert.equal(a.options.length, 1);
  assert.equal(a.options[0].gross, 56.64);
  assert.equal(a.options[0].saving, 54);
  const b = L.advice(4, 5);
  assert.deepEqual(b.options.map(o => [o.toNarrow, o.saving]), [[3.2, 22], [1.6, 64]]);
  assert.equal(L.advice(6, 6).text, 'דרוש מחיר מיוחד');
});

test('מידות לביצוע', () => {
  assert.deepEqual(L.execDims({ height: 3, width: 5 }), { h: 3, w: 5, changed: false });
  assert.deepEqual(L.execDims({ height: 3, width: 5, yossiMode: 'change', execHeight: 1.6, execWidth: 5 }), { h: 1.6, w: 5, changed: true });
  assert.deepEqual(L.execDims({ height: 3, width: 5, yossiMode: 'approve', execHeight: 1.6, execWidth: 5 }), { h: 3, w: 5, changed: false });
});

test('שרשרת סטטוסים', () => {
  const m = { height: 3, width: 5, access: 'קלה' };
  assert.equal(L.status({}), 'await_hq');
  assert.equal(L.status({ hqRec: 'כ' }), 'await_admin');
  assert.equal(L.status({ ...m }), 'await_admin', 'נמדד בשטח לפני אישור');
  assert.equal(L.status({ approved1: true }), 'await_survey');
  assert.equal(L.status({ approved1: true, ...m }), 'await_yossi');
  assert.equal(L.status({ approved1: true, ...m, yossiDecision: 'rejected' }), 'yossi_no');
  assert.equal(L.status({ approved1: true, ...m, yossiDecision: 'approved' }), 'approved');
  assert.equal(L.status({ approved1: true, ...m, yossiDecision: 'approved', toExecute: true }), 'printing');
  assert.equal(L.status({ approved1: true, ...m, yossiDecision: 'approved', toExecute: true, printReturned: true }), 'ready');
  assert.equal(L.status({ ...m, access: 'מנוף', toExecute: true, printReturned: true }), 'await_crane');
  assert.equal(L.status({ ...m, access: 'מנוף', toExecute: true, printReturned: true, craneDate: '2026-10-20' }), 'ready');
  assert.equal(L.status({ ...m, done: true }), 'done');
  assert.equal(L.status({ ...m, done: true, finished: true }), 'finished');
  assert.equal(L.status({ rejected: true, approved1: true }), 'rejected');
});

test('פירוק כתובות מהקובץ הקיים', () => {
  const p = L.parseAddress;
  assert.deepEqual(p('אבוחצירה 32 קומה אחרונה'), { street: 'אבוחצירה', houseNo: '32', floor: 'אחרונה', note: '' });
  assert.deepEqual(p('גיבורי ישראל 24 קומה אחרונה פונה לכיון כביש גהה גבעת שמואל'),
    { street: 'גיבורי ישראל', houseNo: '24', floor: 'אחרונה', note: 'פונה לכיון כביש גהה גבעת שמואל' });
  assert.deepEqual(p('חזון איש 21 פינת האדמור מגור'), { street: 'חזון איש', houseNo: '21', floor: '', note: 'פינת האדמור מגור' });
  assert.deepEqual(p('אבחצירה פינת זבוטינסקי קומה 3'), { street: 'אבחצירה', houseNo: '', floor: '3', note: 'פינת זבוטינסקי' });
  assert.deepEqual(p('עזרא 2 פינת השומר 68'), { street: 'עזרא', houseNo: '2', floor: '', note: 'פינת השומר 68' });
  assert.deepEqual(p("רח' בירנבוים 34 פינת רב עמרם גאון 1"), { street: 'בירנבוים', houseNo: '34', floor: '', note: 'פינת רב עמרם גאון 1' });
  assert.deepEqual(p('נוף רמות 75 (אורך 5 מטר)'), { street: 'נוף רמות', houseNo: '75', floor: '', note: 'אורך 5 מטר' });
  assert.deepEqual(p('מרומי שדה 22/3 מול הפארק'), { street: 'מרומי שדה', houseNo: '22/3', floor: '', note: 'מול הפארק' });
  assert.deepEqual(p('הרצוג 37 קומת כניסה'), { street: 'הרצוג', houseNo: '37', floor: 'כניסה', note: '' });
  assert.deepEqual(p('אבן גבירול 2 קומה 5 דירה 24'), { street: 'אבן גבירול', houseNo: '2', floor: '5', note: 'דירה 24' });
  assert.equal(p('יותם המלך מול פארק יהושפט').houseNo, '');
  assert.deepEqual(p(''), { street: '', houseNo: '', floor: '', note: '' });
});

test('טלפונים', () => {
  assert.deepEqual(L.phones('0527108332 / 0583217545'), ['0527108332', '0583217545']);
  assert.deepEqual(L.phones('052-718-9382 / 050-413-6111'), ['0527189382', '0504136111']);
  assert.deepEqual(L.phones('03-5784601'), ['035784601']);
  assert.deepEqual(L.phones('548531772'), ['0548531772']);
  assert.equal(L.phoneLooksValid('050410322'), false);
  assert.equal(L.phoneLooksValid('0548540415'), true);
  assert.equal(L.phoneLooksValid('025001202'), true);
});
