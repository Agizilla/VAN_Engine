let selectionActive = false;
let startX = 0;
let startY = 0;
let endX = 0;
let endY = 0;
let overlayDiv = null;
let selectionDiv = null;
let statusDiv = null;

function createOverlay() {
  overlayDiv = document.createElement('div');
  overlayDiv.id = 'ocr-overlay';

  selectionDiv = document.createElement('div');
  selectionDiv.id = 'ocr-selection';
  selectionDiv.style.display = 'none';

  statusDiv = document.createElement('div');
  statusDiv.id = 'ocr-status';
  statusDiv.textContent = 'Drag to select text';

  overlayDiv.appendChild(selectionDiv);
  overlayDiv.appendChild(statusDiv);
  document.documentElement.appendChild(overlayDiv);
}

function removeOverlay() {
  overlayDiv?.remove();
  overlayDiv = null;
  selectionDiv = null;
  statusDiv = null;
  selectionActive = false;
}

function setStatus(message) {
  if (statusDiv) statusDiv.textContent = message;
}

function getCropRect() {
  const left = Math.min(startX, endX);
  const top = Math.min(startY, endY);
  const width = Math.abs(endX - startX);
  const height = Math.abs(endY - startY);
  return {
    x: left,
    y: top,
    width,
    height,
    devicePixelRatio: window.devicePixelRatio || 1
  };
}

function copyToClipboard(text) {
  return navigator.clipboard.writeText(text).then(() => {
    const preview = text.length > 120 ? `${text.slice(0, 120)}...` : text;
    alert(`Text copied to clipboard:\n\n${preview}`);
  });
}

function runCapture() {
  const crop = getCropRect();
  setStatus('Running OCR...');

  chrome.runtime.sendMessage({ action: 'captureSelection', crop }, async response => {
    if (chrome.runtime.lastError) {
      alert(`Error communicating with extension: ${chrome.runtime.lastError.message}`);
      removeOverlay();
      return;
    }

    if (!response) {
      alert('No OCR response received.');
      removeOverlay();
      return;
    }

    if (response.error) {
      alert(`OCR failed: ${response.error}`);
      removeOverlay();
      return;
    }

    const text = (response.text || '').trim();
    if (!text) {
      alert('No text found in the selected area.');
      removeOverlay();
      return;
    }

    try {
      await copyToClipboard(text);
    } catch (err) {
      alert(`Text extracted but clipboard copy failed: ${err.message}`);
    }

    removeOverlay();
  });
}

function onMouseDown(event) {
  if (!selectionActive) return;

  startX = event.clientX;
  startY = event.clientY;
  endX = event.clientX;
  endY = event.clientY;

  selectionDiv.style.left = `${startX}px`;
  selectionDiv.style.top = `${startY}px`;
  selectionDiv.style.width = '0px';
  selectionDiv.style.height = '0px';
  selectionDiv.style.display = 'block';

  function onMouseMove(moveEvent) {
    endX = moveEvent.clientX;
    endY = moveEvent.clientY;
    const left = Math.min(startX, endX);
    const top = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);

    selectionDiv.style.left = `${left}px`;
    selectionDiv.style.top = `${top}px`;
    selectionDiv.style.width = `${width}px`;
    selectionDiv.style.height = `${height}px`;
  }

  function onMouseUp(upEvent) {
    document.removeEventListener('mousemove', onMouseMove, true);
    document.removeEventListener('mouseup', onMouseUp, true);

    endX = upEvent.clientX;
    endY = upEvent.clientY;
    const crop = getCropRect();
    if (crop.width < 8 || crop.height < 8) {
      alert('Selection area too small. Please drag a larger rectangle.');
      removeOverlay();
      return;
    }

    runCapture();
  }

  document.addEventListener('mousemove', onMouseMove, true);
  document.addEventListener('mouseup', onMouseUp, true);
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    sendResponse({ status: 'ready' });
    return true;
  }

  if (request.action === 'startSelection') {
    if (selectionActive) {
      sendResponse({ status: 'already_active' });
      return true;
    }

    selectionActive = true;
    createOverlay();
    overlayDiv.addEventListener('mousedown', onMouseDown, true);
    sendResponse({ status: 'started' });
    return true;
  }
});
