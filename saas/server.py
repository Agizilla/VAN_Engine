#!/usr/bin/env python3
"""SAAS Hooks API Server — standalone, 256-skill auto-endpoint server.

Loads ClawDia's SkillLoader to discover all skills. Auto-generates:
  POST /hooks/:skill_name  — execute a skill
  GET  /hooks/             — list all hooks with manifests
  POST /hooks/batch        — batch execution

Usage:
    python saas_hooks_server.py          # port 8001
    uvicorn saas_hooks_server:app --reload
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

import asyncio
import re
import time
import traceback
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

logger = logging.getLogger(__name__)

# ── Path setup ─────────────────────────────────────────────────────

_BASE = Path(__file__).resolve().parent
_SRC = _BASE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_LEGACY_SRC = _BASE.parent / "ClawDia" / "src"
if str(_LEGACY_SRC) not in sys.path:
    sys.path.insert(0, str(_LEGACY_SRC))

# ── Skill loader ───────────────────────────────────────────────────

from skills.base import get_registered_skills, BaseSkill
from skills.loader import SkillLoader

_loader = SkillLoader(skills_dir=str(_SRC / "skills"))

_SKILL_CACHE: dict[str, BaseSkill] = {}
"""Skill cache: name -> instance. Populated lazily on first request."""


def _discover_skills() -> dict[str, BaseSkill]:
    if _SKILL_CACHE:
        return _SKILL_CACHE

    cache: dict[str, BaseSkill] = {}

    for s in _loader.discover_skills():
        if s.name:
            cache[s.name] = s

    for name, info in get_registered_skills().items():
        if name not in cache:
            try:
                inst = info["cls"]()
                if inst is not None:
                    cache[name] = inst
            except Exception:
                pass

    _SKILL_CACHE.update(cache)
    return _SKILL_CACHE


def _get_manifest(skill: BaseSkill) -> dict:
    return {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "version": skill.version,
        "author": skill.author,
        "tags": list(skill.tags) if hasattr(skill, "tags") else [],
        "required_libs": list(skill.required_libs) if hasattr(skill, "required_libs") else [],
        "input_schema": skill.input_schema if hasattr(skill, "input_schema") else {},
        "output_schema": skill.output_schema if hasattr(skill, "output_schema") else {},
        "instructions": (skill.instructions or "")[:500] if hasattr(skill, "instructions") else "",
    }


def _validate_params(params: dict, skill: BaseSkill) -> list[str]:
    errors = []
    schema = getattr(skill, "input_schema", {}) or {}
    props = schema.get("properties", {})
    required = schema.get("required", [])

    for key in required:
        if key not in params:
            errors.append(f"Missing required field: '{key}'")
    for key, val in params.items():
        if key in props:
            expected = props[key].get("type", "string")
            enum_vals = props[key].get("enum")
            if enum_vals and val not in enum_vals:
                errors.append(f"'{key}' must be one of {enum_vals}, got '{val}'")
            elif expected == "string" and not isinstance(val, str):
                errors.append(f"'{key}' expected string, got {type(val).__name__}")
            elif expected == "integer" and not isinstance(val, int):
                errors.append(f"'{key}' expected integer, got {type(val).__name__}")
            elif expected == "array" and not isinstance(val, (list, tuple)):
                errors.append(f"'{key}' expected array, got {type(val).__name__}")
    return errors


def _format_result(result: Any) -> dict:
    if isinstance(result, dict):
        return result
    if isinstance(result, (list, tuple)):
        return {"data": list(result)}
    if isinstance(result, (bool, int, float)):
        return {"data": result}
    s = str(result)
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except (json.JSONDecodeError, TypeError):
        return {"data": s}


# ── FastAPI app ────────────────────────────────────────────────────

app = FastAPI(
    title="SAAS Hooks API",
    version="1.0.0",
    description="256-skill auto-generated hooks server. POST /hooks/:skill_name to execute.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    skills = _discover_skills()
    logger.info("SAAS Hooks API ready — %d skills loaded", len(skills))
    for name in sorted(skills):
        logger.info("  POST /hooks/%-26s  %s", name, getattr(skills[name], "description", "")[:60])


@app.get("/")
def root():
    return {
        "service": "SAAS Hooks API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "This info",
            "GET /hooks": "List all hooks with manifests",
            "GET /hooks/{name}": "Get manifest for a specific hook",
            "POST /hooks/{name}": "Execute a hook (body is skill params JSON)",
            "POST /hooks/batch": "Execute multiple hooks in one request",
            "GET /hooks/ui": "HTML catalog of all hooks",
            "GET /hooks/ui/{name}": "HTML form for a specific hook",
        },
    }


@app.get("/hooks/")
def list_hooks():
    skills = _discover_skills()
    result = []
    for name in sorted(skills):
        skill = skills[name]
        result.append({
            "hook": name,
            "endpoint": f"POST /hooks/{name}",
            "manifest": _get_manifest(skill),
        })
    return {"hooks": result, "total": len(result)}


# ── UI: Auto-generated HTML forms ──────────────────────────────────


def _render_param_html(name: str, prop: dict, required: bool, value: Any = None) -> str:
    """Render a single form field based on its JSON Schema property."""
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
        rows.append(f'  <textarea name="{name}" id="{name}" class="widget code" rows="3">json array…</textarea>')
    elif ptype == "object":
        rows.append(f'  <textarea name="{name}" id="{name}" class="widget code" rows="4">json object…</textarea>')
    else:
        rows.append(f'  <input type="text" name="{name}" id="{name}" value="{val}" class="widget">')

    rows.append(f'</div>')
    return "\n".join(rows)


_UI_STYLES = """
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

