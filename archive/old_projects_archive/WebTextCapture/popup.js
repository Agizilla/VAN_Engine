const REQUIRED_ASSETS = [
  { path: 'vendor/tesseract/tesseract.min.js', minBytes: 10000 },
  { path: 'vendor/tesseract/worker.min.js', minBytes: 10000 },
  { path: 'vendor/tesseract-core/tesseract-core.wasm.js', minBytes: 1000 },
  { path: 'vendor/tesseract-core/tesseract-core.wasm', minBytes: 100000 },
  { path: 'vendor/tessdata/eng.traineddata.gz', minBytes: 20000 }
];

const activateBtn = document.getElementById('activate');
const validateBtn = document.getElementById('validateAssets');
const statusEl = document.getElementById('status');
const assetStatusEl = document.getElementById('assetStatus');
const assetListEl = document.getElementById('assetList');

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB'];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(1)} ${units[index]}`;
}

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

async function validateAssets() {
  assetListEl.innerHTML = '';
  assetStatusEl.textContent = 'Checking local OCR assets...';
  assetStatusEl.className = 'muted';

  const results = [];
  for (const asset of REQUIRED_ASSETS) {
    const size = await getAssetSize(asset.path);
    const htmlStub = asset.path.endsWith('.js') ? await assetLooksLikeHtml(asset.path) : false;
    const ok = size >= asset.minBytes && !htmlStub;
    results.push({ ...asset, size, ok, htmlStub });
  }

  assetListEl.innerHTML = results.map(result => `
    <li class="${result.ok ? 'ok' : 'bad'}">
      ${result.path} - ${formatBytes(result.size)} ${result.ok ? 'OK' : result.htmlStub ? '(downloaded HTML page, not raw file)' : `(expected >= ${formatBytes(result.minBytes)})`}
    </li>
  `).join('');

  const allGood = results.every(result => result.ok);
  assetStatusEl.textContent = allGood
    ? 'Local OCR bundle looks complete.'
    : 'OCR bundle is incomplete or still using placeholders.';
  assetStatusEl.className = allGood ? 'ok' : 'bad';
}

activateBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const sendStartMessage = () => {
    chrome.tabs.sendMessage(tab.id, { action: 'startSelection' }, () => {
      if (chrome.runtime.lastError) {
        statusEl.textContent = 'Error: ' + chrome.runtime.lastError.message;
      } else {
        statusEl.textContent = 'Selection mode activated. Draw rectangle on page.';
        window.close();
      }
    });
  };

  chrome.tabs.sendMessage(tab.id, { action: 'ping' }, () => {
    if (chrome.runtime.lastError) {
      chrome.scripting.insertCSS({
        target: { tabId: tab.id },
        files: ['styles.css']
      }, () => {
        if (chrome.runtime.lastError) {
          statusEl.textContent = 'Failed to inject CSS: ' + chrome.runtime.lastError.message;
          return;
        }

        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }, () => {
          if (chrome.runtime.lastError) {
            statusEl.textContent = 'Failed to inject content script: ' + chrome.runtime.lastError.message;
          } else {
            setTimeout(sendStartMessage, 100);
          }
        });
      });
    } else {
      sendStartMessage();
    }
  });
});

validateBtn.addEventListener('click', () => {
  validateAssets().catch(err => {
    assetStatusEl.textContent = `Asset validation failed: ${err.message}`;
    assetStatusEl.className = 'bad';
  });
});
