const state = { prds: [], activeSlug: null };

const renderer = new marked.Renderer();
renderer.checkbox = (checked) => `<input type="checkbox" disabled ${checked ? 'checked' : ''}>`;
marked.setOptions({ renderer, breaks: true, gfm: true });

let toastTimer;
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg; el.className = `toast ${type} show`;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

function parseFrontmatter(text) {
  const m = text.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!m) return {};
  const fm = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.*)/);
    if (kv) fm[kv[1]] = kv[2].trim();
  }
  return fm;
}

function parseSections(text) {
  const sections = {};
  const re = /^##\s+(.+)$/gm;
  let lastIdx = 0, lastTitle = null;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (lastTitle) sections[lastTitle] = text.slice(lastIdx, m.index).trim();
    lastTitle = m[1].trim(); lastIdx = m.end();
  }
  if (lastTitle) sections[lastTitle] = text.slice(lastIdx).trim();
  return sections;
}

function extractArtifacts(text) {
  const set = new Set();
  const pats = [
    /`([^`]+\.[a-zA-Z]+)`/g,
    /\*\*File:\*\*\s*`([^`]+)`/g,
    /\*\*Status:\*\*\s*(Created|Modified)/g
  ];
  for (const re of pats) {
    let m;
    while ((m = re.exec(text)) !== null) {
      const v = m[1]; if (v.length > 3 && !set.has(v)) set.add(v);
    }
  }
  return Array.from(set);
}

function extClass(fp) {
  const e = fp.split('.').pop().toLowerCase();
  const map = { py: 'tag-standard', ts: 'tag-standard', tsx: 'tag-standard', js: 'tag-standard',
    html: 'tag-comprehensive', css: 'tag-advanced', json: 'tag-extended', md: 'tag-unknown',
    yaml: 'tag-extended', yml: 'tag-extended', toml: 'tag-extended' };
  return map[e] || 'tag-effort';
}

function parsePRD(text, filePath) {
  const fm = parseFrontmatter(text);
  const sections = parseSections(text.replace(/^---[\s\S]*?---\n*/, ''));
  const artifacts = extractArtifacts(text);
  return {
    slug: fm.slug || filePath.split('/').pop().replace(/\.(md|prd)$/,'') || 'unknown',
    task: fm.task || 'Untitled PRD',
    effort: fm.effort || 'standard',
    phase: fm.phase || 'unknown',
    progress: fm.progress || '0/0',
    mode: fm.mode || 'interactive',
    started: fm.started || '',
    updated: fm.updated || '',
    iteration: fm.iteration || '',
    file_path: filePath,
    artifacts,
    sections: Object.keys(sections),
    sectionContent: sections,
    frontmatter: fm,
    raw: text
  };
}

function renderPRD(prd) {
  if (!prd) return '<div class="empty-state"><div class="icon">📋</div><p>Select a PRD to view</p></div>';
  const fm = prd.frontmatter;
  let html = `<div class="prd-viewer"><h1>${esc(fm.task || prd.task)}</h1>`;
  html += '<div class="meta-bar">';
  for (const [k, v] of Object.entries({ effort: fm.effort, phase: fm.phase, progress: fm.progress, mode: fm.mode, iteration: fm.iteration })) {
    if (v) html += `<span class="tag tag-${v}">${k}: ${v}</span>`;
  }
  if (fm.started) html += `<span class="tag tag-effort">${fm.started.slice(0,10)}</span>`;
  html += '</div>';

  let bodyContent = '';
  for (const [title, body] of Object.entries(prd.sectionContent)) {
    const rendered = marked.parse(body || '');
    bodyContent += `<h2>${esc(title)}</h2>${rendered}`;
  }
  if (prd.artifacts.length) {
    bodyContent += '<h2>Artifacts</h2><table><tr><th>File</th><th>Status</th></tr>';
    for (const a of prd.artifacts) {
      const s = a.startsWith('**') ? 'Modified' : 'Created';
      bodyContent += `<tr><td><code>${esc(a.replace(/\*\*/g,''))}</code></td><td><span class="tag tag-${s === 'Created' ? 'complete' : 'build'}">${s}</span></td></tr>`;
    }
    bodyContent += '</table>';
  }

  if (bodyContent.length > 5000) {
    html += `<div class="prd-body-truncated">${bodyContent.slice(0, 5000)}</div>`;
    html += `<div class="prd-body-full" style="display:none">${bodyContent}</div>`;
    html += `<button class="show-more-btn" onclick="togglePRDContent(this)">Show More (${bodyContent.length - 5000} chars remaining)</button>`;
  } else {
    html += bodyContent;
  }

  html += '</div>';
  return html;
}

