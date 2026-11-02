// Dependency-free analysis. Runs locally in the browser; Studio exports never leave the device.
export function parseCsv(text) {
  if (typeof text !== 'string' || !text.trim()) throw new Error('CSV file is empty');
  const rows = []; let row = [], cell = '', quoted = false;
  text = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') { cell += '"'; i++; }
      else if (quoted) quoted = false;
      else if (!cell) quoted = true;
      else cell += c;
    } else if (quoted) cell += c;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\r' || c === '\n') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); cell = '';
      if (row.some(v => v.trim())) rows.push(row);
      row = [];
    } else cell += c;
  }
  if (quoted) throw new Error('Malformed CSV: unclosed quoted field');
  row.push(cell); if (row.some(v => v.trim())) rows.push(row);
  return rows;
}
const norm = s => String(s ?? '').toLowerCase().replace(/\([^)]*\)/g, '').replace(/[^a-z0-9]/g, '');
const number = s => {
  const x = String(s ?? '').trim().replace(/[,\s%]/g, '');
  if (!x || /^[-—–]|n\/a$/i.test(x)) return null;
  const n = Number(x); return Number.isFinite(n) ? n : null;
};
const median = vals => {
  const v = vals.filter(x => x !== null && Number.isFinite(x)).sort((a,b) => a-b);
  return v.length ? (v[(v.length-1)>>1] + v[v.length>>1])/2 : null;
};
const formatType = value => {
  const s = String(value || '').toLowerCase();
  if (s.includes('short')) return 'Shorts';
  if (s.includes('live')) return 'Live';
  if (s.includes('video') || s.includes('long')) return 'Long-form';
  return 'Unspecified';
};
export function analyzeStudioCsv(text) {
  const data = parseCsv(text); if (data.length < 2) throw new Error('CSV requires a header and at least one video row');
  const header = data[0].map(norm);
  const column = (...names) => names.map(norm).map(name => header.indexOf(name)).find(i => i >= 0) ?? -1;
  const titleCol = column('Video title','Content','Video','Title');
  if (titleCol < 0) throw new Error('Missing video-title column. Export the YouTube Studio video table as CSV.');
  const cols = {
    impressions: column('Impressions'),
    ctr: column('Impressions click-through rate (%)','Impressions click through rate','Impressions CTR'),
    avgViewed: column('Average percentage viewed (%)','Average percentage viewed'),
    stayed: column('Stayed to watch (%)','Stayed to watch'),
    engaged: column('Engaged views'), views: column('Views'),
    search: column('YouTube search'),
    type: column('Content type','Video type','Format')
  };
  const metrics = Object.entries(cols).filter(([k,v]) => !['type'].includes(k) && v >= 0).map(([k]) => k);
  if (!metrics.length) throw new Error('No supported performance columns found (impressions, CTR, views, engaged views or retention).');
  const videos = data.slice(1).map((r, i) => {
    const title = String(r[titleCol] ?? '').trim();
    const v = { title, format: cols.type >= 0 ? formatType(r[cols.type]) : 'Unspecified', line: i + 2 };
    for (const k of metrics) v[k] = number(r[cols[k]]);
    return v;
  }).filter(v => v.title && !/^total$/i.test(v.title));
  if (!videos.length) throw new Error('No individual video rows found; export the per-video report, not totals only.');
  const baseline = {};
  for (const group of ['Shorts','Long-form','Live','Unspecified']) {
    const members = videos.filter(v => v.format === group);
    baseline[group] = {};
    for (const k of metrics) {
      const values = members.map(v => v[k]).filter(v => v !== null);
      baseline[group][k] = { median: values.length >= 3 ? median(values) : null, sample: values.length };
    }
  }
  for (const v of videos) {
    const b = baseline[v.format]; v.findings = [];
    const add = (kind, message, metric) => v.findings.push({kind, message, metric});
    if (v.impressions !== undefined && v.ctr !== undefined && v.impressions !== null && v.impressions >= 100 && v.ctr !== null && b.ctr.median !== null && v.ctr < b.ctr.median * 0.75) {
      add('review','Below comparable channel CTR. Test a clearer, accurate title/thumbnail; verify YouTube Reach before editing.','ctr');
    }
    if (v.avgViewed !== undefined && v.avgViewed !== null && b.avgViewed.median !== null && v.avgViewed < b.avgViewed.median * 0.75 && (v.views ?? v.engaged ?? 0) >= 50) {
      add('review','Average percentage viewed is below comparable uploads. Inspect retention curve and opening before revising the edit.','avgViewed');
    }
    if (v.stayed !== undefined && v.stayed !== null && b.stayed.median !== null && v.stayed < b.stayed.median * 0.75 && (v.views ?? v.engaged ?? 0) >= 100) {
      add('review','Shorts stayed-to-watch rate is below comparable uploads; examine the very first visual and sound.','stayed');
    }
    if (!v.findings.length) add('observe','No statistically meaningful underperformance detected by these limited export columns.','none');
  }
  return {
    kind:'youtube-studio-csv-audit', videos:videos.length, availableMetrics:metrics,
    formatWarning: cols.type < 0 ? 'No content-type column: Shorts and long-form may be mixed. Comparisons are indicative only.' : null,
    baseline, results:videos, limitations:[
      'This is descriptive, not a YouTube ranking score or causality test.',
      'Baselines require at least three same-format uploads with numeric data.',
      'CSV does not include per-second retention or query-level relevance unless explicitly exported.',
      'Small samples and format differences may make comparisons unreliable.'
    ]
  };
}
export function auditMetadata({title='',description='',keywords=[]}={}) {
  const checks = []; const t=String(title).trim(),d=String(description).trim();
  if (!t) checks.push('Title is missing.');
  if (t.length > 100) checks.push('Title exceeds YouTube’s 100-character limit.');
  if (!d) checks.push('Description is missing.');
  if (d.length > 5000) checks.push('Description exceeds YouTube’s 5,000-character limit.');
  const words = Array.isArray(keywords)?keywords:[];
  if (words.some(k=>String(k).trim()&&!((t+' '+d).toLowerCase().includes(String(k).trim().toLowerCase())))) checks.push('Some target phrases do not appear naturally in the title or description. Review intent, rather than stuffing keywords.');
  if (/\[(insert|add|placeholder|source|timestamp)/i.test(d)) checks.push('Description contains an editorial placeholder.');
  return {publishReady:checks.length===0, checks, notice:'Mechanical checks only. A human must verify intent, claims, thumbnail and video alignment.'};
}