_MENU_SCRIPT = """
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

_JSON_TREE_STYLES = """
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
/* JSON tree viewer */
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

_FORM_SCRIPT = r"""
<script>
var lastResult = null;
var formFields = {};

/* ── Dynamic form builder ────────────────────────────────── */
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
      /* ── enum → dropdown ── */
      var opts = p.enum.map(function(v) {
        var sel = (v === p.default) ? ' selected' : '';
        return '<option value="' + escapeAttr(v) + '"' + sel + '>' + escapeHtml(v) + '</option>';
      }).join('');
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<select class="widget" data-key="' + escapeAttr(key) + '">' + opts + '</select></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('select'), type: 'string'};
    } else if (p.type === 'boolean') {
      /* ── boolean → toggle ── */
      var chk = p.default ? ' checked' : '';
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label class="toggle-label">' +
        '<label class="toggle"><input type="checkbox" data-key="' + escapeAttr(key) + '"' + chk + '><span class="toggle-slider"></span></label>' +
        '<span>' + escapeHtml(label) + req + '</span>' + desc + '</label></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('input'), type: 'boolean'};
    } else if (p.type === 'integer' || p.type === 'number') {
      /* ── number → input ── */
      var min = p.minimum !== undefined ? ' min="' + p.minimum + '"' : '';
      var max = p.maximum !== undefined ? ' max="' + p.maximum + '"' : '';
      var def = p.default !== undefined ? ' value="' + p.default + '"' : '';
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<input type="number" class="widget" data-key="' + escapeAttr(key) + '"' + min + max + def + '></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('input'), type: 'number'};
    } else if (p.type === 'object') {
      /* ── object → collapsible panel ── */
      var id = 'obj-' + key.replace(/[^a-z0-9]/gi, '-');
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><div class="obj-header" onclick="toggleObj(\'' + escapeAttr(id) + '\')">' +
        '<span class="obj-arrow">&#9654;</span> <strong>' + escapeHtml(label) + '</strong>' + req + '</div>' + desc +
        '<div id="' + escapeAttr(id) + '" class="obj-body"></div></div>');
      var body = document.getElementById(id);
      buildForm(p, body, key + '.');
    } else if (p.type === 'array') {
      /* ── array → simple list ── */
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<textarea class="widget code" data-key="' + escapeAttr(key) + '" rows="2" placeholder="JSON array, e.g. [&quot;a&quot;,&quot;b&quot;]" spellcheck="false"></textarea></div>');
      formFields[key] = {el: container.lastElementChild.querySelector('textarea'), type: 'array'};
    } else {
      /* ── string → input or textarea ── */
      var isLong = (p.description && p.description.length > 60) || (label === 'text');
      var tag = isLong ? 'textarea' : 'input';
      var typeAttr = isLong ? '' : ' type="text"';
      var rows = isLong ? ' rows="4"' : '';
      var def = p.default !== undefined ? (isLong ? '>' + escapeHtml(String(p.default)) : ' value="' + escapeAttr(String(p.default)) + '"') : (isLong ? '>' : '');
      var close = isLong ? '</textarea>' : '';
      container.insertAdjacentHTML('beforeend',
        '<div class="fd"><label>' + escapeHtml(label) + req + '</label>' + desc +
        '<' + tag + typeAttr + ' class="widget' + (isLong ? ' code' : '') + '" data-key="' + escapeAttr(key) + '"' + rows + ' placeholder="' + escapeAttr(label) + '" spellcheck="false"' + def + close + '></div>');
      formFields[key] = {el: container.lastElementChild.querySelector(tag), type: 'string'};
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

/* ── Collect form data ───────────────────────────────────── */
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
  /* flatten dotted keys into nested object */
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

/* ── JSON tree viewer ────────────────────────────────────── */
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

/* ── Submit form ─────────────────────────────────────────── */
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
      /* result div still gets raw JSON for copy-paste */
      resultDiv.innerHTML = '<pre>' + escapeHtml(text) + '</pre>';
      /* but main display is the tree view */
      if (json) {
        treeDiv.style.display = 'block';
        renderJSONTree(json, treeDiv);
        lastResult = json;
        if (lastResult && lastResult.result && lastResult.result.html) {
          if (prevBtn) { prevBtn.disabled = false; prevBtn.textContent = '\u25B6 Preview'; }
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

/* ── Init: load schema, build form ───────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  var skillName = document.getElementById('hook-form').dataset.skill;
  fetch('/hooks/' + skillName).then(function(r) { return r.json(); }).then(function(man) {
    var schema = man.manifest ? man.manifest.input_schema : (man.input_schema || {});
    buildForm(schema, document.getElementById('form-fields'));
  });
});
</script>
"""


