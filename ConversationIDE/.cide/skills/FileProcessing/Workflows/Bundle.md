# Bundle — Multi-Format Archiving Workflow

## Goal
Bundle a file, folder, or project into a compressed archive in the requested format.

## Input
- **source** — file or folder path to archive
- **format** — `tar`, `gzip`, `zip`, `rar`, or `pyp` (default: `zip`)
- **output** — optional output path (default: same dir as source)
- **name** — optional archive name (default: source basename)
- **password** — optional encryption password (zip-only)

## Workflow Steps

### 1. Validate Source
Check source exists. If folder, decide whether to archive the folder itself or its contents.

### 2. Resolve Format & Tool

| Format | Command |
|--------|---------|
| **tar** | `tar -cf "{output}.tar" -C "{parent}" "{basename}"` |
| **gzip** | `tar -czf "{output}.tar.gz" -C "{parent}" "{basename}"` |
| **zip** | `python -m zipfile -c "{output}.zip" "{source}"` _(single file)_ or `Compress-Archive` _(PowerShell, folder)_ |
| **rar** | `rar a -ep1 "{output}.rar" "{source}"` (requires rar CLI in PATH) |
| **pyp** | `python core/pyp_creator.py "{source}" --name "{name}"` then optionally wrap in zip |

### 3. Pyp Format — Extended Process

If format is `pyp`:

1. Run `python core/pyp_creator.py "{abs_source}" --name "{name}"`
   - This inlines `.md/.html/.txt/.py` into the `.pyp` JSON
   - Moves binaries to `ARTIFACTS/`
   - Creates `INPUTS/` and `OTHER/` dirs
2. If `password` is set, wrap the `.pyp` + `ARTIFACTS/` + `INPUTS/` + `OTHER/` into an encrypted zip:
   `python -c "import zipfile; z=zipfile.ZipFile('{output}.pyp.zip','w',zipfile.ZIP_DEFLATED); z.setpassword('{password}'); z.write(...)"`

### 4. Verify Output
Check the output file exists and report its size.

## Examples

**Bundle a project folder as zip:**
```
→ "zip up the voice-cloner project"
→ Source: Services/ClawdiaBridge/voice_cloner.py
→ Format: zip
→ Run: python -m zipfile -c voice_cloner.zip voice_cloner.py
```

**Bundle as pyp skill container:**
```
→ "package my project as a pyp"
→ Source: projects/my-tool/
→ Format: pyp
→ Run: python core/pyp_creator.py projects/my-tool/ --name my-tool
→ Result: my-tool.pyp + ARTIFACTS/ + INPUTS/ + OTHER/
```
