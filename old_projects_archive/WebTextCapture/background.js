let offscreenDocumentReady = false;
let requestIdCounter = 0;
const pendingRequests = new Map();

async function ensureOffscreenDocument() {
  if (offscreenDocumentReady) return;
  const offscreenUrl = chrome.runtime.getURL('offscreen.html');
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl]
  });

  if (contexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['DOM_PARSER'],
      justification: 'Crop screenshots and run OCR in an offscreen document'
    });
  }

  offscreenDocumentReady = true;
}

async function captureVisibleArea(windowId) {
  return chrome.tabs.captureVisibleTab(windowId, { format: 'png' });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'captureSelection') {
    const requestId = ++requestIdCounter;
    pendingRequests.set(requestId, sendResponse);

    Promise.resolve()
      .then(async () => {
        if (typeof sender.tab?.windowId !== 'number') {
          throw new Error('Unable to determine active window for capture.');
        }

        const screenshot = await captureVisibleArea(sender.tab.windowId);
        await ensureOffscreenDocument();

        chrome.runtime.sendMessage({
          target: 'offscreen',
          action: 'ocr',
          requestId,
          imageData: screenshot,
          crop: request.crop || null
        });
      })
      .catch(err => {
        const pending = pendingRequests.get(requestId);
        if (pending) {
          pending({ error: err.message || String(err) });
          pendingRequests.delete(requestId);
        }
      });

    return true;
  }

  if (request.target === 'background' && request.action === 'ocrResult') {
    const pending = pendingRequests.get(request.requestId);
    if (pending) {
      pending({ text: request.text || '', error: request.error || null });
      pendingRequests.delete(request.requestId);
    }
    return true;
  }
});
