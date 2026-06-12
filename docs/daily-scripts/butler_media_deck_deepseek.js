// =============================================================================
// BUTLER MEDIA DECK — DeepSeek Edition
// Voice Synthesis Playback Toolbar for chat.deepseek.com
//
// Usage: Paste into browser DevTools Console (F12) on DeepSeek chat page.
// Or save as a bookmarklet: javascript:(function(){...})()
//
// Features:
// - Selects assistant messages via .ds-markdown + data-testid selectors
// - localStorage-based voice settings persistence (not chrome.storage)
// - Play/Pause/Stop/Prev/Next/First/Last + Copy text
// - Settings modal: voice selection, rate, pitch, preview
// - MutationObserver auto-reinjects on new messages
// - Trusted Types CSP bypass
//
// Target platform: chat.deepseek.com
// Author: OpenCode / VAN_Engine Collective
// Location: docs/daily-scripts/butler_media_deck_deepseek.js
// =============================================================================

(function() {
    'use strict';

    // ==================== 1. Core Config & State ====================
    let voiceConfig = {
        selectedVoiceName: localStorage.getItem('ds_voice_name') || '',
        rate: parseFloat(localStorage.getItem('ds_voice_rate')) || 1.0,
        pitch: parseFloat(localStorage.getItem('ds_voice_pitch')) || 1.0,
        gender: localStorage.getItem('ds_voice_gender') || 'all'
    };

    let playerState = {
        currentTrackIndex: -1,
        isPlaying: false,
        isPaused: false,
        activeUtterance: null
    };

    // ==================== 2. TrustedTypes Bypass ====================
    let escapePolicy = { createHTML: (s) => s };
    if (window.trustedTypes?.createPolicy) {
        try { escapePolicy = window.trustedTypes.createPolicy('ds-bypass-v3', { createHTML: (s) => s }); } catch(e) {}
    }

    // ==================== 3. Voice Gender Helper ====================
    function detectGender(voice) {
        const name = voice.name.toLowerCase();
        if (name.includes('female') || name.includes('zira') || name.includes('hazel') || name.includes('susan') || name.includes('heera') || name.includes('elsa')) return 'female';
        if (name.includes('male') || name.includes('david') || name.includes('george') || name.includes('ravi') || name.includes('mark')) return 'male';
        return 'neutral';
    }

    // ==================== 4. Intercept Speech Synthesis ====================
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

    // ==================== 5. Get Assistant Messages ====================
    function getAssistantMessages() {
        const nodes = document.querySelectorAll('.ds-markdown, [data-testid="assistant-message"], .message-content');
        return Array.from(nodes).filter(el => {
            const txt = el.innerText.trim();
            return txt.length > 20 && !txt.toLowerCase().includes("can make mistakes");
        });
    }

    // ==================== 6. Player Controls ====================
    function updateDeckDisplay(text) {
        const display = document.getElementById('ds-deck-display');
        if (display) display.innerText = text;
    }

    function refreshDisplayStats() {
        if (playerState.isPlaying) return;
        const tracks = getAssistantMessages();
        if (!tracks.length) updateDeckDisplay('00/00');
        else {
            const idx = playerState.currentTrackIndex !== -1 ? playerState.currentTrackIndex + 1 : tracks.length;
            updateDeckDisplay(`${String(idx).padStart(2,'0')}/${String(tracks.length).padStart(2,'0')}`);
        }
    }

    function playTrack(index, fallbackToLast = false) {
        window.speechSynthesis.cancel();
        playerState.isPlaying = false;
        playerState.isPaused = false;

        const tracks = getAssistantMessages();
        if (!tracks.length) { updateDeckDisplay('NO TRK'); return; }

        if (index < 0) index = fallbackToLast ? tracks.length - 1 : 0;
        if (index >= tracks.length) index = tracks.length - 1;

        playerState.currentTrackIndex = index;
        const rawText = tracks[index].innerText || '';
        const cleanText = rawText.replace(/```[\s\S]*?```/g, '').trim();
        if (!cleanText) return;

        updateDeckDisplay(`${String(index+1).padStart(2,'0')}/${String(tracks.length).padStart(2,'0')}`);
        const utterance = new SpeechSynthesisUtterance(cleanText);
        playerState.activeUtterance = utterance;
        playerState.isPlaying = true;
        utterance.onend = () => { playerState.isPlaying = false; syncControlsUI(); };
        utterance.onerror = () => { playerState.isPlaying = false; syncControlsUI(); };
        window.speechSynthesis.speak(utterance);
        syncControlsUI();
    }

    function togglePlayPause() {
        if (playerState.isPlaying && !playerState.isPaused) {
            window.speechSynthesis.pause();
            playerState.isPaused = true;
        } else if (playerState.isPlaying && playerState.isPaused) {
            window.speechSynthesis.resume();
            playerState.isPaused = false;
        } else {
            playTrack(playerState.currentTrackIndex, true);
        }
        syncControlsUI();
    }

    function stopPlayback() {
        window.speechSynthesis.cancel();
        playerState.isPlaying = false;
        playerState.isPaused = false;
        playerState.currentTrackIndex = -1;
        syncControlsUI();
        refreshDisplayStats();
    }

    function copyCurrentTrackText() {
        const tracks = getAssistantMessages();
        if (playerState.currentTrackIndex === -1 || !tracks[playerState.currentTrackIndex]) return;
        const rawText = tracks[playerState.currentTrackIndex].innerText || '';
        const cleanText = rawText.replace(/```[\s\S]*?```/g, '').trim();
        navigator.clipboard.writeText(cleanText).then(() => {
            const btn = document.getElementById('ds-copy-btn');
            if (btn) { btn.innerText = '\u2713'; setTimeout(() => btn.innerText = '\uD83D\uDCCB', 1500); }
        }).catch(console.error);
    }

    function syncControlsUI() {
        const playBtn = document.getElementById('ds-play-btn');
        if (playBtn) playBtn.innerText = (playerState.isPlaying && !playerState.isPaused) ? '\u23F8' : '\u25B6';
        const copyBtn = document.getElementById('ds-copy-btn');
        if (copyBtn) copyBtn.style.display = (playerState.currentTrackIndex !== -1) ? 'inline-flex' : 'none';
    }

    // ==================== 7. Settings Modal ====================
    function launchSettingsModal() {
        if (document.getElementById('ds-modal-overlay')) return;
        const voices = window.speechSynthesis.getVoices();
        const femaleVoices = voices.filter(v => detectGender(v) === 'female');
        const maleVoices = voices.filter(v => detectGender(v) === 'male' || detectGender(v) === 'neutral');

        const femaleOptions = femaleVoices.map(v => `<option value="${v.name}" ${v.name === voiceConfig.selectedVoiceName ? 'selected' : ''}>${v.name} (${v.lang})</option>`).join('');
        const maleOptions = maleVoices.map(v => `<option value="${v.name}" ${v.name === voiceConfig.selectedVoiceName ? 'selected' : ''}>${v.name} (${v.lang})</option>`).join('');

        const modalHTML = escapePolicy.createHTML(`
            <div id="ds-modal-overlay" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);z-index:999999;display:flex;align-items:center;justify-content:center;">
                <div style="background:#1a1a20;border:1px solid #3a2a4e;border-radius:12px;width:440px;padding:1.5rem;color:#e0e0e0;">
                    <h2 style="color:#a78bfa;margin-top:0;">Voice Settings</h2>
                    <div style="margin-bottom:0.8rem;"><label style="display:block;font-size:0.75rem;">Female</label>
                        <select id="ds-voice-female" style="width:100%;background:#121216;border:1px solid #2a2a2e;border-radius:6px;padding:0.4rem;color:#ccc;">${femaleOptions}</select>
                    </div>
                    <div style="margin-bottom:0.8rem;"><label style="display:block;font-size:0.75rem;">Male</label>
                        <select id="ds-voice-male" style="width:100%;background:#121216;border:1px solid #2a2a2e;border-radius:6px;padding:0.4rem;color:#ccc;">${maleOptions}</select>
                    </div>
                    <div style="margin-bottom:0.8rem;">
                        <label style="display:block;font-size:0.75rem;">Gender</label>
                        <div style="display:flex;gap:0.8rem;">
                            <label><input type="radio" name="ds-gender" value="female" ${voiceConfig.gender === 'female' ? 'checked' : ''}> Female</label>
                            <label><input type="radio" name="ds-gender" value="male" ${voiceConfig.gender === 'male' ? 'checked' : ''}> Male</label>
                            <label><input type="radio" name="ds-gender" value="all" ${voiceConfig.gender === 'all' ? 'checked' : ''}> All</label>
                        </div>
                    </div>
                    <div style="margin-bottom:0.8rem;">
                        <label style="display:block;font-size:0.75rem;">Rate: <span id="ds-rate-val">${voiceConfig.rate}</span>x</label>
                        <input type="range" id="ds-rate" min="0.5" max="2" step="0.05" value="${voiceConfig.rate}" style="width:100%;">
                    </div>
                    <div style="margin-bottom:0.8rem;">
                        <label style="display:block;font-size:0.75rem;">Pitch: <span id="ds-pitch-val">${voiceConfig.pitch}</span></label>
                        <input type="range" id="ds-pitch" min="0.5" max="1.5" step="0.05" value="${voiceConfig.pitch}" style="width:100%;">
                    </div>
                    <div style="display:flex;gap:0.5rem;margin-top:1rem;">
                        <button id="ds-test" style="background:#3b2a4e;border:1px solid #a78bfa;padding:0.5rem 1rem;border-radius:6px;color:#c4b5fd;">Test</button>
                        <button id="ds-apply" style="background:#a78bfa;border:none;padding:0.5rem 1rem;border-radius:6px;font-weight:bold;">Apply</button>
                        <button id="ds-cancel" style="background:#2a2a2e;border:none;padding:0.5rem 1rem;border-radius:6px;">Cancel</button>
                    </div>
                </div>
            </div>`);
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const overlay = document.getElementById('ds-modal-overlay');
        const rateSlider = document.getElementById('ds-rate'), pitchSlider = document.getElementById('ds-pitch');
        rateSlider.oninput = () => document.getElementById('ds-rate-val').innerText = rateSlider.value;
        pitchSlider.oninput = () => document.getElementById('ds-pitch-val').innerText = pitchSlider.value;
        function getSelectedVoice() {
            const gender = document.querySelector('input[name="ds-gender"]:checked').value;
            if (gender === 'female') return document.getElementById('ds-voice-female').value;
            if (gender === 'male') return document.getElementById('ds-voice-male').value;
            return document.getElementById('ds-voice-female').value || document.getElementById('ds-voice-male').value;
        }
        document.getElementById('ds-test').onclick = () => {
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance("Testing voice configuration.");
            const vn = getSelectedVoice();
            if (vn) { const ch = voices.find(v => v.name === vn); if (ch) utter.voice = ch; }
            utter.rate = parseFloat(rateSlider.value); utter.pitch = parseFloat(pitchSlider.value);
            originalSpeak.call(window.speechSynthesis, utter);
        };
        document.getElementById('ds-apply').onclick = () => {
            voiceConfig.gender = document.querySelector('input[name="ds-gender"]:checked').value;
            voiceConfig.selectedVoiceName = getSelectedVoice();
            voiceConfig.rate = parseFloat(rateSlider.value);
            voiceConfig.pitch = parseFloat(pitchSlider.value);
            localStorage.setItem('ds_voice_name', voiceConfig.selectedVoiceName);
            localStorage.setItem('ds_voice_rate', voiceConfig.rate);
            localStorage.setItem('ds_voice_pitch', voiceConfig.pitch);
            localStorage.setItem('ds_voice_gender', voiceConfig.gender);
            overlay.remove();
        };
        document.getElementById('ds-cancel').onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    }

    // ==================== 8. Button Factory ====================
    function makeButton(text, title, onClick) {
        const btn = document.createElement('button');
        btn.innerText = text;
        btn.title = title;
        btn.style.cssText = 'background:transparent;border:none;color:#a5a5b5;cursor:pointer;padding:4px 6px;font-size:0.8rem;border-radius:4px;min-width:28px;';
        btn.onclick = (e) => { e.preventDefault(); onClick(); };
        return btn;
    }

    // ==================== 9. Create Deck Element ====================
    function createDeckElement() {
        const deck = document.createElement('div');
        deck.id = 'ds-media-deck';
        deck.style.cssText = 'display:inline-flex;align-items:center;background:#121216;border:1px solid #2a2a35;border-radius:20px;padding:2px 10px;gap:4px;height:34px;font-family:monospace;flex-shrink:0;margin-left:auto;margin-right:8px;';

        const display = document.createElement('div');
        display.id = 'ds-deck-display';
        display.style.cssText = 'color:#00ffcc;font-size:0.7rem;padding:0 6px;min-width:60px;text-align:center;';
        display.innerText = '--/--';

        const btnFirst = makeButton('\u23EE', 'First', () => playTrack(0));
        const btnPrev = makeButton('\u25C0\u25C0', 'Previous', () => playTrack(playerState.currentTrackIndex - 1));
        const btnPlay = makeButton('\u25B6', 'Play/Pause', togglePlayPause);
        btnPlay.id = 'ds-play-btn';
        const btnStop = makeButton('\u23F9', 'Stop', stopPlayback);
        const btnNext = makeButton('\u25B6\u25B6', 'Next', () => playTrack(playerState.currentTrackIndex + 1));
        const btnLast = makeButton('\u23ED', 'Last', () => playTrack(-1, true));
        const btnCopy = makeButton('\uD83D\uDCCB', 'Copy text', copyCurrentTrackText);
        btnCopy.id = 'ds-copy-btn';
        btnCopy.style.display = 'none';
        const btnGear = makeButton('\u2699\uFE0F', 'Voice settings', launchSettingsModal);

        deck.append(display, btnFirst, btnPrev, btnPlay, btnStop, btnNext, btnLast, btnCopy, btnGear);
        return deck;
    }

    // ==================== 10. Inject Media Deck ====================
    function injectMediaDeck() {
        if (document.getElementById('ds-media-deck')) return;

        const inputContainer = document.querySelector('.bf38813a');
        if (!inputContainer) {
            setTimeout(injectMediaDeck, 500);
            return;
        }

        const deck = createDeckElement();
        inputContainer.appendChild(deck);
        refreshDisplayStats();
    }

    // ==================== 11. Start Injection & Observer ====================
    injectMediaDeck();
    const observer = new MutationObserver(() => injectMediaDeck());
    observer.observe(document.body, { childList: true, subtree: true });
})();
