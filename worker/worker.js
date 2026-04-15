// Cloudflare Worker — ZIP / Email / Drive Backup / Cloudinary Delete

const CORS = { 'Access-Control-Allow-Origin': '*' };
const JSON_CORS = { 'Content-Type': 'application/json', ...CORS };
const ok = d => new Response(JSON.stringify({ success: true, ...d }), { headers: JSON_CORS });
const err = (msg, s=500) => new Response('Error: ' + msg, { status: s, headers: CORS });

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: { ...CORS, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
    if (req.method !== 'POST') return new Response('Method not allowed', { status: 405, headers: CORS });
    const action = new URL(req.url).pathname;
    try {
      if (action === '/backup') {
        const data = await req.text();
        console.log('backup received, length:', data.length, 'type:', req.headers.get('content-type'));
        return await handleBackup({ data }, env);
      }
      if (action === '/mirror') {
        const data = await req.text();
        return await handleMirror({ data }, env);
      }
      const body = await req.json();
      if (action === '/email')  return await handleEmail(body, env);
      if (action === '/delete') return await handleDelete(body, env);
      return await handleZip(body);
    } catch(e) { return err(e.message); }
  },
  async scheduled(event, env) { await runDailyBackup(env); }
};

// ── AUTH ──
async function getToken(env) {
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: env.GMAIL_CLIENT_ID, client_secret: env.GMAIL_CLIENT_SECRET, refresh_token: env.GMAIL_REFRESH_TOKEN, grant_type: 'refresh_token' })
  });
  const d = await r.json();
  if (!d.access_token) throw new Error('Token error: ' + JSON.stringify(d));
  return d.access_token;
}

// ── EMAIL ──
async function handleEmail(body, env) {
  const { to, subject, text, html, attachments, attachmentUrls } = body;
  const token = await getToken(env);

  // הורד קבצים מ-URL
  let atts = [...(attachments||[])];
  for (const a of (attachmentUrls||[])) {
    try {
      const res = await fetch(a.url);
      if (!res.ok) continue;
      const bytes = new Uint8Array(await res.arrayBuffer());
      let bin = ''; const chunk = 8192;
      for (let i = 0; i < bytes.length; i += chunk) bin += String.fromCharCode(...bytes.subarray(i, i+chunk));
      atts.push({ base64: btoa(bin), name: a.name, mimeType: 'application/pdf' });
    } catch(e) {}
  }

  const B = 'b_' + Math.random().toString(36).slice(2);
  const B2 = 'i_' + Math.random().toString(36).slice(2);
  const enc = s => btoa(unescape(encodeURIComponent(s)));
  const subj = `=?UTF-8?B?${enc(subject)}?=`;
  const headers = [`From: ${env.GMAIL_SENDER}`, `To: ${to}`, `Subject: ${subj}`, 'MIME-Version: 1.0'];

  let lines;
  if (atts.length) {
    lines = [...headers, `Content-Type: multipart/mixed; boundary="${B}"`, '',
      `--${B}`, `Content-Type: multipart/alternative; boundary="${B2}"`, '',
      `--${B2}`, 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', enc(text||''), '',
      `--${B2}`, 'Content-Type: text/html; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', enc(html||text||''), '', `--${B2}--`
    ];
    for (const a of atts) {
      lines.push('', `--${B}`, `Content-Type: ${a.mimeType||'application/octet-stream'}; name="${a.name}"`,
        'Content-Transfer-Encoding: base64', `Content-Disposition: attachment; filename="=?UTF-8?B?${btoa(unescape(encodeURIComponent(a.name)))}?="`, '', a.base64);
    }
    lines.push(`--${B}--`);
  } else if (html) {
    lines = [...headers, `Content-Type: multipart/alternative; boundary="${B}"`, '',
      `--${B}`, 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', enc(text||''), '',
      `--${B}`, 'Content-Type: text/html; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', enc(html), '', `--${B}--`];
  } else {
    lines = [...headers, 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: base64', '', enc(text)];
  }

  const raw = btoa(unescape(encodeURIComponent(lines.join('\r\n')))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  const r = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
    method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw })
  });
  if (!r.ok) { const e = await r.json(); throw new Error(e.error?.message || 'Gmail failed'); }
  return ok();
}