def _render_menu_page(skills: dict) -> str:
    """Full HTML page: catalog of all hooks grouped by category."""
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
<title>SAAS Hooks — Menu</title>{_UI_STYLES}{_MENU_SCRIPT}
</head><body>
  <h1>SAAS Hooks API</h1>
  <p class="subtitle">{len(skills)} endpoints — pick one to execute</p>
  <div class="cat-group">
    <div class="cat-title">✦ Special</div>
    <a href="/hooks/ui/forge" class="hook-link" style="border-color:#238636">
      <div><span class="name" style="color:#3fb950">forge</span><span class="badge" style="background:#1a3a2a;color:#3fb950">multi-agent</span></div>
      <div class="desc">Spawn N agents with skills — they build together in real time via SSE</div>
    </a>
  </div>
  <input type="text" id="search" class="search" placeholder="Filter hooks…" oninput="filterHooks()">
  {hooks_rows}
</body></html>"""


def _render_form_page(skill_name: str, skill: object) -> str:
    """Full HTML page: auto-generated form for a single hook."""
    schema = getattr(skill, "input_schema", {}) or {}
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    desc = getattr(skill, "description", "")
    tags = getattr(skill, "tags", [])
    badges = "".join(f'<span class="badge">{t}</span>' for t in (tags or [])[:4])

    fields_html = _render_param_html("action", {"type": "string", "enum": ["_info"], "default": "_info"}, False)  # placeholder

    if props:
        fields_html = "\n".join(
            _render_param_html(name, prop, name in required)
            for name, prop in props.items()
        )
    else:
        fields_html = '<p style="color:#8b949e;font-size:.9rem">This hook takes no parameters. Submit to execute.</p>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{skill_name} — SAAS Hook</title>{_UI_STYLES}{_JSON_TREE_STYLES}{_FORM_SCRIPT}
</head><body>
  <a href="/hooks/ui" class="back">← Back to menu</a>
  <h1>{skill_name}</h1>
  <p class="subtitle">{desc}{badges}</p>
  <form id="hook-form" data-skill="{skill_name}" onsubmit="event.preventDefault();submitForm('{skill_name}')">
    <div id="form-fields"><p style="color:#8b949e;font-size:.9rem">Loading form…</p></div>
    <div style="display:flex;gap:0.5rem;align-items:center;margin-top:1rem">
      <button type="submit" class="submit" id="submit-btn">Execute</button>
      <button type="button" class="submit" id="preview-btn" style="background:#1e2a3a;border:1px solid #30363d;color:#e6edf3" disabled onclick="previewResult()">&#9654; Preview</button>
    </div>
  </form>
  <div id="error" class="error" style="display:none"></div>
  <div id="json-tree-view" class="result" style="display:none;margin-top:1rem"></div>
  <div id="result" class="result" style="margin-top:1rem"></div>
  <div id="preview-container" style="display:none;margin-top:1rem"></div>
</body></html>"""


