// לוגיקה טהורה של מערכת השלטים — תמחור, ייעוץ, סטטוס, פירוק כתובות.
// נטען בדפדפן (window.SignsLogic) ובבדיקות node (module.exports).
(function (root) {
  'use strict';

  const DEFAULT_PRICING = {
    vat: 0.18,
    tiers: [
      { max: 1.6, price: 16, desc: "שמשונית + תפירה טבעות עד רוחב 1.6 מ'" },
      { max: 3.2, price: 35, desc: "שמשונית + תפירה טבעות + הלחמה עד רוחב 3.2 מ'" },
      { max: 5, price: 45, desc: "שמשונית + תפירה טבעות + הלחמה עד רוחב 5 מ'" }
    ]
  };

  const round2 = x => Math.round((x + Number.EPSILON) * 100) / 100;
  const num = v => {
    if (v === null || v === undefined || v === '') return 0;
    const n = parseFloat(String(v).replace(',', '.'));
    return isFinite(n) ? n : 0;
  };
  const sortedTiers = p => [...((p && p.tiers) || DEFAULT_PRICING.tiers)]
    .filter(t => num(t.max) > 0)
    .sort((a, b) => num(a.max) - num(b.max));
  const vatOf = p => (p && p.vat !== undefined && p.vat !== '') ? num(p.vat) : DEFAULT_PRICING.vat;

  // מחיר לשלט: המדרגה לפי הצד הצר, המחיר למטר אורך (הצד הארוך)
  function price(h, w, pricing) {
    h = num(h); w = num(w);
    if (!(h > 0 && w > 0)) return null;
    const narrow = Math.min(h, w), length = Math.max(h, w);
    const tiers = sortedTiers(pricing);
    const idx = tiers.findIndex(t => narrow <= num(t.max) + 1e-9);
    const vat = vatOf(pricing);
    if (idx === -1) return { narrow, length, special: true, tierIndex: -1, perMeter: 0, net: 0, gross: 0, desc: 'דרוש מחיר מיוחד' };
    const t = tiers[idx];
    const net = round2(num(t.price) * length);
    return { narrow, length, special: false, tierIndex: idx, perMeter: num(t.price), net, gross: round2(net * (1 + vat)), desc: t.desc || '' };
  }

  // ייעוץ לחיסכון: הקטנת הצד הצר לגבול של כל מדרגה נמוכה יותר
  function advice(h, w, pricing) {
    const cur = price(h, w, pricing);
    if (!cur) return { text: '', options: [] };
    if (cur.special) return { text: 'דרוש מחיר מיוחד', options: [] };
    if (cur.tierIndex === 0) return { text: 'במדרגה הנמוכה – אין מה לייעל', options: [] };
    const tiers = sortedTiers(pricing), vat = vatOf(pricing);
    const options = [];
    for (let i = cur.tierIndex - 1; i >= 0; i--) {
      const to = num(tiers[i].max);
      const gross = round2(num(tiers[i].price) * cur.length * (1 + vat));
      const saving = cur.gross > 0 ? Math.round((1 - gross / cur.gross) * 100) : 0;
      options.push({ toNarrow: to, gross, saving });
    }
    const ils = x => '₪' + Math.round(x).toLocaleString('he-IL');
    const text = options.map(o => `הקטנת הצד הצר ל-${o.toNarrow} מ': ${ils(o.gross)} במקום ${ils(cur.gross)} (חיסכון ${o.saving}%)`).join(' | ');
    return { text, options };
  }

  const isMeasured = s => num(s.height) > 0 && num(s.width) > 0 && !!s.access;

  // מידות לביצוע: מה שיוסי הזין אם בחר "שנה", אחרת המדידה
  function execDims(s) {
    if (s.yossiMode === 'change' && num(s.execHeight) > 0 && num(s.execWidth) > 0)
      return { h: num(s.execHeight), w: num(s.execWidth), changed: true };
    return { h: num(s.height), w: num(s.width), changed: false };
  }

  const STATUSES = [
    { key: 'await_hq', label: 'ממתין להמלצת מטה', color: '#94a3b8' },
    { key: 'await_admin', label: 'ממתין לאישור שלמה', color: '#f59e0b' },
    { key: 'await_survey', label: 'ממתין למדידה', color: '#3b82f6' },
    { key: 'await_yossi', label: 'ממתין ליוסי', color: '#8b5cf6' },
    { key: 'approved', label: 'אושר – ממתין לביצוע', color: '#0ea5e9' },
    { key: 'printing', label: 'בדפוס', color: '#6366f1' },
    { key: 'await_crane', label: 'ממתין לתיאום מנוף', color: '#ea580c' },
    { key: 'ready', label: 'מוכן לתלייה', color: '#14b8a6' },
    { key: 'done', label: 'בוצע – ממתין לסיום', color: '#22c55e' },
    { key: 'finished', label: 'הסתיים', color: '#15803d' },
    { key: 'yossi_no', label: 'יוסי לא אישר', color: '#dc2626' },
    { key: 'rejected', label: 'נדחה', color: '#7f1d1d' }
  ];
  const STATUS_MAP = Object.fromEntries(STATUSES.map(s => [s.key, s]));

  function status(s) {
    if (s.finished) return 'finished';
    if (s.rejected) return 'rejected';
    if (s.done) return 'done';
    if (s.printReturned) return (s.access === 'מנוף' && !s.craneDate) ? 'await_crane' : 'ready';
    if (s.toExecute) return 'printing';
    if (s.yossiDecision === 'approved') return 'approved';
    if (s.yossiDecision === 'rejected') return 'yossi_no';
    const measured = isMeasured(s);
    if (!s.approved1) return (s.hqRec || measured) ? 'await_admin' : 'await_hq';
    if (!measured) return 'await_survey';
    return 'await_yossi';
  }

  // פירוק כתובת חופשית לרחוב / מספר / קומה / הערה
  function parseAddress(text) {
    let t = String(text || '').replace(/\s+/g, ' ').trim();
    const out = { street: '', houseNo: '', floor: '', note: '' };
    if (!t) return out;
    const notes = [];
    // הערות בסוגריים
    t = t.replace(/\(([^)]*)\)/g, (_, inner) => { if (inner.trim()) notes.push(inner.trim()); return ' '; });
    // קומה
    let m = t.match(/(?:^|\s)(קומת\s+כניסה|קומה\s+[^\s,]+)/);
    if (m) {
      out.floor = m[1].startsWith('קומת') ? 'כניסה' : m[1].replace(/^קומה\s+/, '');
      t = (t.slice(0, m.index) + ' ' + t.slice(m.index + m[0].length));
    }
    t = t.replace(/^רח(?:וב|')\s+/, '').replace(/\s+/g, ' ').trim();
    m = t.match(/^(.+?)\s+(\d+(?:\/\d+)?[א-ת]?)(?=\s|,|$)(.*)$/);
    if (m && !/(?:^|\s)(פינת|מול|ע"י|ליד)$/.test(m[1].trim())) {
      out.street = m[1].trim();
      out.houseNo = m[2];
      if (m[3].trim()) notes.unshift(m[3].trim());
    } else {
      out.street = t;
    }
    // "פינת ..." בשם הרחוב עובר להערה
    const p = out.street.match(/^(.+?)\s+(פינת\s.+)$/);
    if (p) { out.street = p[1].trim(); notes.unshift(p[2].trim()); }
    out.note = notes.join(' ').replace(/^[\s,.\-–]+/, '').replace(/\s+/g, ' ').trim();
    return out;
  }

  function formatAddress(s) {
    let a = [s.street, s.houseNo].filter(Boolean).join(' ');
    if (s.floor) a += (a ? ', ' : '') + 'קומה ' + s.floor;
    return a;
  }

  // מספרי טלפון מתוך טקסט חופשי (לחיוג)
  function phones(text) {
    const res = [];
    String(text || '').replace(/0?\d[\d\-.]{6,12}\d/g, m => {
      let d = m.replace(/\D/g, '');
      if (d.length === 9 && /^5/.test(d)) d = '0' + d;
      if (d.length >= 9) res.push(d);
      return m;
    });
    return [...new Set(res)];
  }
  const phoneLooksValid = d => /^0(5\d{8}|[2-489]\d{7}|7\d{8})$/.test(d);

  const api = { DEFAULT_PRICING, price, advice, execDims, isMeasured, status, STATUSES, STATUS_MAP, parseAddress, formatAddress, phones, phoneLooksValid, num, round2 };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SignsLogic = api;
})(typeof window !== 'undefined' ? window : this);
