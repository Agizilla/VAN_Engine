# Local OCR Assets

This extension is designed to run with local Tesseract assets only.

Preferred layout:

```text
vendor/
  tesseract/
    tesseract.min.js
    worker.min.js
  tesseract-core/
    tesseract-core.wasm.js
    tesseract-core.wasm
  tessdata/
    eng.traineddata.gz
```

Alternative legacy flat layout supported by the code:

```text
tesseract.min.js
worker.min.js
tesseract-core.wasm.js
tesseract-core.wasm
eng.traineddata.gz
```

Notes:
- Use real files from a matching Tesseract.js distribution.
- Do not leave placeholder files in place; the extension validates minimum file sizes and will reject incomplete assets.
- The preferred `vendor/` layout keeps OCR dependencies isolated from the extension source files.