@app.get("/hooks/ui/portal")
async def ui_portal(request: Request):
    return HTMLResponse(Path(__file__).parent.joinpath("saas_portal.html").read_text(encoding="utf-8"))

@app.get("/hooks/ui")
def ui_menu(request: Request):
    skills = _discover_skills()
    return HTMLResponse(_render_menu_page(skills))


# IMPORTANT: Specific paths must be registered before /{skill_name}
# to avoid FastAPI catching them as parameter values. Forge UI is
# defined inline here; _FORGE_SCRIPT and _FORGE_UI_STYLES are
# module-level globals defined later — safe because this function
# body runs at request time, not module import time.
@app.get("/hooks/ui/forge")
async def ui_forge(request: Request):
    skills = _discover_skills()
    skill_options = "".join(f'<option value="{n}">{n}</option>' for n in sorted(skills))
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forge — Multi-Agent Studio</title>{_UI_STYLES}{_FORGE_UI_STYLES}{_FORGE_SCRIPT}
</head><body>
  <a href="/hooks/ui" class="back">← Back to menu</a>
  <h1>Forge Studio</h1>
  <p class="subtitle">Spawn agents, give them skills, watch them build together. Every call tests our SAAS.</p>

  <form id="forge-form" onsubmit="event.preventDefault();startForge()">
    <div class="field">
      <label for="seed">Seed / Scenario</label>
      <input type="text" id="seed" class="widget" value="two lovers in a recursive garden" placeholder="Describe the scenario…">
    </div>
    <div class="field">
      <label for="iterations">Iterations (rounds)</label>
      <input type="number" id="iterations" class="widget" value="3" min="1" max="20" style="max-width:100px">
    </div>
    <h2>Agents</h2>
    <div id="agents-container">
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Lyricist">
        <input class="agent-role widget" placeholder="Role" value="lyricist">
        <input class="agent-skills widget" placeholder="comic_compiler,vibe_affirmations" value="vibe_affirmations">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">×</button>
      </div>
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Composer">
        <input class="agent-role widget" placeholder="Role" value="composer">
        <input class="agent-skills widget" placeholder="audio_analyze,audio_info" value="audio_info">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">×</button>
      </div>
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Mike">
        <input class="agent-role widget" placeholder="Role" value="composer">
        <input class="agent-skills widget" placeholder="midi_render" value="midi_render">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">×</button>
      </div>
    </div>
    <button type="button" onclick="addAgent()" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:.4rem 1rem;cursor:pointer;margin-bottom:1rem">+ Add Agent</button>
    <button type="submit" class="submit" id="forge-btn">Forge</button>
  </form>

  <div id="error" class="error" style="display:none"></div>
  <div id="forge-status" style="color:#8b949e;font-size:.85rem;margin-top:.5rem"></div>

  <div class="split-panel">
    <div>
      <h2>Agent Activity</h2>
      <div id="forge-output">Waiting for forge…</div>
    </div>
    <div>
      <h2>Live Preview</h2>
      <div id="live-preview"><p style="color:#8b949e">HTML will appear here as agents collaborate…</p></div>
    </div>
  </div>