function togglePRDContent(btn) {
  const truncated = btn.parentElement.querySelector('.prd-body-truncated');
  const full = btn.parentElement.querySelector('.prd-body-full');
  if (truncated && full) {
    const showingFull = full.style.display !== 'none';
    truncated.style.display = showingFull ? 'block' : 'none';
    full.style.display = showingFull ? 'none' : 'block';
    btn.textContent = showingFull ? `Show More (${full.textContent.length - 5000} chars remaining)` : 'Show Less';
  }
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function renderListItem(prd) {
  const active = prd.slug === state.activeSlug ? ' active' : '';
  const phase = prd.phase || 'unknown';
  const effort = prd.effort || 'standard';
  const date = (prd.started || '').slice(0,10) || (prd.updated || '').slice(0,10) || '';
  return `<div class="prd-item${active}" data-slug="${prd.slug}">
    <div class="title">${esc(prd.task)}</div>
    <div class="meta">
      <span class="tag tag-${effort}">${effort}</span>
      <span class="tag tag-${phase}">${phase}</span>
      <span class="tag tag-effort">${prd.progress}</span>
      <span class="tag tag-effort">${prd.artifacts.length} artifacts</span>
    </div>
    <div class="date">${date}</div>
  </div>`;
}

function renderArtifacts(artifacts) {
  if (!artifacts || !artifacts.length) {
    return '<div class="empty-state">No artifacts extracted<br><span style="font-size:10px;color:var(--text3)">Files produced by this PRD</span></div>';
  }
  return artifacts.map(a => {
    const ext = a.split('.').pop();
    return `<div class="artifact-item"><span class="ext">.${ext}</span> ${esc(a)}</div>`;
  }).join('');
}

function updateUI() {
  const query = (document.getElementById('searchBox').value || '').toLowerCase();
  const filtered = query ? state.prds.filter(p => p.task.toLowerCase().includes(query) || p.slug.toLowerCase().includes(query)) : state.prds;
  document.getElementById('prdList').innerHTML = filtered.map(renderListItem).join('');
  document.getElementById('prdCount').textContent = `(${state.prds.length})`;
  document.getElementById('statsBar').innerHTML = `<span>📄 <span class="num">${state.prds.length}</span> PRDs</span><span>📎 <span class="num">${state.prds.reduce((a,p) => a + p.artifacts.length, 0)}</span> artifacts</span>`;
  localStorage.setItem('lastSearchQuery', query);
  updateTimeline();
  if (!state.activeSlug || !state.prds.find(p => p.slug === state.activeSlug)) {
    if (filtered.length) selectPRD(filtered[0].slug);
    else { document.getElementById('prdContent').innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>Select a PRD to view</p></div>';
      document.getElementById('artifactList').innerHTML = '<div class="empty-state">No PRD selected</div>';
      document.getElementById('artifactCount').textContent = ''; }
  }
}

function updateTimeline() {
  const bar = document.getElementById('timelineBar');
  if (state.prds.length < 2) { bar.innerHTML = ''; bar.style.display = 'none'; return; }
  bar.style.display = 'flex';
  const sorted = [...state.prds].sort((a,b) => (a.started||'').localeCompare(b.started||''));
  bar.innerHTML = sorted.map((p,i) => {
    const active = p.slug === state.activeSlug ? ' active' : '';
    const phase = p.phase || 'unknown';
    const date = (p.started||'').slice(0,10);
    const conn = i < sorted.length - 1 ? '<div class="timeline-connector"></div>' : '';
    return `<div class="timeline-node${active}" data-slug="${p.slug}"><div class="dot ${phase}"></div><div class="tlabel">${esc(p.task.slice(0,30))}</div><div class="tdate">${date}</div></div>${conn}`;
  }).join('');
}

function selectPRD(slug) {
  state.activeSlug = slug;
  localStorage.setItem('lastSelectedPrd', slug);
  const prd = state.prds.find(p => p.slug === slug);
  if (!prd) return;
  document.getElementById('prdContent').innerHTML = renderPRD(prd);
  document.getElementById('artifactList').innerHTML = renderArtifacts(prd.artifacts);
  document.getElementById('artifactCount').textContent = `(${prd.artifacts.length})`;
  updateUI();
  document.querySelector(`.prd-item.active`)?.scrollIntoView({ block: 'nearest' });
}

function loadPRD(text, filePath) {
  const prd = parsePRD(text, filePath);
  const existing = state.prds.findIndex(p => p.slug === prd.slug);
  if (existing >= 0) state.prds[existing] = prd;
  else state.prds.push(prd);
  state.prds.sort((a,b) => (b.started||'').localeCompare(a.started||''));
  updateUI();
  selectPRD(prd.slug);
}

function loadPRDs(prds) {
  for (const [text, fp] of prds) {
    const prd = parsePRD(text, fp);
    const existing = state.prds.findIndex(p => p.slug === prd.slug);
    if (existing >= 0) state.prds[existing] = prd;
    else state.prds.push(prd);
  }
  state.prds.sort((a,b) => (b.started||'').localeCompare(a.started||''));
  updateUI();
  if (!state.activeSlug && state.prds.length) selectPRD(state.prds[0].slug);
}

function readFile(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = () => rej(r.error);
    r.readAsText(file);
  });
}

