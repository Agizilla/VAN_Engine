(function() {
    // 1. Unified Config Sync Engine
    let voiceConfig = { selectedVoiceName: '', rate: 1.0, pitch: 1.0, gender: 'all' };

    // Initialize data from extension storage
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['voiceName', 'rate', 'pitch', 'gender'], (items) => {
            if (items.voiceName) voiceConfig.selectedVoiceName = items.voiceName;
            if (items.rate) voiceConfig.rate = parseFloat(items.rate);
            if (items.pitch) voiceConfig.pitch = parseFloat(items.pitch);
            if (items.gender) voiceConfig.gender = items.gender;
        });
    }

    let playerState = { currentTrackIndex: -1, isPlaying: false, isPaused: false, activeUtterance: null };

    // Setup secure trusted content pipeline
    let escapePolicy = { createHTML: (str) => str };
    if (window.trustedTypes && window.trustedTypes.createPolicy) {
        try { escapePolicy = window.trustedTypes.createPolicy('butler-ext', { createHTML: (s) => s }); } catch (e) {}
    }

    function detectGender(voice) {
        const name = voice.name.toLowerCase();
        if (/female|zira|hazel|susan|heera|elsa/.test(name)) return 'female';
        if (/male|david|george|ravi|mark/.test(name)) return 'male';
        return 'neutral';
    }

    // Intercept default system voice pipelines
    const originalSpeak = window.speechSynthesis.speak;
    window.speechSynthesis.speak = function(utterance) {
        const voices = window.speechSynthesis.getVoices();
        if (voiceConfig.selectedVoiceName) {
            const chosen = voices.find(v => v.name === voiceConfig.selectedVoiceName);
            if (chosen) utterance.voice = chosen;
        }
        utterance.rate = voiceConfig.rate;
        utterance.pitch = voiceConfig.pitch;
        originalSpeak.call(window.speechSynthesis, utterance);
    };

    // 2. Adaptive Multi-Platform DOM Query Selector Hub
    function getAssistantMessages() {
        const selectors = [
            'message-content', '.message-content', '[data-node-type="message-content"]',
            '.model-response', '.ds-markdown'
        ];
        const nodes = document.querySelectorAll(selectors.join(','));
        let cleanNodes = [];
        nodes.forEach(node => {
            let text = node.innerText ? node.innerText.trim() : "";
            if (text.length > 5 && !text.toLowerCase().includes("can make mistakes")) {
                cleanNodes.push(node);
            }
        });
        return cleanNodes;
    }

    function findTargetToolbarWrapper() {
        const geminiMic = document.querySelector('speech-dictation-mic-button');
        if (geminiMic && geminiMic.parentNode.parentNode) {
            return { element: geminiMic.parentNode.parentNode, mode: 'gemini' };
        }
        const dsSendBtn = document.querySelector('[class*="sendButton"]');
        if (dsSendBtn && dsSendBtn.parentNode) {
            return { element: dsSendBtn.parentNode, mode: 'deepseek' };
        }
        return null;
    }

    function playTrack(index, fallbackToLast = false) {
        window.speechSynthesis.cancel();
        playerState.isPlaying = false;
        playerState.isPaused = false;

        const tracks = getAssistantMessages();
        if (tracks.length === 0) { return updateDeckDisplay("NO TRK"); }

        if (index < 0) index = fallbackToLast ? tracks.length - 1 : 0;
        if (index >= tracks.length) index = tracks.length - 1;

        playerState.currentTrackIndex = index;
        const targetNode = tracks[index];
        let rawText = targetNode.innerText || "";
        let cleanText = rawText.replace(/```[\s\S]*?```/g, '').trim();

        if (!cleanText) { return updateDeckDisplay('ERR TRK'); }

        updateDeckDisplay('TRK ' + String(index + 1).padStart(2, '0') + '/' + String(tracks.length).padStart(2, '0'));

        const utterance = new SpeechSynthesisUtterance(cleanText);
        playerState.activeUtterance = utterance;
        playerState.isPlaying = true;

        utterance.onend = () => { if (!playerState.isPaused) { playerState.isPlaying = false; syncControlsUI(); } };
        utterance.onerror = () => { playerState.isPlaying = false; playerState.isPaused = false; syncControlsUI(); };

        window.speechSynthesis.speak(utterance);
        syncControlsUI();
    }

    function togglePlayPause() {
        if (playerState.isPlaying && !playerState.isPaused) {
            window.speechSynthesis.pause(); playerState.isPaused = true; syncControlsUI();
        } else if (playerState.isPlaying && playerState.isPaused) {
            window.speechSynthesis.resume(); playerState.isPaused = false; syncControlsUI();
        } else {
            playTrack(playerState.currentTrackIndex, true);
        }
    }

    function stopPlayback() {
        window.speechSynthesis.cancel();
        playerState.isPlaying = false; playerState.isPaused = false; playerState.currentTrackIndex = -1;
        syncControlsUI(); refreshDisplayStats();
    }

    function copyCurrentTrackText() {
        const tracks = getAssistantMessages();
        if (playerState.currentTrackIndex === -1 || !tracks[playerState.currentTrackIndex]) return;
        const rawText = tracks[playerState.currentTrackIndex].innerText || "";
        const cleanText = rawText.replace(/```[\s\S]*?```/g, '').trim();

        navigator.clipboard.writeText(cleanText).then(() => {
            const copyBtn = document.getElementById('butler-deck-copy-btn');
            if (!copyBtn) return;
            copyBtn.innerText = "DONE";
            setTimeout(() => { copyBtn.innerText = "\uD83D\uDCCB"; }, 1200);
        });
    }

    function syncControlsUI() {
        const playBtn = document.getElementById('butler-deck-play-btn');
        const copyBtn = document.getElementById('butler-deck-copy-btn');
        if (playBtn) playBtn.innerText = (playerState.isPlaying && !playerState.isPaused) ? "\u23F8" : "\u25B6";
        if (copyBtn) copyBtn.style.display = (playerState.currentTrackIndex !== -1) ? "block" : "none";
    }

    function updateDeckDisplay(text) {
        const display = document.getElementById('butler-deck-display-screen');
        if (display) display.innerText = text;
    }

    function refreshDisplayStats() {
        if (playerState.isPlaying) return;
        const tracks = getAssistantMessages();
        if (tracks.length === 0) {
            updateDeckDisplay("00 / 00");
        } else {
            const currentDisplayIdx = playerState.currentTrackIndex !== -1 ? playerState.currentTrackIndex + 1 : tracks.length;
            updateDeckDisplay('CH ' + String(currentDisplayIdx).padStart(2, '0') + '/' + String(tracks.length).padStart(2, '0'));
        }
        syncControlsUI();
    }

    function breakNativeLayoutEncapsulation() {
        const geminiTarget = document.querySelector('#app-root > main > side-navigation-v2 > bard-sidenav-container > bard-sidenav-content > div > div > div > bots-chat-window > chat-window > div > input-container > fieldset > input-area-v2 > div > div');
        if (geminiTarget) {
            let current = geminiTarget;
            for (let i = 0; i < 4; i++) {
                if (current) { current.style.maxWidth = 'none'; current.style.width = '100%'; current = current.parentNode; }
            }
        }
    }

    function launchSettingsModal() {
        if (document.getElementById('butler-modal-overlay')) return;
        const overlay = document.createElement('div');
        overlay.id = 'butler-modal-overlay';

        const voices = window.speechSynthesis.getVoices();
        const femaleOptions = voices.filter(v => detectGender(v) === 'female').map(v => '<option value="' + v.name + '" ' + (v.name === voiceConfig.selectedVoiceName ? 'selected' : '') + '>' + v.name + ' (' + v.lang + ')</option>').join('');
        const maleOptions = voices.filter(v => detectGender(v) !== 'female').map(v => '<option value="' + v.name + '" ' + (v.name === voiceConfig.selectedVoiceName ? 'selected' : '') + '>' + v.name + ' (' + v.lang + ')</option>').join('');

        overlay.innerHTML = escapePolicy.createHTML(
            '<div class="butler-modal">' +
            '<h2>Butler Voice Synthesis Panel</h2>' +
            '<div class="butler-field"><label>Female Voice Profiles</label><select id="butler-female-select"><option value="">-- Choose Profile --</option>' + femaleOptions + '</select></div>' +
            '<div class="butler-field"><label>Male Profiles</label><select id="butler-male-select"><option value="">-- Choose Profile --</option>' + maleOptions + '</select></div>' +
            '<div class="butler-field"><label>Speech Rate</label><div class="butler-slider-container"><input type="range" id="butler-rate" min="0.5" max="2" step="0.05" value="' + voiceConfig.rate + '"><span id="butler-rate-txt">' + voiceConfig.rate + 'x</span></div></div>' +
            '<div class="butler-field"><label>Voice Pitch</label><div class="butler-slider-container"><input type="range" id="butler-pitch" min="0.5" max="1.5" step="0.05" value="' + voiceConfig.pitch + '"><span id="butler-pitch-txt">' + voiceConfig.pitch + '</span></div></div>' +
            '<div class="butler-actions"><button class="butler-btn butler-btn-test" id="butler-test">\uD83C\uDF99\uFE0F Preview</button>' +
            '<button class="butler-btn butler-btn-cancel" id="butler-close">Cancel</button>' +
            '<button class="butler-btn butler-btn-apply" id="butler-save">Apply</button></div></div>'
        );
        document.body.appendChild(overlay);

        const rSlider = document.getElementById('butler-rate');
        const pSlider = document.getElementById('butler-pitch');
        rSlider.oninput = function() { document.getElementById('butler-rate-txt').innerText = rSlider.value + 'x'; };
        pSlider.oninput = function() { document.getElementById('butler-pitch-txt').innerText = pSlider.value; };

        document.getElementById('butler-test').onclick = function() {
            window.speechSynthesis.cancel();
            const targetVoice = document.getElementById('butler-female-select').value || document.getElementById('butler-male-select').value;
            const u = new SpeechSynthesisUtterance("Testing configuration parameters.");
            if (targetVoice) u.voice = voices.find(function(v) { return v.name === targetVoice; });
            u.rate = parseFloat(rSlider.value); u.pitch = parseFloat(pSlider.value);
            originalSpeak.call(window.speechSynthesis, u);
        };

        document.getElementById('butler-save').onclick = function() {
            voiceConfig.selectedVoiceName = document.getElementById('butler-female-select').value || document.getElementById('butler-male-select').value;
            voiceConfig.rate = parseFloat(rSlider.value);
            voiceConfig.pitch = parseFloat(pSlider.value);

            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({ voiceName: voiceConfig.selectedVoiceName, rate: voiceConfig.rate, pitch: voiceConfig.pitch });
            }
            overlay.remove();
        };

        document.getElementById('butler-close').onclick = function() { window.speechSynthesis.cancel(); overlay.remove(); };
    }

    function injectMediaDeck() {
        if (document.getElementById('butler-media-deck-toolbar')) return;

        const targetHook = findTargetToolbarWrapper();
        if (!targetHook) return;

        breakNativeLayoutEncapsulation();

        const deck = document.createElement('div');
        deck.id = 'butler-media-deck-toolbar';
        deck.className = 'butler-media-deck';

        deck.innerHTML = escapePolicy.createHTML(
            '<div id="butler-deck-display-screen" class="butler-deck-display">-- / --</div>' +
            '<button class="butler-btn-action butler-deck-btn" data-action="first" title="First Message">|\u25C0</button>' +
            '<button class="butler-btn-action butler-deck-btn" data-action="prev" title="Previous">\u25C0\u25C0</button>' +
            '<button id="butler-deck-play-btn" class="butler-deck-btn" title="Play/Pause">\u25B6</button>' +
            '<button class="butler-btn-action butler-deck-btn" data-action="stop" title="Stop">\u23F9</button>' +
            '<button class="butler-btn-action butler-deck-btn" data-action="next" title="Next">\u25B6\u25B6</button>' +
            '<button class="butler-btn-action butler-deck-btn" data-action="last" title="Last">\u25B6|</button>' +
            '<button id="butler-deck-copy-btn" class="butler-deck-btn" title="Copy Text">\uD83D\uDCCB</button>' +
            '<button id="butler-deck-gear-btn" class="butler-deck-btn butler-deck-btn-gear" title="Settings">' +
            '<svg viewBox="0 0 24 24"><path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.85,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.43-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/></svg>' +
            '</button>'
        );

        deck.querySelectorAll('.butler-btn-action').forEach(function(btn) {
            btn.onclick = function(e) {
                e.preventDefault();
                var act = btn.getAttribute('data-action');
                if (act === 'first') playTrack(0);
                if (act === 'prev') playTrack(playerState.currentTrackIndex - 1);
                if (act === 'stop') stopPlayback();
                if (act === 'next') playTrack(playerState.currentTrackIndex + 1);
                if (act === 'last') playTrack(-1, true);
            };
        });

        deck.querySelector('#butler-deck-play-btn').onclick = function(e) { e.preventDefault(); togglePlayPause(); };
        deck.querySelector('#butler-deck-copy-btn').onclick = function(e) { e.preventDefault(); copyCurrentTrackText(); };
        deck.querySelector('#butler-deck-gear-btn').onclick = function(e) { e.preventDefault(); launchSettingsModal(); };

        if (targetHook.mode === 'gemini') {
            targetHook.element.insertBefore(deck, targetHook.element.firstChild);
        } else {
            targetHook.element.style.display = 'flex';
            targetHook.element.style.alignItems = 'center';
            targetHook.element.insertBefore(deck, targetHook.element.firstChild);
        }
        refreshDisplayStats();
    }

    // 3. Execution Pipeline Initialization
    injectMediaDeck();
    var observer = new MutationObserver(function(mutations) {
        var updateRequired = false;
        for (var i = 0; i < mutations.length; i++) {
            var m = mutations[i];
            if (m.target && m.target.id !== 'butler-deck-display-screen' && !(m.target.closest && m.target.closest('.butler-media-deck'))) {
                updateRequired = true; break;
            }
        }
        if (updateRequired) { injectMediaDeck(); breakNativeLayoutEncapsulation(); refreshDisplayStats(); }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