</body></html>""")


@app.get("/hooks/ui/midi")
async def ui_midi_composer(request: Request):
    return HTMLResponse(_MIDI_UI_HTML.replace("{_UI_STYLES}", _UI_STYLES).replace("{_MIDI_UI_STYLES}", _MIDI_UI_STYLES).replace("{_MIDI_SCRIPT}", _MIDI_SCRIPT))


@app.get("/hooks/ui/forge-entanglement")
async def forge_entanglement_ui():
    import pathlib
    fpath = pathlib.Path(__file__).parent / "forge_entanglement.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>forge_entanglement.html not found</h1>", status_code=404)


@app.get("/hooks/ui/{skill_name}")
def ui_form(skill_name: str, request: Request):
    skills = _discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    return HTMLResponse(_render_form_page(skill_name, skill))


# IMPORTANT: /batch MUST be registered before /{skill_name} to avoid
# FastAPI matching "batch" as a skill_name parameter.
@app.post("/hooks/batch")
async def execute_batch(request: Request):
    skills = _discover_skills()
    try:
        raw = await request.body()
        data = json.loads(raw) if raw else {"calls": []}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Invalid JSON body")

    calls = data.get("calls", []) if isinstance(data, dict) else []
    if not isinstance(calls, list):
        raise HTTPException(422, "'calls' must be an array")

    results = []
    for i, call in enumerate(calls):
        hook_name = call.get("hook", "") if isinstance(call, dict) else ""
        params = call.get("params", {}) if isinstance(call, dict) else {}
        skill = skills.get(hook_name)
        if not skill:
            results.append({"index": i, "hook": hook_name, "status": "error", "error": "Hook not found"})
            continue
        errors = _validate_params(params, skill)
        if errors:
            results.append({"index": i, "hook": hook_name, "status": "validation_error", "errors": errors})
            continue
        try:
            if hasattr(skill, "execute"):
                result = skill.execute(**params)
            else:
                result = skill.run(payload=params)
            results.append({"index": i, "hook": hook_name, "status": "ok", "result": _format_result(result)})
        except Exception as e:
            results.append({"index": i, "hook": hook_name, "status": "error", "error": str(e)})

    return {
        "results": results,
        "total": len(calls),
        "succeeded": sum(1 for r in results if r["status"] == "ok"),
    }


# ── MIDI / Sheet Music Render ─────────────────────────────────────

_MIDI_UI_STYLES = """
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

