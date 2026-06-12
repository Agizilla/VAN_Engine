---
name: PRDSkill
description: Master PRD Catalog Skill — scan, parse, categorize, and produce professional PRD catalogs across project directories. USE WHEN PRD, product requirements document, catalog, scan PRDs, view PRD, timeline, artifacts, specification, requirements doc.
how_to: Invoke via IPC `prd:*` or directly from Python `from tools.master_skills.prdSkill import PRDSkill`
version: 1.0.0
countPublicMethods: 14
countLineNumbers: 250
---

# PRDSkill

Master PRD catalog skill. Scan, parse, categorize, and visualize PRDs with artifact tracking and timeline.

## Capabilities

| Capability | Description |
|---|---|
| Scan | Recursively find all PRD files across project directories |
| Parse | Extract YAML frontmatter, sections, artifacts |
| Categorize | Group by effort, phase, status |
| Timeline | Generate chronological PRD timeline data |
| Search | Full-text search across PRDs |
| Artifacts | Extract and track files produced/updated by each PRD |
| Orphan Detection | Find PRDs >90 days old not in complete state |
| HTML Render | Render a PRD to styled HTML |
| Export | Export catalog as JSON |
| Viewer | Open professional 3-panel PRD catalog viewer |

## Usage

```python
from tools.master_skills.prdSkill import PRDSkill

skill = PRDSkill()
prds = skill.scan()
catalog = skill.get_catalog(prds)
timeline = skill.get_timeline(prds)
artifacts = skill.get_artifacts_for("prd-master-skills")
```

## IPC Channels

- `prd:scan` — Scan for all PRDs, return catalog
- `prd:get` — Get a single PRD by slug
- `prd:search` — Search PRDs by keyword
- `prd:viewer-path` — Get path to PRD viewer HTML

## Viewer

Open `prd_viewer.html` in any browser for the professional 3-panel PRD catalog viewer with:
- Left: PRD list (searchable, sortable)
- Center: Full rendered PRD content
- Right: Artifacts produced/updated
- Bottom: Timeline scroller when multiple PRDs loaded