// ── DRIVE BACKUP ──
async function getDriveFolderId(token) {
  const name = 'גיבויים — טיולים דגל ביתר';
  const s = await fetch(`https://www.googleapis.com/drive/v3/files?q=name='${encodeURIComponent(name)}' and mimeType='application/vnd.google-apps.folder' and trashed=false&fields=files(id)`,
    { headers: { 'Authorization': `Bearer ${token}` } });
  const d = await s.json();
  if (d.files?.length) return d.files[0].id;
  const c = await fetch('https://www.googleapis.com/drive/v3/files', {
    method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, mimeType: 'application/vnd.google-apps.folder' })
  });
  return (await c.json()).id;
}

async function uploadToDrive(token, folderId, filename, content) {
  const bnd = '---314159265358979';
  const body = `--${bnd}\r\nContent-Type: application/json\r\n\r\n${JSON.stringify({ name: filename, parents: [folderId] })}\r\n--${bnd}\r\nContent-Type: application/json\r\n\r\n${content}\r\n--${bnd}--`;
  return fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
    method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': `multipart/related; boundary="${bnd}"` }, body
  });
}

async function handleBackup({ data }, env) {
  if (!data) return err('No data', 400);
  console.log('backup: data length', data.length);
  const token = await getToken(env);
  console.log('backup: got token');
  const folderId = await getDriveFolderId(token);
  console.log('backup: folderId', folderId);
  const now = new Date();
  const d = now.toLocaleDateString('he-IL').replace(/\//g,'-');
  const t = now.toLocaleTimeString('he-IL',{hour:'2-digit',minute:'2-digit'}).replace(/:/g,'-');
  const filename = `גיבוי-טיולים-${d}_${t}.json`;
  const uploadRes = await uploadToDrive(token, folderId, filename, data);
  const uploadData = await uploadRes.json();
  console.log('backup: upload result', JSON.stringify(uploadData).slice(0,200));
  if(uploadData.error) throw new Error(uploadData.error.message || JSON.stringify(uploadData.error));
  return ok({ filename });
}

// Finds a file by exact name in a Drive folder; returns id or null
async function findDriveFile(token, folderId, name) {
  const q = `name='${name.replace(/'/g,"\\'")}' and '${folderId}' in parents and trashed=false`;
  const r = await fetch(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id)`,
    { headers: { 'Authorization': `Bearer ${token}` } });
  const d = await r.json();
  return d.files?.length ? d.files[0].id : null;
}

// Updates file content by id (media upload)
async function updateDriveFile(token, fileId, content) {
  return fetch(`https://www.googleapis.com/upload/drive/v3/files/${fileId}?uploadType=media`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: content
  });
}

// /mirror — overwrite a single rolling file state-latest.json in the Drive folder
async function handleMirror({ data }, env) {
  if (!data) return err('No data', 400);
  const token = await getToken(env);
  const folderId = await getDriveFolderId(token);
  const name = 'state-latest.json';
  const existingId = await findDriveFile(token, folderId, name);
  if (existingId) {
    const r = await updateDriveFile(token, existingId, data);
    const j = await r.json();
    if (j.error) throw new Error(j.error.message || 'mirror update failed');
  } else {
    const r = await uploadToDrive(token, folderId, name, data);
    const j = await r.json();
    if (j.error) throw new Error(j.error.message || 'mirror create failed');
  }
  return ok({ mirrored: name });
}