_MIDI_SCRIPT = """
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
  chipDiv.innerHTML = notes.map(function(n) { return '<span class=\"note-chip\">' + n + '</span>'; }).join('');
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


_MIDI_UI_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mike — MIDI Composer</title>""" + "{_UI_STYLES}{_MIDI_UI_STYLES}{_MIDI_SCRIPT}" + r"""
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


@app.post("/hooks/midi/render")
async def midi_render_nested(request: Request):
    """POST /hooks/midi/render — nested alias for midi_render skill."""
    skills = _discover_skills()
    skill = skills.get("midi_render")
    if not skill:
        raise HTTPException(404, "midi_render skill not found")
    try:
        raw = await request.body()
        params = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        params = {}
    errors = _validate_params(params, skill)
    if errors:
        raise HTTPException(422, {"errors": errors})
    try:
        result = skill.execute(**params) if hasattr(skill, "execute") else skill.run(payload=params)
        return _format_result(result)
    except Exception as e:
        raise HTTPException(500, {"error": str(e)})


# ── Forge: Multi-Agent Collaboration Engine ────────────────────────


class ForgeContext:
    """Shared state that agents build together."""

    def __init__(self, seed: str, output_format: str = "html"):
        self.seed = seed
        self.output_format = output_format
        self.artifact = "" if output_format == "html" else ""
        self.artifacts: list[dict] = []
        self.round = 0
        self.log: list[dict] = []
        self._lock = asyncio.Lock()

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "output_format": self.output_format,
            "artifact": self.artifact,
            "artifacts": self.artifacts,
            "round": self.round,
            "log_count": len(self.log),
        }


def _tpl(s: str, ctx: ForgeContext, agent_name: str = "") -> str:
    """Template substitution: {seed}, {context}, {agent}, {round}, {ts}."""
    s = s.replace("{seed}", ctx.seed)
    s = s.replace("{context}", ctx.artifact)
    s = s.replace("{agent}", agent_name)
    s = s.replace("{round}", str(ctx.round))
    s = s.replace("{ts}", str(time.time()))
    return s


async def _run_forge(
    agents: list[dict],
    iterations: int,
    seed: str,
    output_format: str,
    skills: dict,
):
    """Async generator that yields SSE events for the forge session."""
    ctx = ForgeContext(seed, output_format)
    start_ts = time.time()
    session_id = uuid.uuid4().hex[:12]

    yield f"event: session_start\ndata: {json.dumps({'session_id': session_id, 'agents': len(agents), 'iterations': iterations})}\n\n"

    # Initialize HTML if needed
    if output_format == "html":
        ctx.artifact = "<!DOCTYPE html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\">\n"
        ctx.artifact += f"<title>Forge: {seed[:40]}</title>\n"
        ctx.artifact += "<style>body{font-family:system-ui;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.6}</style>\n"
        ctx.artifact += "</head>\n<body>\n"
        ctx.artifact += f"<h1>Forge: {seed[:60]}</h1>\n<div class=\"forge-content\">\n"

    for iteration in range(1, iterations + 1):
        ctx.round = iteration
        yield f"event: round_start\ndata: {json.dumps({'round': iteration, 'total': iterations})}\n\n"

        for agent in agents:
            agent_name = agent.get("name", "agent")
            agent_role = agent.get("role", "")
            agent_skills = agent.get("skills", [])

            yield f"event: agent_start\ndata: {json.dumps({'agent': agent_name, 'role': agent_role, 'round': iteration})}\n\n"

            if not agent_skills:
                yield f"event: agent_skip\ndata: {json.dumps({'agent': agent_name, 'reason': 'no skills configured'})}\n\n"
                continue

            for skill_binding in agent_skills:
                skill_name = skill_binding.get("skill", "")
                param_tpls = skill_binding.get("params", {})

                skill = skills.get(skill_name)
                if not skill:
                    yield f"event: skill_error\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'error': 'Skill not found'})}\n\n"
                    continue

                # Resolve template params
                resolved = {}
                for k, v in param_tpls.items():
                    if isinstance(v, str):
                        resolved[k] = _tpl(v, ctx, agent_name)
                    else:
                        resolved[k] = v

                yield f"event: skill_call\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'params': resolved})}\n\n"

                try:
                    result = skill.execute(**resolved) if hasattr(skill, "execute") else skill.run(payload=resolved)

                    # Determine if this was called via await
                    if asyncio.iscoroutine(result):
                        result = await result

                    formatted = _format_result(result)

                    entry = {
                        "agent": agent_name,
                        "skill": skill_name,
                        "params": resolved,
                        "result": formatted,
                        "round": iteration,
                        "timestamp": time.time(),
                    }
                    ctx.log.append(entry)
                    ctx.artifacts.append(entry)

                    # Accumulate into shared artifact
                    result_text = json.dumps(formatted, indent=2)
                    if output_format == "html":
                        ctx.artifact += f"<div class=\"forge-entry\">\n"
                        ctx.artifact += f"  <h3>{agent_name} ({skill_name})</h3>\n"
                        ctx.artifact += f"  <pre>{result_text}</pre>\n"
                        ctx.artifact += f"</div>\n"
                    else:
                        ctx.artifact += f"\n--- {agent_name}/{skill_name} ---\n{result_text}\n"

                    yield f"event: skill_result\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'result': formatted, 'round': iteration})}\n\n"

                except Exception as e:
                    err_msg = f"{type(e).__name__}: {e}"
                    yield f"event: skill_error\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'error': err_msg})}\n\n"

            yield f"event: agent_done\ndata: {json.dumps({'agent': agent_name, 'round': iteration})}\n\n"

        # Emit progress with current artifact
        yield f"event: progress\ndata: {json.dumps({'round': iteration, 'total': iterations, 'html': ctx.artifact if output_format == 'html' else '', 'artifact_length': len(ctx.artifact)})}\n\n"

    # Finalize artifact
    if output_format == "html":
        ctx.artifact += "</div>\n<footer><p>Generated by SAAS Forge in "
        ctx.artifact += f"{len(ctx.log)} skill calls across {iterations} rounds</p></footer>\n"
        ctx.artifact += "</body>\n</html>"

    elapsed = time.time() - start_ts
    complete_data = json.dumps({
        "session_id": session_id,
        "rounds": iterations,
        "skill_calls": len(ctx.log),
        "elapsed_seconds": round(elapsed, 2),
        "output_format": output_format,
        "artifact": ctx.artifact,
        "artifacts": ctx.artifacts,
    })
    yield f"event: complete\ndata: {complete_data}\n\n"


@app.post("/hooks/forge")
async def forge_endpoint(request: Request):
    """Multi-agent collaboration endpoint with SSE streaming.

    Agents with different roles build something together by calling
    existing SAAS hooks. Every skill call is a live integration test.
    The user watches the HTML populate in real time via SSE.
    """
    try:
        raw = await request.body()
        body = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Invalid JSON body")

    agents = body.get("agents", [])
    if not agents or not isinstance(agents, list):
        raise HTTPException(422, "'agents' must be a non-empty array")

    iterations = body.get("iterations", 3)
    if not isinstance(iterations, int) or iterations < 1:
        raise HTTPException(422, "'iterations' must be a positive integer")

    seed = body.get("seed", "forge session")
    output_format = body.get("output_format", "html")
    skills = _discover_skills()

    # Validate skills exist
    for agent in agents:
        for sb in agent.get("skills", []):
            sname = sb.get("skill", "")
            if sname and sname not in skills:
                raise HTTPException(422, f"Skill '{sname}' not found (agent '{agent.get('name', '?')}')")

    return StreamingResponse(
        _run_forge(agents, iterations, seed, output_format, skills),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Forge UI page (auto-generated form for the forge endpoint) ────

_FORGE_SCRIPT = """
<script>
async function startForge() {
  const btn = document.getElementById('forge-btn');
  const output = document.getElementById('forge-output');
  const status = document.getElementById('forge-status');
  const errorDiv = document.getElementById('error');
  btn.disabled = true; btn.textContent = 'Forging…';
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

  const evtSource = new EventSource('/hooks/forge?' + new URLSearchParams({
    body: JSON.stringify({agents, iterations, seed, output_format: 'html'})
  }));
  // Actually, we need POST with SSE. Use fetch + reader instead.
  evtSource.close();

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
        } else if (line.startsWith('event: ')) {
          // track events
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
    + ' <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">×</button>';
  container.appendChild(div);
}
</script>
"""

_FORGE_UI_STYLES = """
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


@app.get("/hooks/{skill_name}")
def get_hook(skill_name: str):
    skills = _discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    return {
        "hook": skill_name,
        "endpoint": f"POST /hooks/{skill_name}",
        "manifest": _get_manifest(skill),
    }


@app.post("/hooks/{skill_name}")
async def execute_hook(skill_name: str, request: Request):
    skills = _discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")

    try:
        raw = await request.body()
        params = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        params = {}

    errors = _validate_params(params, skill)
    if errors:
        raise HTTPException(422, {"errors": errors, "hook": skill_name})

    try:
        if hasattr(skill, "execute"):
            result = skill.execute(**params)
        elif hasattr(skill, "run"):
            result = skill.run(payload=params)
        else:
            raise HTTPException(500, f"Skill '{skill_name}' has no execute or run method")
        return _format_result(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Hook '%s' failed", skill_name)
        raise HTTPException(500, {"error": str(e), "hook": skill_name})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("saas_hooks_server:app", host="127.0.0.1", port=8001, reload=False)