document.addEventListener('dragover', e => {
  e.preventDefault();
  document.getElementById('dropZone').classList.add('active');
  document.getElementById('dropZone').querySelector('.box').style.border = '3px dashed #7c5cfc';
  document.getElementById('dropZone').querySelector('.box').style.background = 'rgba(124,92,252,0.08)';
});
document.addEventListener('dragleave', e => {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('active');
  document.getElementById('dropZone').querySelector('.box').style.border = '2px dashed var(--accent)';
  document.getElementById('dropZone').querySelector('.box').style.background = 'var(--surface)';
});
document.addEventListener('drop', async e => {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('active');
  document.getElementById('dropZone').querySelector('.box').style.border = '2px dashed var(--accent)';
  document.getElementById('dropZone').querySelector('.box').style.background = 'var(--surface)';
  const files = Array.from(e.dataTransfer.files);
  if (!files.length) return;
  const prds = [];
  for (const f of files) {
    if (!f.name.match(/PRD|\.prd|PRD_/i)) continue;
    const text = await readFile(f);
    prds.push([text, f.name]);
  }
  loadPRDs(prds);
  showToast(`Loaded ${prds.length} PRD${prds.length !== 1 ? 's' : ''}`, 'success');
});

document.getElementById('openFile').onclick = () => document.getElementById('fileInput').click();
document.getElementById('fileInput').onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  const text = await readFile(f);
  loadPRD(text, f.name);
  showToast(`Loaded: ${f.name}`, 'success');
  e.target.value = '';
};

document.getElementById('scanDir').onclick = () => document.getElementById('dirInput').click();
document.getElementById('dirInput').onchange = async e => {
  const files = Array.from(e.target.files);
  const prds = [];
  for (const f of files) {
    if (!f.name.match(/PRD|\.prd|PRD_/i)) continue;
    const text = await readFile(f);
    const relPath = f.webkitRelativePath || f.name;
    prds.push([text, relPath]);
  }
  loadPRDs(prds);
  showToast(`Loaded ${prds.length} PRDs from directory`, 'success');
  e.target.value = '';
};

document.getElementById('loadAll').onclick = async () => {
  try {
    if (window.electronAPI?.prd) {
      const res = await window.electronAPI.prd.scan();
      if (res.prds) {
        for (const p of res.prds) {
          const existing = state.prds.findIndex(x => x.slug === p.slug);
          if (existing >= 0) state.prds[existing] = p;
          else state.prds.push(p);
        }
        state.prds.sort((a,b) => (b.started||'').localeCompare(a.started||''));
        updateUI();
        if (!state.activeSlug && state.prds.length) selectPRD(state.prds[0].slug);
        showToast(`Loaded ${state.prds.length} PRDs`, 'success');
        return;
      }
    }
    const res = await fetch('/api/prd/scan', { method: 'POST' }).catch(() => null);
    if (res?.ok) {
      const data = await res.json();
      if (data.prds && data.prds.length > 0) {
        loadPRDs(data.prds.map(p => [p.raw || '', p.file_path || p.slug]));
        showToast(`Loaded ${data.prds.length} PRDs`, 'success');
        return;
      }
    }
    showToast('No backend available — use Open or Scan to load PRDs manually', 'info');
  } catch { showToast('Could not reach PRD backend', 'error'); }
};

document.getElementById('exportCatalog').onclick = () => {
  const catalog = state.prds.map(p => ({
    slug: p.slug,
    task: p.task,
    effort: p.effort,
    phase: p.phase,
    progress: p.progress,
    artifacts: p.artifacts,
    sections: p.sections,
    started: p.started,
    updated: p.updated,
  }));
  const blob = new Blob([JSON.stringify(catalog, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `prd_catalog_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Catalog exported', 'success');
};

document.getElementById('prdList').addEventListener('click', e => {
  const item = e.target.closest('.prd-item');
  if (item) selectPRD(item.dataset.slug);
});
document.getElementById('timelineBar').addEventListener('click', e => {
  const node = e.target.closest('.timeline-node');
  if (node) selectPRD(node.dataset.slug);
});

document.getElementById('searchBox').addEventListener('input', () => updateUI());

document.addEventListener('keydown', e => {
  const searchBox = document.getElementById('searchBox');
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    e.preventDefault();
    searchBox.focus();
    searchBox.select();
  }
  if (e.key === 'Escape') {
    searchBox.value = '';
    searchBox.blur();
    updateUI();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
    e.preventDefault();
    document.getElementById('fileInput').click();
  }
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    const items = document.querySelectorAll('.prd-item');
    const active = document.querySelector('.prd-item.active');
    let idx = Array.from(items).indexOf(active);
    if (e.key === 'ArrowDown') idx = Math.min(idx + 1, items.length - 1);
    else idx = Math.max(idx - 1, 0);
    if (items[idx]) selectPRD(items[idx].dataset.slug);
    e.preventDefault();
  }
});

(function restoreState() {
  const lastSlug = localStorage.getItem('lastSelectedPrd');
  const lastQuery = localStorage.getItem('lastSearchQuery');
  if (lastQuery) {
    document.getElementById('searchBox').value = lastQuery;
  }
  if (lastSlug) {
    state.activeSlug = lastSlug;
  }
})();

showToast('Open a PRD file or scan a directory to begin', 'info');
