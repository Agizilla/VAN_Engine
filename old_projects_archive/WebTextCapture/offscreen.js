let tessWorker = null;
let workerReady = false;
let initError = null;

const OCR_ASSETS = {
  scriptPath: 'vendor/tesseract/tesseract.min.js',
  workerPath: 'vendor/tesseract/worker.min.js',
  corePath: 'vendor/tesseract-core/tesseract-core.wasm.js',
  langPath: 'vendor/tessdata',
  required: [
    { path: 'vendor/tesseract/tesseract.min.js', minBytes: 10000 },
    { path: 'vendor/tesseract/worker.min.js', minBytes: 10000 },
    { path: 'vendor/tesseract-core/tesseract-core.wasm.js', minBytes: 1000 },
    { path: 'vendor/tesseract-core/tesseract-core.wasm', minBytes: 100000 },
    { path: 'vendor/tessdata/eng.traineddata.gz', minBytes: 20000 }
  ]
};

async function getAssetSize(path) {
  const response = await fetch(chrome.runtime.getURL(path));
  if (!response.ok) return 0;
  const blob = await response.blob();
  return blob.size;
}

async function assetLooksLikeHtml(path) {
  const response = await fetch(chrome.runtime.getURL(path));
  if (!response.ok) return false;
  const text = await response.text();
  return /^\s*<!DOCTYPE html>/i.test(text) || /^\s*<html/i.test(text);
}

async function ensureOcrAssets() {
  for (const asset of OCR_ASSETS.required) {
    const size = await getAssetSize(asset.path);
    const htmlStub = asset.path.endsWith('.js') ? await assetLooksLikeHtml(asset.path) : false;
    if (size < asset.minBytes) {
      throw new Error(
        `Missing or placeholder OCR asset: ${asset.path}. Install the vendor OCR bundle before using this extension.`
      );
    }
    if (htmlStub) {
      throw new Error(
        `Invalid OCR asset: ${asset.path} is an HTML page, not a raw file. Download the raw asset URL and replace it.`
      );
    }
  }
}

async function loadLocalScript(path) {
  await new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL(path);
    script.async = false;
    script.onload = resolve;
    script.onerror = () => reject(new Error(`Failed to load script: ${path}`));
    document.head.appendChild(script);
  });
}

function getTesseractApi() {
  const candidates = [
    globalThis?.Tesseract,
    typeof self !== 'undefined' ? self.Tesseract : undefined,
    typeof window !== 'undefined' ? window.Tesseract : undefined
  ];

  return candidates.find(candidate => candidate && typeof candidate.createWorker === 'function') || null;
}

function describeTesseractBindings() {
  return [
    `globalThis.Tesseract=${typeof globalThis?.Tesseract}`,
    `self.Tesseract=${typeof (typeof self !== 'undefined' ? self.Tesseract : undefined)}`,
    `window.Tesseract=${typeof (typeof window !== 'undefined' ? window.Tesseract : undefined)}`
  ].join(', ');
}

async function initTesseract() {
  if (workerReady && tessWorker) return tessWorker;
  if (initError) throw initError;

  try {
    await ensureOcrAssets();
    await loadLocalScript(OCR_ASSETS.scriptPath);
    await new Promise(resolve => setTimeout(resolve, 0));

    const tesseractApi = getTesseractApi();
    if (!tesseractApi) {
      throw new Error(
        `Local tesseract.min.js did not expose Tesseract.createWorker. ${describeTesseractBindings()}`
      );
    }

    tessWorker = await tesseractApi.createWorker('eng', 1, {
      workerPath: chrome.runtime.getURL(OCR_ASSETS.workerPath),
      corePath: chrome.runtime.getURL(OCR_ASSETS.corePath),
      langPath: chrome.runtime.getURL(OCR_ASSETS.langPath),
      workerBlobURL: false
    });
    workerReady = true;
    return tessWorker;
  } catch (err) {
    initError = err;
    throw err;
  }
}

async function cropImage(imageDataUrl, crop) {
  const image = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Failed to decode captured image.'));
    img.src = imageDataUrl;
  });

  if (!crop || !crop.width || !crop.height) {
    return imageDataUrl;
  }

  const scale = crop.devicePixelRatio || 1;
  const sx = Math.max(0, Math.round(crop.x * scale));
  const sy = Math.max(0, Math.round(crop.y * scale));
  const sw = Math.max(1, Math.round(crop.width * scale));
  const sh = Math.max(1, Math.round(crop.height * scale));

  const canvas = new OffscreenCanvas(sw, sh);
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(image, sx, sy, sw, sh, 0, 0, sw, sh);
  const blob = await canvas.convertToBlob({ type: 'image/png' });

  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Failed to encode cropped image.'));
    reader.readAsDataURL(blob);
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.target === 'offscreen' && request.action === 'ocr') {
    Promise.resolve()
      .then(async () => {
        const croppedImage = await cropImage(request.imageData, request.crop);
        const worker = await initTesseract();
        const result = await worker.recognize(croppedImage);
        const text = result?.data?.text?.trim() || '';

        chrome.runtime.sendMessage({
          target: 'background',
          action: 'ocrResult',
          requestId: request.requestId,
          text
        });
      })
      .catch(err => {
        chrome.runtime.sendMessage({
          target: 'background',
          action: 'ocrResult',
          requestId: request.requestId,
          error: err.message || String(err)
        });
      });

    return true;
  }
});