// Daily cron: copy latest mirror to a dated backup file
async function runDailyBackup(env) {
  try {
    const token = await getToken(env);
    const folderId = await getDriveFolderId(token);
    const latestId = await findDriveFile(token, folderId, 'state-latest.json');
    if (!latestId) { console.warn('runDailyBackup: no state-latest.json found, skipping'); return; }
    // Download content of latest
    const dl = await fetch(`https://www.googleapis.com/drive/v3/files/${latestId}?alt=media`,
      { headers: { 'Authorization': `Bearer ${token}` } });
    const content = await dl.text();
    const d = new Date().toLocaleDateString('he-IL').replace(/\//g,'-');
    const filename = `גיבוי-אוטומטי-${d}.json`;
    const up = await uploadToDrive(token, folderId, filename, content);
    const j = await up.json();
    if (j.error) throw new Error(j.error.message || 'daily backup upload failed');
    console.log('Daily backup done:', filename);
  } catch(e) { console.error('Backup failed:', e.message); }
}

// ── CLOUDINARY DELETE ──
async function handleDelete({ publicId }, env) {
  if (!publicId) return err('Missing publicId', 400);
  const ts = Math.floor(Date.now()/1000);
  const sig = await sha1(`public_id=${publicId}&timestamp=${ts}${env.CLOUDINARY_API_SECRET}`);
  const fd = new FormData();
  fd.append('public_id', publicId); fd.append('timestamp', ts);
  fd.append('api_key', env.CLOUDINARY_API_KEY); fd.append('signature', sig);
  for (const type of ['image','raw']) {
    const r = await fetch(`https://api.cloudinary.com/v1_1/${env.CLOUDINARY_CLOUD_NAME}/${type}/destroy`, { method:'POST', body:fd });
    if ((await r.json()).result === 'ok') break;
  }
  return ok();
}

async function sha1(msg) {
  const buf = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(msg));
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

// ── ZIP ──
async function handleZip({ files }) {
  if (!files?.length) return new Response('No files', { status: 400 });
  const bufs = await Promise.all(files.map(async f => {
    try {
      let data, name = f.name||'file';
      if (f.base64) {
        const bin = atob(f.base64); data = new Uint8Array(bin.length);
        for (let i=0;i<bin.length;i++) data[i]=bin.charCodeAt(i);
      } else {
        const r = await fetch(f.url); if (!r.ok) return null;
        data = new Uint8Array(await r.arrayBuffer());
        if (!name.toLowerCase().endsWith('.pdf')) name+='.pdf';
      }
      return {name,data};
    } catch(e){return null;}
  }));
  const valid = bufs.filter(Boolean);
  if (!valid.length) return new Response('No files downloaded', { status:500 });
  return new Response(buildZip(valid), { headers:{ 'Content-Type':'application/zip', 'Content-Disposition':'attachment; filename="trip-folder.zip"', ...CORS }});
}

function buildZip(files) {
  const enc = new TextEncoder(), lhs=[], chs=[];
  let off=0;
  for (const f of files) {
    const nb=enc.encode(f.name), d=f.data, crc=crc32(d), sz=d.length;
    const lh=new Uint8Array(30+nb.length), lv=new DataView(lh.buffer);
    lv.setUint32(0,0x04034b50,true);lv.setUint16(4,20,true);lv.setUint16(6,0x0800,true);
    lv.setUint32(14,crc,true);lv.setUint32(18,sz,true);lv.setUint32(22,sz,true);lv.setUint16(26,nb.length,true);
    lh.set(nb,30);
    const ch=new Uint8Array(46+nb.length), cv=new DataView(ch.buffer);
    cv.setUint32(0,0x02014b50,true);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x0800,true);
    cv.setUint32(16,crc,true);cv.setUint32(20,sz,true);cv.setUint32(24,sz,true);cv.setUint16(28,nb.length,true);cv.setUint32(42,off,true);
    ch.set(nb,46);
    lhs.push(lh,d); chs.push(ch); off+=lh.length+d.length;
  }
  const cdsz=chs.reduce((s,h)=>s+h.length,0);
  const eocd=new Uint8Array(22), ev=new DataView(eocd.buffer);
  ev.setUint32(0,0x06054b50,true);ev.setUint16(8,files.length,true);ev.setUint16(10,files.length,true);
  ev.setUint32(12,cdsz,true);ev.setUint32(16,off,true);
  const parts=[...lhs,...chs,eocd], total=parts.reduce((s,p)=>s+p.length,0), res=new Uint8Array(total);
  let p=0; for(const part of parts){res.set(part,p);p+=part.length;}
  return res;
}

function crc32(data) {
  const t=new Uint32Array(256);
  for(let i=0;i<256;i++){let c=i;for(let j=0;j<8;j++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[i]=c;}
  let crc=0xFFFFFFFF;
  for(let i=0;i<data.length;i++)crc=(crc>>>8)^t[(crc^data[i])&0xFF];
  return(crc^0xFFFFFFFF)>>>0;
}