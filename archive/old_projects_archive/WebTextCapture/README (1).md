# Screen OCR Extractor

A Chrome extension that lets you drag a rectangle over any webpage content, capture that area, and extract text via OCR. The extracted text is automatically copied to your clipboard.

## Installation
1. Clone this repository.
2. Open Chrome and go to `chrome://extensions`.
3. Enable "Developer mode" (toggle in top right).
4. Install real local Tesseract assets before loading the extension.
5. Preferred asset layout:

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

6. Click "Load unpacked" and select the extension folder.

## Usage
1. Click the extension icon in the toolbar.
2. Click "Validate Local OCR Assets" to confirm the vendor OCR bundle is installed correctly.
3. Click "Activate Screen Selection".
4. Drag a rectangle over the area containing text you want to capture.
5. The text will be copied to your clipboard.

## Dependencies
- Local Tesseract.js distribution packaged with the extension

## Notes
- The extension uses a content script to overlay selection UI.
- The background worker captures the visible tab, then the offscreen document crops and OCRs the selected area.
- OCR now uses the `vendor/` asset layout only.
- Use the popup validator before testing OCR so missing files are obvious immediately.
- For best results, ensure the captured area contains clear, printed text.
