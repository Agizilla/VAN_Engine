"""Shared UI assets: CSS, JS, and HTML rendering helpers."""
from typing import Any

UI_STYLES = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0d1117; color: #e6edf3; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem;
  }
  h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: .25rem; color: #f0f6fc; }
  h2 { font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 .75rem; color: #79c0ff; }
  .subtitle { color: #8b949e; margin-bottom: 1.5rem; font-size: .95rem; }
  .cat-group { margin-bottom: 2rem; }
  .cat-title {
    font-size: .85rem; text-transform: uppercase; letter-spacing: .06em;
    color: #58a6ff; margin-bottom: .5rem; border-bottom: 1px solid #21262d; padding-bottom: .25rem;
  }
  .hook-link {
    display: block; padding: .7rem 1rem; margin-bottom: 4px;
    background: #161b22; border: 1px solid #21262d; border-radius: 8px;
    text-decoration: none; color: #e6edf3; transition: all .15s;
  }
  .hook-link:hover { background: #1c2128; border-color: #30363d; }
  .hook-link .name { font-weight: 600; color: #58a6ff; }
  .hook-link .desc { font-size: .85rem; color: #8b949e; margin-top: 2px; }
  .hook-link .badge {
    display: inline-block; font-size: .7rem; padding: 1px 6px; border-radius: 4px;
    background: #1f2937; color: #8b949e; margin-left: 8px; vertical-align: middle;
  }
  .back { margin-bottom: 1rem; display: inline-block; color: #58a6ff; text-decoration: none; font-size: .9rem; }
  .back:hover { text-decoration: underline; }
  form { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 1.5rem; }
  .field { margin-bottom: 1rem; }
  .field label { display: block; font-weight: 600; font-size: .9rem; margin-bottom: 4px; }
  .field .desc { display: block; font-size: .8rem; color: #8b949e; margin-bottom: 4px; }
  .widget {
    width: 100%; padding: .5rem .75rem; background: #0d1117; color: #e6edf3;
    border: 1px solid #30363d; border-radius: 6px; font-size: .9rem;
  }
  .widget:focus { outline: none; border-color: #58a6ff; }
  .widget.code { font-family: 'JetBrains Mono', 'Cascadia Code', monospace; font-size: .82rem; }
  select.widget { cursor: pointer; }
  .toggle { position: relative; display: inline-block; width: 44px; height: 24px; cursor: pointer; }
  .toggle input { opacity: 0; width: 0; height: 0; }
  .toggle-slider {
    position: absolute; inset: 0; background: #21262d; border-radius: 12px; transition: .2s;
  }
  .toggle-slider::before {
    content: ""; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px;
    background: #e6edf3; border-radius: 50%; transition: .2s;
  }
  .toggle input:checked + .toggle-slider { background: #58a6ff; }
  .toggle input:checked + .toggle-slider::before { transform: translateX(20px); }
  button.submit {
    padding: .6rem 1.5rem; background: #238636; color: #fff; border: none; border-radius: 6px;
    font-weight: 600; font-size: .95rem; cursor: pointer; margin-top: .5rem;
  }
  button.submit:hover { background: #2ea043; }
  button.submit:disabled { opacity: .5; cursor: not-allowed; }
  .error {
    background: #3d1114; border: 1px solid #da3633; border-radius: 6px; padding: .75rem 1rem;
    margin-top: 1rem; font-size: .9rem; color: #ffa198;
  }
  .result {
    background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 1rem;
    margin-top: 1rem; overflow-x: auto;
  }
  .result pre { font-family: 'JetBrains Mono', 'Cascadia Code', monospace; font-size: .82rem; white-space: pre-wrap; }
  .status-badge {
    display: inline-block; padding: 1px 8px; border-radius: 12px;
    font-size: .75rem; font-weight: 600; margin-left: 8px;
  }
  .status-badge.ok { background: #1a3a2a; color: #3fb950; }
  .status-badge.err { background: #3d1114; color: #f85149; }
  .search {
    width: 100%; padding: .6rem .75rem; background: #0d1117; color: #e6edf3;
    border: 1px solid #30363d; border-radius: 8px; font-size: .95rem; margin-bottom: 1.5rem;
  }
  .search:focus { outline: none; border-color: #58a6ff; }
</style>
"""

MENU_SCRIPT = """
<script>
function filterHooks() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.hook-link').forEach(el => {
    el.style.display = el.textContent.toLowerCase().includes(q) ? 'block' : 'none';
  });
  document.querySelectorAll('.cat-group').forEach(g => {
    const visible = [...g.querySelectorAll('.hook-link')].some(l => l.style.display !== 'none');
    g.style.display = visible ? 'block' : 'none';
  });
}
</script>
"""

JSON_TREE_STYLES = """
<style>
.fd { margin-bottom: .85rem; }
.fd label { display: block; font-weight: 600; font-size: .9rem; margin-bottom: 4px; }
.fd .fd-desc { font-size: .8rem; color: #8b949e; margin-bottom: 4px; }
.toggle-label { display: flex !important; align-items: center; gap: .5rem; cursor: pointer; }
.toggle-label .toggle { flex-shrink: 0; }
.obj-header { cursor: pointer; user-select: none; padding: .4rem .6rem; background: #161b22; border-radius: 6px; border: 1px solid #21262d; margin-bottom: 4px; }
.obj-header:hover { background: #1c2128; }
.obj-arrow { display: inline-block; transition: transform .2s; font-size: .7rem; color: #58a6ff; margin-right: 4px; }
.obj-arrow.open { transform: rotate(90deg); }
.obj-body { display: none; padding-left: 1rem; border-left: 2px solid #21262d; margin: 4px 0 8px; }
.obj-body.open { display: block; }
.json-tree { font-family: 'JetBrains Mono', 'Cascadia Code', monospace; font-size: .82rem; line-height: 1.7; }
.j-key { color: #79c0ff; }
.j-str { color: #a5d6ff; }
.j-num { color: #ffa657; }
.j-bool { color: #ff7b72; }
.j-null { color: #8b949e; }
.j-bracket { color: #e6edf3; }
.j-count { color: #8b949e; font-size: .7rem; margin-left: 4px; }
.j-toggle { cursor: pointer; user-select: none; font-size: .6rem; color: #58a6ff; margin-right: 2px; }
.j-toggle.j-closed { display: inline-block; transform: rotate(-90deg); }
.j-collapsed { display: none !important; }
.j-item { border-left: 1px solid #21262d; }
</style>
"""

FORM_SCRIPT = r"""
<script>
var lastResult = null;
var formFields = {};

function buildForm(schema, container, prefix) {
  prefix = prefix || '';
  container.innerHTML = '';
  formFields = {};
  var props = (schema && schema.properties) || {};
  var required = new Set((schema && schema.required) || []);
  Object.keys(props).forEach(function(name) {
    var p = props[name];
    var key = prefix + name;
    var label = name.replace(/_/g, ' ');
    var req = required.has(name) ? ' <span style="color:#f85149;font-size:.75rem">*</span>' : '';
    var desc = p.description ? '<div class="fd-desc">' + escapeHtml(p.description) + '</div>' : '';

    if (p.enum && Array.isArray(p.enum)) {
      var opts = p.enum.map(function(v) {
        var sel = (v === p.default) ? ' selected' : '';
        return '<option value="' + escapeAttr(v) + '"' + sel + '>' + escapeHtml(v) + '</option>';
      }).join('');
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<select class="widget" data-key="' + escapeAttr(key) + '">' + opts + '</select></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('select'), type: 'string'};
    } else if (p.type === 'boolean') {
      var chk = p.default ? ' checked' : '';
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label class="toggle-label">' +
        '<label class="toggle"><input type="checkbox" data-key="' + escapeAttr(key) + '"' + chk + '><span class="toggle-slider"></span></label>' +
        '<span>' + escapeHtml(label) + req + '</span>' + desc + '</label></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('input'), type: 'boolean'};
    } else if (p.type === 'integer' || p.type === 'number') {
      var min = p.minimum !== undefined ? ' min="' + p.minimum + '"' : '';
      var max = p.maximum !== undefined ? ' max="' + p.maximum + '"' : '';
      var def = p.default !== undefined ? ' value="' + p.default + '"' : '';
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<input type="number" class="widget" data-key="' + escapeAttr(key) + '"' + min + max + def + '></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('input'), type: 'number'};
    } else if (p.type === 'object') {
      var id = 'obj-' + key.replace(/[^a-z0-9]/gi, '-');
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><div class="obj-header" onclick="toggleObj(\'' + escapeAttr(id) + '\')">' +
        '<span class="obj-arrow">&#9654;</span> <strong>' + escapeHtml(label) + '</strong>' + req + '</div>' + desc +
        '<div id="' + escapeAttr(id) + '" class="obj-body"></div></div>');
      var body = document.getElementById(id);
      buildForm(p, body, key + '.');
    } else if (p.type === 'array') {
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<textarea class="widget code" data-key="' + escapeAttr(key) + '" rows="2" placeholder="JSON array, e.g. [&quot;a&quot;,&quot;b&quot;]" spellcheck="false"></textarea></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('textarea'), type: 'array'};
    } else if (p.format === 'image-path') {
      var fid = 'fu-' + key.replace(/[^a-z0-9]/gi, '-');
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<div style="display:flex;gap:6px;align-items:center">' +
        '<input type="text" class="widget" data-key="' + escapeAttr(key) + '" placeholder="File path or data: URI" spellcheck="false" style="flex:1">' +
        '<button type="button" class="fu-btn" data-fid="' + escapeAttr(fid) + '" style="padding:6px 12px;background:#1e2a3a;color:#e6edf3;border:1px solid #30363d;border-radius:6px;cursor:pointer;font-size:12px">\uD83D\uDCC1 Browse</button>' +
        '</div>' +
        '<input type="file" id="' + escapeAttr(fid) + '" accept="image/*" style="display:none">' +
        '<textarea id="b64-' + escapeAttr(fid) + '" class="widget code" rows="2" placeholder="Paste base64 data URI here..." spellcheck="false" style="display:none;margin-top:4px;font-size:11px"></textarea>' +
        '<div style="margin-top:4px">' +
        '<label style="font-size:11px;color:#8b949e;cursor:pointer"><input type="checkbox" class="fu-b64-toggle" data-b64="b64-' + escapeAttr(fid) + '" data-target="' + escapeAttr(key) + '"> Paste base64 instead</label>' +
        '</div></div>');
      var textInput = container.lastElementChild.querySelector('input[type="text"]');
      formFields[key] = {el: textInput, type: 'string'};
      var fileInput = container.lastElementChild.querySelector('input[type="file"]');
      fileInput.addEventListener('change', function() {
        var file = this.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function(e) {
          textInput.value = e.target.result;
        };
        reader.readAsDataURL(file);
      });
      container.lastElementChild.querySelector('.fu-btn').addEventListener('click', function() {
        document.getElementById(this.dataset.fid).click();
      });
      container.lastElementChild.querySelector('.fu-b64-toggle').addEventListener('change', function() {
        var ta = document.getElementById(this.dataset.b64);
        if (this.checked) {
          ta.style.display = 'block';
          textInput.style.display = 'none';
          formFields[key].el = ta;
        } else {
          ta.style.display = 'none';
          textInput.style.display = '';
          formFields[key].el = textInput;
        }
      });
    } else {
      var isLong = (p.description && p.description.length > 60) || (label === 'text');
      var tag = isLong ? 'textarea' : 'input';
      var typeAttr = isLong ? '' : ' type="text"';
      var rows = isLong ? ' rows="4"' : '';
      var def = p.default !== undefined ? (isLong ? '>' + escapeHtml(String(p.default)) : ' value="' + escapeAttr(String(p.default)) + '"') : (isLong ? '>' : '');
      var close = isLong ? '</textarea>' : '';
      var isJsonLike = name.toLowerCase().indexOf('json') !== -1 || (p.description && p.description.toLowerCase().indexOf('json') !== -1);
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<' + tag + typeAttr + ' class="widget' + (isLong ? ' code' : '') + '" data-key="' + escapeAttr(key) + '"' + rows + ' placeholder="' + escapeAttr(label) + '" spellcheck="false"' + def + close + '></div>' +
        (isJsonLike ? '<div style="margin-top:4px"><button type="button" class="json-builder-btn" data-key="' + escapeAttr(key) + '" style="padding:4px 10px;background:#1e2a3a;color:#e6edf3;border:1px solid #30363d;border-radius:4px;cursor:pointer;font-size:11px">\uD83D\uDDD2 Build JSON</button></div>' : ''));
      var el = container.lastElementChild.querySelector(tag);
      formFields[key] = {el: el, type: 'string'};
      if (isJsonLike) {
        container.lastElementChild.querySelector('.json-builder-btn').addEventListener('click', function() {
          openJsonBuilder(key, el);
        });
      }
    }
  });
}

function toggleObj(id) {
  var body = document.getElementById(id);
  if (!body) return;
  body.classList.toggle('open');
  var arrow = body.parentElement.querySelector('.obj-arrow');
  if (arrow) arrow.classList.toggle('open');
}

function collectFormData() {
  var data = {};
  Object.keys(formFields).forEach(function(key) {
    var f = formFields[key];
    if (f.type === 'boolean') {
      data[key] = f.el.checked;
    } else if (f.type === 'number') {
      data[key] = f.el.value !== '' ? Number(f.el.value) : null;
    } else if (f.type === 'array') {
      try {
        data[key] = f.el.value ? JSON.parse(f.el.value) : [];
      } catch(e) {
        data[key] = f.el.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      }
    } else {
      data[key] = f.el.value || '';
    }
  });
  var out = {};
  Object.keys(data).forEach(function(k) {
    var parts = k.split('.');
    var cur = out;
    for (var i = 0; i < parts.length - 1; i++) {
      if (!cur[parts[i]]) cur[parts[i]] = {};
      cur = cur[parts[i]];
    }
    if (data[k] !== null) cur[parts[parts.length - 1]] = data[k];
  });
  return out;
}

function renderJSONTree(data, container) {
  container.innerHTML = '<div class="json-tree">' + renderJSONValue(data, '') + '</div>';
}

function renderJSONValue(val, path) {
  if (val === null || val === undefined) return '<span class="j-null">null</span>';
  if (typeof val === 'boolean') return '<span class="j-bool">' + val + '</span>';
  if (typeof val === 'number') return '<span class="j-num">' + val + '</span>';
  if (typeof val === 'string') return '<span class="j-str">"' + escapeHtml(val) + '"</span>';
  if (Array.isArray(val)) {
    if (val.length === 0) return '<span class="j-bracket">[</span><span class="j-null">empty</span><span class="j-bracket">]</span>';
    var id = 'j-' + path.replace(/[^a-z0-9]/gi, '-');
    var items = val.map(function(v, i) {
      return '<div class="j-item" style="padding-left:1.5rem">' + renderJSONValue(v, path + '-' + i) + '</div>';
    }).join('');
    return '<span class="j-toggle" onclick="toggleJTree(\'' + escapeAttr(id) + '\')">&#9660;</span>' +
      '<span class="j-bracket">[</span><span class="j-count">' + val.length + '</span>' +
      '<div id="' + escapeAttr(id) + '">' + items + '</div><span class="j-bracket">]</span>';
  }
  if (typeof val === 'object') {
    var keys = Object.keys(val);
    if (keys.length === 0) return '<span class="j-bracket">{</span><span class="j-null">empty</span><span class="j-bracket">}</span>';
    var id2 = 'j-' + path.replace(/[^a-z0-9]/gi, '-');
    var props = keys.map(function(k) {
      return '<div class="j-item" style="padding-left:1.5rem"><span class="j-key">"' + escapeHtml(k) + '"</span>: ' + renderJSONValue(val[k], path + '-' + k) + '</div>';
    }).join('');
    return '<span class="j-toggle" onclick="toggleJTree(\'' + escapeAttr(id2) + '\')">&#9660;</span>' +
      '<span class="j-bracket">{</span><span class="j-count">' + keys.length + '</span>' +
      '<div id="' + escapeAttr(id2) + '">' + props + '</div><span class="j-bracket">}</span>';
  }
  return escapeHtml(String(val));
}

function toggleJTree(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('j-collapsed');
  var toggle = el.previousElementSibling.previousElementSibling;
  if (toggle && toggle.classList) toggle.classList.toggle('j-closed');
}

async function submitForm(skillName) {
  var btn = document.getElementById('submit-btn');
  var prevBtn = document.getElementById('preview-btn');
  var resultDiv = document.getElementById('result');
  var errorDiv = document.getElementById('error');
  var previewDiv = document.getElementById('preview-container');
  var treeDiv = document.getElementById('json-tree-view');

  btn.disabled = true; btn.textContent = 'Running\u2026';
  resultDiv.innerHTML = ''; errorDiv.innerHTML = ''; errorDiv.style.display = 'none';
  previewDiv.style.display = 'none'; previewDiv.innerHTML = '';
  treeDiv.style.display = 'none'; treeDiv.innerHTML = '';
  if (prevBtn) { prevBtn.disabled = true; prevBtn.textContent = '\u25B6 Preview'; }

  var data = collectFormData();
  try {
    var resp = await fetch('/hooks/' + skillName, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    var text = await resp.text();
    var json = null;
    try { json = JSON.parse(text); } catch(e) {}

    if (resp.ok) {
      resultDiv.innerHTML = '<pre>' + escapeHtml(text) + '</pre>';
      if (json) {
        treeDiv.style.display = 'block';
        renderJSONTree(json, treeDiv);
        lastResult = json;
        if (lastResult && lastResult.result && lastResult.result.html) {
          if (prevBtn) { prevBtn.disabled = false; prevBtn.textContent = '\u25B6 Preview'; }
        }
        // skill-specific rendering
        if (skillName === 'vibe_affirmations' && json.result) {
          renderAffirmationsAsArt(json.result, resultDiv);
        }
        if (skillName === 'text_rewrite' && json.result && json.result.variations && json.result.variations.length) {
          var origText = data.text || '';
          renderRewriteDiff(origText, json.result.variations, resultDiv);
        }
        if (skillName === 'dirty_talker' && json.result && json.result.phrase) {
          renderDirtyTalkerPreview(json.result, resultDiv);
        }
        if (skillName === 'emotion_svg' && json.result && json.result.svg) {
          renderSvgPreview(json.result, resultDiv);
        }
        if (skillName === 'bullshit_detector' && json.result) {
          renderBullshitAlert(json.result, resultDiv);
        }
        if (skillName === 'humor_ascii_generator' && json.result && json.result.ascii) {
          renderAsciiPreview(json.result, resultDiv);
        }
        if (skillName === 'batch_wizard' && json.result) {
          renderBatchWizard(json.result, resultDiv, skillName);
        }
      }
    } else {
      errorDiv.innerHTML = 'Status ' + resp.status + ': ' + escapeHtml(text);
      errorDiv.style.display = 'block';
    }
  } catch(e) {
    errorDiv.innerHTML = 'Network error: ' + escapeHtml(e.message);
    errorDiv.style.display = 'block';
  }
  btn.disabled = false; btn.textContent = 'Execute';
}

function previewResult() {
  var previewDiv = document.getElementById('preview-container');
  if (!lastResult || !lastResult.result || !lastResult.result.html) {
    previewDiv.innerHTML = '<div class="error" style="padding:1rem">No HTML result to preview</div>';
    previewDiv.style.display = 'block';
    return;
  }
  previewDiv.style.display = 'block';
  previewDiv.innerHTML = '<div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.5rem">' +
    '<span style="font-size:0.85rem;color:#8b949e">HTML Preview</span>' +
    '<button onclick="copyPreviewHtml()" style="background:#1e2a3a;color:#e6edf3;border:1px solid #30363d;border-radius:4px;padding:0.25rem 0.75rem;font-size:0.8rem;cursor:pointer;font-family:inherit">\U0001F4CB Copy HTML</button>' +
    '</div>' +
    '<iframe srcdoc="' + escapeAttr(lastResult.result.html) + '" style="width:100%;height:600px;border:1px solid #30363d;border-radius:8px"></iframe>';
}

function copyPreviewHtml() {
  if (!lastResult || !lastResult.result || !lastResult.result.html) return;
  navigator.clipboard.writeText(lastResult.result.html).then(function() {
    var btn = document.querySelector('#preview-container button');
    if (btn) { var t = btn.textContent; btn.textContent = '\u2713 Copied!'; setTimeout(function() { btn.textContent = t; }, 1500); }
  });
}

function escapeAttr(s) { return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escapeHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

// ─── VIBE AFFIRMATIONS — ASCII ART COMIC PREVIEW ────────────────────
function renderAffirmationsAsArt(result, container) {
  var items = result.affirmations || (result.affirmation ? [result.affirmation] : []);
  if (!items.length) return;
  var chars = ['\u2571', 'o', '\u25cb', '\u2022', '*', '+'];
  var hue = Math.floor(Math.random() * 360);
  var comic = '<div style="font-family:monospace;white-space:pre;line-height:1.3;padding:12px;background:#0a0a12;border-radius:8px;overflow-x:auto">';
  comic += '<div style="color:#888;font-size:10px;margin-bottom:6px">\u250c\u2500 VIBE AFFIRMATIONS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510</div>';
  items.forEach(function(aff, i) {
    var lines = aff.split(' ').reduce(function(acc, w) {
      if (!acc.length || acc[acc.length-1].length + w.length + 1 > 36) acc.push(w);
      else acc[acc.length-1] += ' ' + w;
      return acc;
    }, []);
    var bw = Math.max.apply(null, lines.map(function(l) { return l.length; })) + 4;
    var c = ['#ff6680','#66ffaa','#ffaa66','#aa88ff','#66ccff','#ff88cc'][i % 6];
    var cx = 8 + (i % 3) * 12;
    var cy = 14 + Math.floor(i / 3) * 6;
    comic += '<div style="color:' + c + ';margin-bottom:14px">';
    // stick figure (simple)
    comic += '  '.repeat(i % 3) + ' \u256d' + '\u2500'.repeat(4) + '\u256e' + '\n';
    comic += '  '.repeat(i % 3) + ' \u2502' + chars[i % chars.length] + '  \u2502' + '\n';
    comic += '  '.repeat(i % 3) + ' \u2570' + '\u2500'.repeat(4) + '\u256f' + '\n';
    comic += '  '.repeat(i % 3) + '  \u2571\u2572' + '\n';
    comic += '  '.repeat(i % 3) + ' \u2571  \u2572' + '\n';
    // speech bubble
    var sw = bw + 2;
    comic += '  '.repeat(i % 3) + ' ' + '\u250c' + '\u2500'.repeat(sw) + '\u2510' + '\n';
    lines.forEach(function(l) {
      var pad = sw - l.length;
      comic += '  '.repeat(i % 3) + ' \u2502 ' + l + ' '.repeat(pad) + '\u2502' + '\n';
    });
    comic += '  '.repeat(i % 3) + ' \u2514' + '\u2500'.repeat(sw) + '\u2518' + '\n';
    // tail
    comic += '  '.repeat(i % 3) + '   \u2570\u2500\u2500\u2572' + '\n';
    comic += '</div>';
  });
  comic += '<div style="color:#888;font-size:10px">\u2514' + '\u2500'.repeat(36) + '\u2518</div></div>';
  container.innerHTML = comic;
}

// ─── TEXT REWRITE — WORD-LEVEL DIFF PREVIEW ─────────────────────────
function wordDiff(oldWords, newWords) {
  var m = oldWords.length, n = newWords.length;
  var dp = Array(m + 1).fill().map(function() { return Array(n + 1).fill(0); });
  for (var i = 1; i <= m; i++) {
    for (var j = 1; j <= n; j++) {
      if (oldWords[i-1] === newWords[j-1]) dp[i][j] = dp[i-1][j-1] + 1;
      else dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
    }
  }
  var result = [];
  var i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i-1] === newWords[j-1]) {
      result.unshift({type: 'same', word: oldWords[i-1]});
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
      result.unshift({type: 'added', word: newWords[j-1]});
      j--;
    } else {
      result.unshift({type: 'removed', word: oldWords[i-1]});
      i--;
    }
  }
  return result;
}

function renderRewriteDiff(original, variations, container) {
  var html = '<div style="font-family:monospace;font-size:13px;line-height:1.6">';
  variations.forEach(function(v, vi) {
    var origWords = original.match(/\\S+\\s*/g) || [];
    var newWords = v.match(/\\S+\\s*/g) || [];
    var diff = wordDiff(origWords, newWords);
    html += '<div style="margin-bottom:16px;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px">';
    html += '<div style="color:#8b949e;font-size:10px;margin-bottom:6px">Variation ' + (vi + 1) + ':</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    // original
    html += '<div style="flex:1;min-width:200px"><div style="color:#8b949e;font-size:9px;margin-bottom:4px">ORIGINAL</div><div>';
    origWords.forEach(function(w) {
      html += '<span style="color:#8b949e">' + escapeHtml(w) + '</span>';
    });
    html += '</div></div>';
    // rewritten with diff
    html += '<div style="flex:1;min-width:200px"><div style="color:#8b949e;font-size:9px;margin-bottom:4px">REWRITTEN</div><div>';
    diff.forEach(function(d) {
      if (d.type === 'same') html += '<span style="color:#e6edf3">' + escapeHtml(d.word) + '</span>';
      else if (d.type === 'added') html += '<span style="color:#3fb950;font-weight:700">' + escapeHtml(d.word) + '</span>';
      else if (d.type === 'removed') html += '<span style="color:#f85149;text-decoration:line-through">' + escapeHtml(d.word) + '</span>';
    });
    html += '</div></div></div></div>';
  });
  html += '</div>';
  // popup button
  html += '<button onclick="showDiffPopup()" style="padding:6px 14px;background:#1e2a3a;color:#e6edf3;border:1px solid #30363d;border-radius:6px;cursor:pointer;font-size:12px">\\u26A0 Open Diff Popup</button>';
  container.innerHTML = html;
  // Store for popup
  window.__diffData = {original: original, variations: variations};
}

function showDiffPopup() {
  if (!window.__diffData) return;
  var d = window.__diffData;
  var w = window.open('', 'diff-popup', 'width=800,height=600,scrollbars=yes');
  if (!w) return;
  var origWords = d.original.match(/\\S+\\s*/g) || [];
  var html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Text Rewrite — Diff</title>';
  html += '<style>body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:24px;font-size:14px;line-height:1.6}';
  html += '.old{color:#f85149;text-decoration:line-through}.new{color:#3fb950;font-weight:700}.same{color:#e6edf3}</style></head><body>';
  html += '<h2 style="color:#58a6ff;font-size:16px;margin-bottom:16px">Original</h2>';
  html += '<div style="margin-bottom:24px;padding:12px;background:#161b22;border:1px solid #21262d;border-radius:6px">';
  html += '<pre style="white-space:pre-wrap;margin:0">' + escapeHtml(d.original) + '</pre></div>';
  d.variations.forEach(function(v, vi) {
    var newWords = v.match(/\\S+\\s*/g) || [];
    var diff = wordDiff(origWords, newWords);
    html += '<h3 style="color:#8b949e;font-size:12px;margin-bottom:8px">Variation ' + (vi+1) + '</h3>';
    html += '<div style="margin-bottom:20px;padding:12px;background:#161b22;border:1px solid #21262d;border-radius:6px">';
    diff.forEach(function(d2) {
      if (d2.type === 'same') html += '<span class="same">' + escapeHtml(d2.word) + '</span>';
      else if (d2.type === 'added') html += '<span class="new">' + escapeHtml(d2.word) + '</span>';
      else if (d2.type === 'removed') html += '<span class="old">' + escapeHtml(d2.word) + '</span>';
    });
    html += '</div>';
  });
  html += '</body></html>';
  w.document.write(html);
  w.document.close();
}

// ─── DIRTY TALKER — VOICE PLAYBACK PREVIEW ───────────────────────────
function renderDirtyTalkerPreview(result, container) {
  var phrase = result.phrase || '';
  var html = '<div style="font-family:monospace;padding:16px;background:#0d1117;border:1px solid #30363d;border-radius:8px;max-width:600px">';
  html += '<div style="color:#8b949e;font-size:10px;margin-bottom:6px">GENERATED PHRASE</div>';
  html += '<div style="color:#e6edf3;font-size:16px;padding:12px;background:#161b22;border-radius:6px;margin-bottom:12px">' + escapeHtml(phrase) + '</div>';
  if (result.sanitized) html += '<div style="color:#3fb950;font-size:11px;margin-bottom:8px">✓ Sanitized</div>';
  html += '<div style="display:flex;gap:8px">';
  html += '<button onclick="speakPhrase()" style="padding:8px 16px;background:#238636;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600">🔊 Speak</button>';
  html += '<button onclick="speakPhraseSlow()" style="padding:8px 16px;background:#1e2a3a;color:#e6edf3;border:1px solid #30363d;border-radius:6px;cursor:pointer;font-size:13px">🐢 Slow Mode</button>';
  html += '</div></div>';
  container.innerHTML = html;
  window.__dirtyPhrase = phrase;
}

function speakPhrase() {
  if (!window.__dirtyPhrase || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(window.__dirtyPhrase);
  u.rate = 1.0; u.pitch = 1.0;
  speechSynthesis.speak(u);
}

function speakPhraseSlow() {
  if (!window.__dirtyPhrase || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(window.__dirtyPhrase);
  u.rate = 0.6; u.pitch = 0.85;
  speechSynthesis.speak(u);
}

// ─── EMOTION SVG — RENDER SVG PREVIEW ───────────────────────────────
function renderSvgPreview(result, container) {
  var svg = result.svg || '';
  var emotion = result.emotion || 'neutral';
  var colors = {neutral:'#00f2fe', joy:'#66ff99', laugh:'#88ffbb', sad:'#aa88ff', surprise:'#66aaff', anger:'#ff6666', fear:'#cc66ff', disgust:'#88cc44', contempt:'#dd8844', tension:'#ffaa44', love:'#ff88aa', mischief:'#ff66aa'};
  var c = colors[emotion] || '#00f2fe';
  var html = '<div style="font-family:monospace;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:8px">';
  html += '<div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">';
  html += '<span style="color:' + c + ';font-weight:700;font-size:14px">Emotion: ' + emotion + '</span>';
  if (result.text) html += '<span style="color:#8b949e;font-size:11px">"' + escapeHtml(result.text) + '"</span>';
  html += '</div>';
  html += '<div style="background:#fff;border-radius:6px;padding:8px;display:flex;justify-content:center;max-height:400px;overflow:auto">';
  html += svg;
  html += '</div></div>';
  container.innerHTML = html;
}

// ─── BULLSHIT DETECTOR — ALERT BOX ──────────────────────────────────
function renderBullshitAlert(result, container) {
  var action = result.action || 'pass';
  var score = result.score !== undefined ? result.score : null;
  var level = result.level !== undefined ? result.level : 0;
  var message = result.message || '';
  var details = result.details || [];
  var isAlert = action === 'warn' || action === 'block';
  var map = {
    pass: {icon: '✅', color: '#3fb950', bg: '#0a2a1a', border: '#3fb95033', label: 'PASS — Looks good'},
    warn: {icon: '⚠️', color: '#d29922', bg: '#1a1a0a', border: '#d2992233', label: 'WARNING — Low quality'},
    block: {icon: '🚫', color: '#f85149', bg: '#2a0a0a', border: '#f8514933', label: 'BLOCKED — Try again'}
  };
  var m = map[action] || map.pass;
  var barW = score !== null ? Math.min(100, Math.max(0, score)) : 0;
  var barColor = barW < 30 ? '#3fb950' : barW < 60 ? '#d29922' : '#f85149';
  var html = '<div style="font-family:monospace;padding:16px;background:' + m.bg + ';border:2px solid ' + m.border + ';border-radius:10px;max-width:600px">';
  html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">';
  html += '<span style="font-size:24px">' + m.icon + '</span>';
  html += '<div><div style="color:' + m.color + ';font-weight:700;font-size:14px">' + m.label + '</div>';
  if (level > 0) html += '<div style="color:#8b949e;font-size:11px">Level ' + level + '</div>';
  html += '</div></div>';
  if (score !== null) {
    html += '<div style="margin:10px 0">';
    html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:#8b949e;margin-bottom:4px"><span>Score</span><span>' + barW + '/100</span></div>';
    html += '<div style="height:8px;background:#21262d;border-radius:4px;overflow:hidden"><div style="height:100%;width:' + barW + '%;background:' + barColor + ';border-radius:4px;transition:width .3s"></div></div>';
    html += '</div>';
  }
  if (message) html += '<div style="color:#e6edf3;font-size:12px;padding:8px;background:#00000066;border-radius:4px;margin-top:8px;white-space:pre-wrap">' + escapeHtml(message) + '</div>';
  html += '</div>';
  container.innerHTML = html;
}

// ─── HUMOR ASCII GENERATOR — RICH TEXT ASCII PREVIEW ────────────────
function renderAsciiPreview(result, container) {
  var ascii = result.ascii || '';
  var style = result.style || 'banner';
  var html = '<div style="font-family:monospace;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:8px">';
  html += '<div style="color:#8b949e;font-size:10px;margin-bottom:6px">ASCII ART — ' + style + '</div>';
  html += '<pre style="color:#58a6ff;background:#0a0a12;padding:16px;border-radius:6px;overflow-x:auto;line-height:1.2;font-size:12px;margin:0">' + escapeHtml(ascii) + '</pre>';
  html += '</div>';
  container.innerHTML = html;
}

// ─── BATCH WIZARD — DIRECTORY INPUT + MODAL ─────────────────────────
function renderBatchWizard(result, container, skillName) {
  var state = result.state || 'idle';
  var script = result.script || '';
  var grouped = result.grouped || {};
  var total = result.total || 0;
  var choices = result.choices || [];
  var options = result.options || [];
  var ext = result.ext || '';
  var html = '<div style="font-family:monospace">';
  if (state === 'welcome' || state === 'idle') {
    html += '<div style="padding:12px;background:#161b22;border:1px solid #30363d;border-radius:8px;margin-bottom:10px">';
    html += '<div style="color:#58a6ff;font-weight:700;font-size:13px;margin-bottom:6px">📂 Directory Scan</div>';
    if (script) html += '<pre style="color:#e6edf3;font-size:12px;white-space:pre-wrap;background:#0d1117;padding:8px;border-radius:4px">' + escapeHtml(script) + '</pre>';
    if (total > 0) html += '<div style="color:#8b949e;font-size:11px;margin-top:6px">Found ' + total + ' files</div>';
    html += '</div>';
  } else if (state === 'choose_type' || state === 'choose_action') {
    html += '<div style="padding:12px;background:#161b22;border:1px solid #30363d;border-radius:8px;margin-bottom:10px">';
    html += '<div style="color:' + (state === 'choose_type' ? '#d29922' : '#3fb950') + ';font-weight:700;font-size:13px;margin-bottom:6px">Step: ' + state.replace('_', ' ') + '</div>';
    if (script) html += '<pre style="color:#e6edf3;font-size:12px;white-space:pre-wrap;background:#0d1117;padding:8px;border-radius:4px">' + escapeHtml(script) + '</pre>';
    if (state === 'choose_type' && choices.length) {
      html += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px">';
      choices.forEach(function(c) {
        html += '<span style="padding:3px 8px;background:#1e2a3a;border:1px solid #30363d;border-radius:4px;font-size:11px;color:#e6edf3">' + escapeHtml(c) + '</span>';
      });
      html += '</div>';
    }
    html += '</div>';
  } else if (state === 'run') {
    var errs = result.errors || [];
    var ok = result.success_count || 0;
    var fail = result.error_count || 0;
    html += '<div style="padding:12px;background:#161b22;border:1px solid #30363d;border-radius:8px;margin-bottom:10px">';
    html += '<div style="color:#3fb950;font-weight:700;font-size:13px;margin-bottom:6px">✓ Processing Complete</div>';
    html += '<div style="color:#e6edf3;font-size:12px">' + ok + ' succeeded, ' + fail + ' failed</div>';
    if (errs.length) html += '<pre style="color:#f85149;font-size:11px;margin-top:6px;background:#0d1117;padding:8px;border-radius:4px">' + escapeHtml(errs.join('\n')) + '</pre>';
    html += '</div>';
  }
  html += '<button onclick="openBatchWizardModal()" style="padding:8px 16px;background:#238636;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;margin-top:4px">🔍 Open Wizard Modal</button>';
  html += '</div>';
  container.innerHTML = html;
  window.__batchResult = result;
}

function openBatchWizardModal() {
  var r = window.__batchResult;
  if (!r) return;
  var w = window.open('', 'batch-wizard', 'width=700,height=600,scrollbars=yes');
  if (!w) return;
  var html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Batch Wizard</title>';
  html += '<style>body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:20px;font-size:13px;line-height:1.5}';
  html += 'pre{background:#161b22;padding:10px;border-radius:6px;white-space:pre-wrap;font-size:12px}';
  html += 'h2{color:#58a6ff;font-size:15px}';
  html += '.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;margin:2px;background:#1e2a3a;border:1px solid #30363d}</style></head><body>';
  html += '<h2>📂 Batch Wizard — ' + (r.state || 'idle') + '</h2>';
  if (r.script) html += '<pre>' + escapeHtml(r.script) + '</pre>';
  if (r.grouped) {
    html += '<h3 style="color:#8b949e;font-size:12px;margin-top:12px">Files by type</h3><div>';
    Object.keys(r.grouped).forEach(function(ext) {
      html += '<div style="margin:4px 0"><span class="badge">' + escapeHtml(ext) + '</span> <span style="color:#8b949e">' + r.grouped[ext] + ' files</span></div>';
    });
    html += '</div>';
  }
  if (r.choices && r.choices.length) {
    html += '<h3 style="color:#8b949e;font-size:12px;margin-top:12px">Available choices</h3><div>';
    r.choices.forEach(function(c) { html += '<span class="badge" style="border-color:#d29922;color:#d29922">' + escapeHtml(c) + '</span> '; });
    html += '</div>';
  }
  if (r.total !== undefined) html += '<div style="margin-top:12px;color:#8b949e;font-size:11px">Total files: ' + r.total + '</div>';
  html += '</body></html>';
  w.document.write(html);
  w.document.close();
}

// ─── JSON BUILDER — DYNAMIC JSON POPUP ──────────────────────────────
function openJsonBuilder(paramName, textarea) {
  var w = window.open('', 'json-builder', 'width=650,height=550,scrollbars=yes');
  if (!w) return;
  var current = '';
  try { current = JSON.stringify(JSON.parse(textarea.value || '{}'), null, 2); } catch(e) { current = textarea.value || '{}'; }
  var html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>JSON Builder — ' + escapeHtml(paramName) + '</title>';
  html += '<style>body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:20px;font-size:13px}';
  html += 'h2{color:#58a6ff;font-size:15px;margin-bottom:10px}';
  html += '.row{display:flex;gap:6px;margin-bottom:6px;align-items:center}';
  html += '.row input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#e6edf3;padding:6px 8px;font-family:monospace;font-size:12px}';
  html += '.row input:focus{outline:none;border-color:#58a6ff}';
  html += '.row .del{background:#3d1114;border:1px solid #da3633;color:#ffa198;border-radius:4px;cursor:pointer;padding:4px 8px;font-size:11px}';
  html += '.row .del:hover{background:#5a1a1a}';
  html += '#addBtn{background:#1e2a3a;border:1px solid #30363d;color:#e6edf3;border-radius:4px;cursor:pointer;padding:6px 12px;font-size:12px;margin:8px 0}';
  html += '#addBtn:hover{background:#2a3a4a}';
  html += '#doneBtn{background:#238636;border:none;color:#fff;border-radius:6px;cursor:pointer;padding:8px 16px;font-size:13px;font-weight:600;margin-right:6px}';
  html += '#cancelBtn{background:#1e2a3a;border:1px solid #30363d;color:#e6edf3;border-radius:6px;cursor:pointer;padding:8px 16px;font-size:13px}';
  html += '#preview{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;margin-top:10px;font-size:11px;white-space:pre-wrap;max-height:150px;overflow:auto}';
  html += '.key-hint{color:#8b949e;font-size:10px;margin-bottom:8px}';
  html += '.type-select{background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#e6edf3;padding:4px;font-size:11px}</style></head><body>';
  html += '<h2>🛠 Build JSON: ' + escapeHtml(paramName) + '</h2>';
  html += '<div class="key-hint">Add key-value pairs. Supports strings, numbers, booleans, arrays, nested objects.</div>';
  html += '<div id="rows"></div>';
  html += '<button id="addBtn">+ Add Field</button>';
  html += '<div style="margin-top:10px"><button id="doneBtn">✓ Done — Use This JSON</button><button id="cancelBtn">Cancel</button></div>';
  html += '<pre id="preview">' + escapeHtml(current) + '</pre>';
  html += '<script>';
  html += 'var data = {};';
  try {
    var existing = JSON.parse(textarea.value || '{}');
    Object.keys(existing).forEach(function(k) {
      html += 'data[' + JSON.stringify(k) + '] = ' + JSON.stringify(existing[k]) + ';';
    });
  } catch(e) {}
  html += 'function addRow(k, v, t) {';
  html += '  var key = k || ""; var val = v !== undefined ? v : ""; var type = t || "string";';
  html += '  var div = document.createElement("div"); div.className = "row";';
  html += '  div.innerHTML = \'<input class="jk" placeholder="key" value="\' + escapeJs(key) + \'" spellcheck="false">\' +';
  html += '    \'<select class="jt" onchange="updatePreview()">\' +';
  html += '    \'<option value="string"\'>\' + (type==="string"?" selected":"") + \'</option>\' +';
  html += '    \'<option value="number"\'>\' + (type==="number"?" selected":"") + \'</option>\' +';
  html += '    \'<option value="boolean"\'>\' + (type==="boolean"?" selected":"") + \'</option>\' +';
  html += '    \'<option value="array"\'>\' + (type==="array"?" selected":"") + \'</option>\' +';
  html += '    \'<option value="null"\'>\' + (type==="null"?" selected":"") + \'</option>\' +';
  html += '    \'</select>\' +';
  html += '    \'<input class="jv" placeholder="value" value="\' + escapeJs(String(val)) + \'" spellcheck="false">\' +';
  html += '    \'<button class="del" onclick="this.parentElement.remove();updatePreview()">✕</button>\';';
  html += '  document.getElementById("rows").appendChild(div);';
  html += '}';
  html += 'function escapeJs(s) { return s.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }';
  html += 'function updatePreview() {';
  html += '  var obj = {};';
  html += '  document.querySelectorAll(".row").forEach(function(row) {';
  html += '    var k = row.querySelector(".jk").value.trim();';
  html += '    if (!k) return;';
  html += '    var v = row.querySelector(".jv").value;';
  html += '    var t = row.querySelector(".jt").value;';
  html += '    if (t === "number") v = parseFloat(v) || 0;';
  html += '    else if (t === "boolean") v = v === "true" || v === "1";';
  html += '    else if (t === "array") { try { v = JSON.parse(v); } catch(e) { v = []; } }';
  html += '    else if (t === "null") v = null;';
  html += '    obj[k] = v;';
  html += '  });';
  html += '  document.getElementById("preview").textContent = JSON.stringify(obj, null, 2);';
  html += '}';
  html += 'document.getElementById("addBtn").onclick = function() { addRow("","","string"); updatePreview(); };';
  html += 'document.getElementById("cancelBtn").onclick = function() { window.close(); };';
  html += 'document.getElementById("doneBtn").onclick = function() {';
  html += '  updatePreview();';
  html += '  var json = document.getElementById("preview").textContent;';
  html += '  window.opener.__jsonBuilderCallback(' + JSON.stringify(paramName) + ', json);';
  html += '  window.close();';
  html += '};';
  html += 'Object.keys(data).forEach(function(k) { addRow(k, data[k], typeof data[k]); });';
  html += 'updatePreview();';
  html += '<\/script>';
  html += '</body></html>';
  w.document.write(html);
  w.document.close();
}

// JSON builder callback — stored on the opener window
window.__jsonBuilderCallback = function(paramName, json) {
  // find the textarea for this param and set its value
  var ta = document.querySelector('textarea[data-key="' + escapeAttr(paramName) + '"], input[data-key="' + escapeAttr(paramName) + '"]');
  if (ta) ta.value = json;
  // trigger preview update
  if (window.updatePreview) window.updatePreview();
};

document.addEventListener('DOMContentLoaded', function() {
  var skillName = document.getElementById('hook-form').dataset.skill;
  fetch('/hooks/' + skillName).then(function(r) { return r.json(); }).then(function(man) {
    var schema = man.manifest ? man.manifest.input_schema : (man.input_schema || {});
    buildForm(schema, document.getElementById('form-fields'));
  });
});
</script>
"""

FORGE_SCRIPT = """
<script>
async function startForge() {
  const btn = document.getElementById('forge-btn');
  const output = document.getElementById('forge-output');
  const status = document.getElementById('forge-status');
  const errorDiv = document.getElementById('error');
  btn.disabled = true; btn.textContent = 'Forging\u2026';
  output.innerHTML = ''; errorDiv.innerHTML = ''; errorDiv.style.display = 'none';

  const form = document.getElementById('forge-form');
  const agents = [];
  const agentRows = form.querySelectorAll('.agent-row');
  agentRows.forEach(row => {
    const name = row.querySelector('.agent-name').value;
    const role = row.querySelector('.agent-role').value;
    const skills = row.querySelector('.agent-skills').value.split(',').map(s => s.trim()).filter(s => s);
    if (name && skills.length) {
      agents.push({name, role, skills: skills.map(s => ({skill: s, params: {}}))});
    }
  });
  const iterations = parseInt(document.getElementById('iterations').value) || 3;
  const seed = document.getElementById('seed').value;

  if (!agents.length) { errorDiv.textContent = 'Add at least one agent with skills'; errorDiv.style.display = 'block'; btn.disabled = false; btn.textContent = 'Forge'; return; }

  try {
    const resp = await fetch('/hooks/forge', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Accept': 'text/event-stream'},
      body: JSON.stringify({agents, iterations, seed, output_format: 'html'})
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let roundCount = 0;

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.round) roundCount = data.round;
            if (data.agent && data.skill) {
              const div = document.createElement('div');
              div.className = 'forge-entry';
              div.innerHTML = '<span class="agent-badge">' + data.agent + '</span> '
                + '<span class="skill-badge">' + data.skill + '</span> '
                + (data.result ? '<pre>' + JSON.stringify(data.result, null, 2) + '</pre>' : '');
              output.appendChild(div);
              output.scrollTop = output.scrollHeight;
            }
            if (data.html && data.round) {
              document.getElementById('live-preview').innerHTML = data.html;
            }
            if (data.artifact) {
              document.getElementById('live-preview').innerHTML = data.artifact;
            }
            if (data.session_id) {
              status.textContent = 'Session: ' + data.session_id;
            }
          } catch(e) {}
        }
      }
    }
    status.textContent = 'Complete! (' + roundCount + ' rounds)';
  } catch(e) {
    errorDiv.textContent = 'Error: ' + e.message;
    errorDiv.style.display = 'block';
  }
  btn.disabled = false; btn.textContent = 'Forge';
}

function addAgent() {
  const container = document.getElementById('agents-container');
  const idx = container.children.length;
  const div = document.createElement('div');
  div.className = 'agent-row';
  div.innerHTML = '<input class="agent-name widget" placeholder="Name" value="Agent' + (idx+1) + '">'
    + ' <input class="agent-role widget" placeholder="Role" value="contributor">'
    + ' <input class="agent-skills widget" placeholder="comic_compiler,vibe_affirmations" value="">'
    + ' <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">\u00d7</button>';
  container.appendChild(div);
}
</script>
"""

FORGE_UI_STYLES = """
<style>
  .forge-entry {
    background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
    padding: .75rem; margin-bottom: 6px; font-size: .85rem;
  }
  .agent-badge {
    display: inline-block; background: #1f2937; color: #58a6ff;
    padding: 1px 8px; border-radius: 4px; font-weight: 600; font-size: .8rem;
  }
  .skill-badge {
    display: inline-block; background: #1a3a2a; color: #3fb950;
    padding: 1px 8px; border-radius: 4px; font-size: .75rem; margin-left: 4px;
  }
  .forge-entry pre {
    font-family: 'JetBrains Mono', monospace; font-size: .78rem;
    margin-top: 4px; white-space: pre-wrap; color: #8b949e;
  }
  .agent-row {
    display: flex; gap: 8px; margin-bottom: 8px; align-items: center;
  }
  .agent-row .widget { flex: 1; }
  .agent-row .widget:first-child { max-width: 120px; }
  .agent-row .widget:nth-child(2) { max-width: 140px; }
  #live-preview {
    background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
    padding: 1rem; margin-top: 1rem; min-height: 200px; overflow-y: auto;
  }
  #forge-output {
    background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
    padding: .75rem; margin-top: 1rem; max-height: 400px; overflow-y: auto;
    font-family: 'JetBrains Mono', monospace; font-size: .82rem;
  }
  .split-panel {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;
  }
  @media (max-width: 700px) { .split-panel { grid-template-columns: 1fr; } }
</style>
"""

MIDI_UI_STYLES = """
<style>
  .midi-container { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
  @media (max-width: 700px) { .midi-container { grid-template-columns: 1fr; } }
  .piano-roll { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; min-height: 300px; }
  .sheet-music { background: #fff; border-radius: 8px; padding: 1rem; min-height: 300px; overflow-x: auto; }
  .midi-field { margin-bottom: .75rem; }
  .midi-field label { display: block; font-weight: 600; font-size: .85rem; margin-bottom: 4px; color: #e6edf3; }
  .midi-field input, .midi-field select { width: 100%; }
  .note-grid { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }
  .note-chip {
    background: #1f2937; color: #58a6ff; padding: 4px 10px; border-radius: 12px;
    font-family: monospace; font-size: .8rem; border: 1px solid #30363d;
  }
  .keyboard-row { display: flex; gap: 2px; margin-top: 8px; flex-wrap: wrap; }
  .piano-key {
    width: 32px; height: 80px; border-radius: 0 0 4px 4px; cursor: pointer;
    font-size: .6rem; text-align: center; display: flex; align-items: flex-end;
    justify-content: center; padding-bottom: 4px; border: 1px solid #555;
    transition: all .1s; user-select: none;
  }
  .piano-key.white { background: #e6edf3; color: #333; }
  .piano-key.black { background: #1f2937; color: #8b949e; width: 24px; height: 52px; margin: 0 -4px; z-index: 1; }
  .piano-key.active { background: #58a6ff !important; color: #fff; transform: scale(.95); }
  .piano-key:hover { filter: brightness(1.2); }
</style>
"""

MIDI_SCRIPT = """
<script>
let midiCtx = null;
let midiPlayback = null;

function noteFreq(note) {
  var map = {
    'C4':261.63,'C#4':277.18,'D4':293.66,'D#4':311.13,'E4':329.63,
    'F4':349.23,'F#4':369.99,'G4':392.00,'G#4':415.30,'A4':440.00,
    'A#4':466.16,'B4':493.88,'C5':523.25,'C#5':554.37,'D5':587.33,
    'D#5':622.25,'E5':659.25,'F5':698.46,'F#5':739.99,'G5':783.99,
    'G#5':830.61,'A5':880.00,'A#5':932.33,'B5':987.77
  };
  return map[note] || 440;
}

function updateMidiPreview() {
  var notes = document.getElementById('midi-notes').value.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
  var chipDiv = document.getElementById('note-chips');
  chipDiv.innerHTML = notes.map(function(n) { return '<span class="note-chip">' + n + '</span>'; }).join('');
}

function playMidi() {
  if (!midiCtx) midiCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (midiPlayback) { midiPlayback.forEach(function(t) { clearTimeout(t); }); midiPlayback = null; }

  var notes = document.getElementById('midi-notes').value.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
  var tempo = parseInt(document.getElementById('midi-tempo').value) || 120;
  var dur = 60 / tempo;
  var timers = [];

  notes.forEach(function(n, i) {
    var freq = noteFreq(n);
    if (!freq) return;
    var start = midiCtx.currentTime + i * dur;
    var t = setTimeout(function() {
      var osc = midiCtx.createOscillator();
      var gain = midiCtx.createGain();
      osc.connect(gain);
      gain.connect(midiCtx.destination);
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.15, midiCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, midiCtx.currentTime + dur * 0.8);
      osc.start();
      osc.stop(midiCtx.currentTime + dur * 0.8);
    }, (start - midiCtx.currentTime) * 1000);
    timers.push(t);
  });
  midiPlayback = timers;
}

function addNoteToSequence(note) {
  var input = document.getElementById('midi-notes');
  var current = input.value.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
  current.push(note);
  input.value = current.join(',');
  updateMidiPreview();
}
</script>
"""


def render_param_html(name: str, prop: dict, required: bool, value: Any = None) -> str:
    ptype = prop.get("type", "string")
    enum_vals = prop.get("enum")
    default = prop.get("default", "")
    desc = prop.get("description", "")
    label = name.replace("_", " ").title()
    val = value if value is not None else default
    rows = []
    rows.append(f'<div class="field">')
    rows.append(f'  <label for="{name}">{label}{" *" if required else ""}</label>')
    if desc:
        rows.append(f'  <span class="desc">{desc}</span>')
    if enum_vals:
        rows.append(f'  <select name="{name}" id="{name}" class="widget">')
        for opt in enum_vals:
            sel = ' selected' if str(opt) == str(val) else ''
            rows.append(f'    <option value="{opt}"{sel}>{opt}</option>')
        rows.append(f'  </select>')
    elif ptype == "boolean":
        chk = ' checked' if val else ''
        rows.append(f'  <label class="toggle">')
        rows.append(f'    <input type="checkbox" name="{name}" id="{name}"{chk}>')
        rows.append(f'    <span class="toggle-slider"></span>')
        rows.append(f'  </label>')
    elif ptype == "integer":
        min_v = prop.get("minimum", "")
        max_v = prop.get("maximum", "")
        attrs = f' min="{min_v}"' if min_v != "" else ""
        attrs += f' max="{max_v}"' if max_v != "" else ""
        rows.append(f'  <input type="number" name="{name}" id="{name}" value="{val}"{attrs} class="widget">')
    elif ptype == "number":
        min_v = prop.get("minimum", "")
        max_v = prop.get("maximum", "")
        attrs = f' min="{min_v}"' if min_v != "" else ""
        attrs += f' max="{max_v}"' if max_v != "" else ""
        attrs += ' step="0.1"'
        rows.append(f'  <input type="number" name="{name}" id="{name}" value="{val}"{attrs} class="widget">')
    elif ptype == "array":
        rows.append(f'  <textarea name="{name}" id="{name}" class="widget code" rows="3">json array\u2026</textarea>')
    elif ptype == "object":
        rows.append(f'  <textarea name="{name}" id="{name}" class="widget code" rows="4">json object\u2026</textarea>')
    else:
        rows.append(f'  <input type="text" name="{name}" id="{name}" value="{val}" class="widget">')
    rows.append(f'</div>')
    return "\n".join(rows)


def render_menu_page(skills: dict) -> str:
    cats: dict[str, list[tuple[str, object]]] = {}
    for name in sorted(skills):
        s = skills[name]
        cat = getattr(s, "category", "general") or "general"
        cats.setdefault(cat, []).append((name, s))
    hooks_rows = ""
    for cat in sorted(cats):
        hooks_rows += f'<div class="cat-group">'
        hooks_rows += f'<div class="cat-title">{cat}</div>'
        for name, s in cats[cat]:
            desc = getattr(s, "description", "")[:80]
            tags = getattr(s, "tags", [])
            badges = "".join(f'<span class="badge">{t}</span>' for t in (tags or [])[:3])
            hooks_rows += f'<a href="/hooks/ui/{name}" class="hook-link">'
            hooks_rows += f'  <div><span class="name">{name}</span>{badges}</div>'
            hooks_rows += f'  <div class="desc">{desc}</div>'
            hooks_rows += f'</a>'
        hooks_rows += f'</div>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SAAS Hooks \u2014 Menu</title>{UI_STYLES}{MENU_SCRIPT}
</head><body>
  <h1>SAAS Hooks API</h1>
  <p class="subtitle">{len(skills)} endpoints \u2014 pick one to execute</p>
  <div class="cat-group">
    <div class="cat-title">\u2726 Special</div>
    <a href="/hooks/ui/forge" class="hook-link" style="border-color:#238636">
      <div><span class="name" style="color:#3fb950">forge</span><span class="badge" style="background:#1a3a2a;color:#3fb950">multi-agent</span></div>
      <div class="desc">Spawn N agents with skills \u2014 they build together in real time via SSE</div>
    </a>
  </div>
  <input type="text" id="search" class="search" placeholder="Filter hooks\u2026" oninput="filterHooks()">
  {hooks_rows}
</body></html>"""


def render_form_page(skill_name: str, skill: object) -> str:
    schema = getattr(skill, "input_schema", {}) or {}
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    desc = getattr(skill, "description", "")
    tags = getattr(skill, "tags", [])
    badges = "".join(f'<span class="badge">{t}</span>' for t in (tags or [])[:4])
    if props:
        fields_html = "\n".join(
            render_param_html(name, prop, name in required)
            for name, prop in props.items()
        )
    else:
        fields_html = '<p style="color:#8b949e;font-size:.9rem">This hook takes no parameters. Submit to execute.</p>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{skill_name} \u2014 SAAS Hook</title>{UI_STYLES}{JSON_TREE_STYLES}{FORM_SCRIPT}
</head><body>
  <a href="/hooks/ui" class="back">\u2190 Back to menu</a>
  <h1>{skill_name}</h1>
  <p class="subtitle">{desc}{badges}</p>
  <form id="hook-form" data-skill="{skill_name}" onsubmit="event.preventDefault();submitForm('{skill_name}')">
    <div id="form-fields"><p style="color:#8b949e;font-size:.9rem">Loading form\u2026</p></div>
    <div style="display:flex;gap:0.5rem;align-items:center;margin-top:1rem">
      <button type="submit" class="submit" id="submit-btn">Execute</button>
      <button type="button" class="submit" id="preview-btn" style="background:#1e2a3a;border:1px solid #30363d;color:#e6edf3" disabled onclick="previewResult()">\u25B6 Preview</button>
    </div>
  </form>
  <div id="error" class="error" style="display:none"></div>
  <div id="json-tree-view" class="result" style="display:none;margin-top:1rem"></div>
  <div id="result" class="result" style="margin-top:1rem"></div>
  <div id="preview-container" style="display:none;margin-top:1rem"></div>
</body></html>"""


MIDI_UI_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mike — MIDI Composer</title>""" + "{UI_STYLES}{MIDI_UI_STYLES}{MIDI_SCRIPT}" + r"""
</head><body>
  <a href="/hooks/ui" class="back">← Back to menu</a>
  <h1>🎹 Mike — MIDI Composer</h1>
  <p class="subtitle">Compose note sequences, hear them play, render sheet music via VexFlow</p>

  <div class="midi-field">
    <label for="midi-notes">Notes (comma-separated)</label>
    <input type="text" id="midi-notes" class="widget" value="C4,E4,G4,C5,G4,E4,C4" oninput="updateMidiPreview()">
  </div>
  <div id="note-chips" class="note-grid"></div>
  <div class="keyboard-row" id="piano-keyboard"></div>

  <div style="display:flex;gap:.5rem;align-items:center;margin-top:.75rem;flex-wrap:wrap">
    <div class="midi-field" style="margin:0">
      <label for="midi-tempo">Tempo (BPM)</label>
      <input type="number" id="midi-tempo" class="widget" value="120" min="30" max="300" style="width:80px">
    </div>
    <button onclick="playMidi()" class="submit" style="background:#4A148C;margin-top:16px">▶ Play</button>
    <button onclick="renderSheetMusic()" style="background:#1e2a3a;color:#fff;border:1px solid #30363d;border-radius:6px;padding:.5rem 1.2rem;font-weight:600;cursor:pointer;margin-top:16px">🎼 Render Sheet Music</button>
    <button onclick="exportJSON()" style="background:#1e2a3a;color:#fff;border:1px solid #30363d;border-radius:6px;padding:.5rem 1.2rem;font-weight:600;cursor:pointer;margin-top:16px">💾 Export JSON</button>
  </div>

  <div class="midi-container">
    <div class="piano-roll">
      <h3 style="color:#e6edf3;margin:0 0 8px">Sheet Music</h3>
      <div id="sheet-music"><p style="color:#8b949e">Click "Render Sheet Music" to see VexFlow notation</p></div>
    </div>
    <div>
      <h3 style="color:#e6edf3;margin:0 0 8px">Piano Keys</h3>
      <div id="piano-keys" style="display:flex;flex-wrap:wrap;gap:2px"></div>
    </div>
  </div>

  <script>
    function renderSheetMusic() {
      var n = document.getElementById('midi-notes').value;
      var t = parseInt(document.getElementById('midi-tempo').value) || 120;
      fetch('/hooks/midi_render', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({notes: n, tempo: t, format: 'html'})
      }).then(function(r) { return r.text(); }).then(function(h) {
        document.getElementById('sheet-music').innerHTML = h;
      });
    }
    function exportJSON() {
      var n = document.getElementById('midi-notes').value;
      var t = parseInt(document.getElementById('midi-tempo').value) || 120;
      fetch('/hooks/midi_render', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({notes: n, tempo: t, format: 'json'})
      }).then(function(r) { return r.json(); }).then(function(d) {
        var b = new Blob([JSON.stringify(d.result, null, 2)], {type: 'application/json'});
        var a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = 'midi_composition_' + Date.now() + '.json';
        a.click();
      });
    }
    updateMidiPreview();
    var keys = ['C4','C#4','D4','D#4','E4','F4','F#4','G4','G#4','A4','A#4','B4','C5','C#5','D5','D#5','E5','F5','F#5','G5','G#5','A5','A#5','B5'];
    var container = document.getElementById('piano-keys');
    keys.forEach(function(k) {
      var el = document.createElement('div');
      el.className = 'piano-key ' + (k.includes('#') ? 'black' : 'white');
      el.textContent = k;
      el.onclick = function() { addNoteToSequence(k); };
      container.appendChild(el);
    });
  </script>
</body></html>"""
