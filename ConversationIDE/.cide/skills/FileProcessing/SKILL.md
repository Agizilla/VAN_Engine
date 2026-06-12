---
name: FileProcessing
description: Archive, compress, bundle files in tar/gzip/zip/rar/pyp formats. USE WHEN archive, compress, bundle, zip, tar, gzip, rar, pyp, package files, file processing, batch compress.
---

# FileProcessing

Multi-format file archiving and compression. Supports standard formats (tar, gzip, zip, rar) and the proprietary `.pyp` skill-container format.

## Formats

| Format | Extension | Tool | Notes |
|--------|-----------|------|-------|
| Tar | `.tar` | `tar` (built-in) | No compression, preserves permissions |
| Gzip | `.tar.gz` / `.gz` | `tar -czf` / `gzip` | Good for text-heavy projects |
| Zip | `.zip` | `python -m zipfile` / `Compress-Archive` | Universal, best for mixed content |
| Rar | `.rar` | Requires `unrar` / `rar` CLI | Proprietary, high compression |
| Pyp | `.pyp` | `core/pyp_creator.py` | Structured skill container with typed sections |

## Workflow Routing

| Trigger | Workflow |
|---------|----------|
| "bundle", "archive", "compress files", "make a zip" | `Workflows/Bundle.md` |
| "pyp", "skill container", "package as pyp" | `Workflows/Bundle.md` (format=pyp) |

## Quick Reference

- **Default format:** zip (widest compatibility)
- **Pyp format** — first runs `pyp_creator.py` to build the structured container, then optionally compresses
- **All formats** output to the same directory as the source or a specified output path
- **Encryption:** Only zip supports password via `python -m zipfile -e`; pyp can wrap in encrypted zip
