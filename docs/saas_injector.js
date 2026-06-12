(function() {
    // SAAS endpoint list — points to local ClawDia hooks server
    const BASE = 'http://127.0.0.1:8001';
    const endpoints = {
        "\ud83d\udcc4 Text Summarize":               BASE + "/hooks/text_summarize",
        "\u270d\ufe0f Text Rewrite":                 BASE + "/hooks/text_rewrite",
        "\u2728 Text Generate":                      BASE + "/hooks/text_generate",
        "\ud83c\udff7\ufe0f Text Classify":           BASE + "/hooks/text_classify",
        "\ud83d\udd0d Extract Entities":              BASE + "/hooks/text_extract_entities",
        "\ud83c\udf10 Translate (ES/FR/DE/PT/IT)":   BASE + "/hooks/text_translate",
        "\ud83c\udfb5 MIDI Composer (Mike)":          BASE + "/hooks/midi_render",
        "\ud83e\udd16 Multi-Agent Forge":             BASE + "/hooks/forge",
        "\ud83c\udfa8 Unified Studio UI":             BASE + "/hooks/ui",
    };

    // Create floating button
    const btn = document.createElement('button');
    btn.innerText = '\ud83d\ude80 Open SAAS Studio';
    btn.style.position = 'fixed';
    btn.style.bottom = '20px';
    btn.style.right = '20px';
    btn.style.zIndex = '999999';
    btn.style.padding = '12px 20px';
    btn.style.backgroundColor = '#8b5cf6';
    btn.style.border = 'none';
    btn.style.borderRadius = '40px';
    btn.style.color = 'white';
    btn.style.fontWeight = 'bold';
    btn.style.cursor = 'pointer';
    btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    btn.style.fontFamily = 'system-ui, sans-serif';

    // Modal backdrop
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
    modal.style.zIndex = '1000000';
    modal.style.display = 'none';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.fontFamily = 'system-ui, sans-serif';

    const modalContent = document.createElement('div');
    modalContent.style.backgroundColor = '#1e1e2a';
    modalContent.style.borderRadius = '24px';
    modalContent.style.padding = '24px';
    modalContent.style.maxWidth = '560px';
    modalContent.style.width = '90%';
    modalContent.style.color = '#eef2ff';
    modalContent.style.boxShadow = '0 20px 35px rgba(0,0,0,0.5)';

    modalContent.innerHTML = `
        <h2 style="margin-top:0; color:#c084fc;">\u2728 SAAS Endpoints</h2>
        <p style="font-size:13px; color:#94a3b8;">ClawDia hooks server running at <code style="background:#0a0a10; padding:2px 6px; border-radius:6px;">${BASE}</code></p>
        <ul style="list-style:none; padding:0; margin:16px 0;">
            ${Object.entries(endpoints).map(([name, url]) =>
                `<li style="margin:10px 0; display:flex; align-items:center; gap:8px;">
                    <span style="flex-shrink:0;">${name}</span>
                    <code style="flex:1; font-size:11px; background:#0a0a10; padding:4px 8px; border-radius:8px; word-break:break-all;">${url}</code>
                    <button class="copy-btn" data-url="${url}" style="background:#3a3a4a; border:none; padding:4px 10px; border-radius:20px; cursor:pointer; font-size:11px;">Copy</button>
                </li>`
            ).join('')}
        </ul>
        <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button id="closeModalBtn" style="background:#3a3a4a; border:none; padding:8px 16px; border-radius:40px; cursor:pointer;">Close</button>
            <button id="launchStudioBtn" style="background:#8b5cf6; border:none; padding:8px 16px; border-radius:40px; cursor:pointer;">\ud83d\ude80 Open API Guide</button>
        </div>
    `;

    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    document.body.appendChild(btn);

    btn.onclick = () => { modal.style.display = 'flex'; };

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    document.getElementById('closeModalBtn').onclick = () => { modal.style.display = 'none'; };
    document.getElementById('launchStudioBtn').onclick = () => {
        window.open(BASE + '/hooks/ui', '_blank');
        modal.style.display = 'none';
    };

    // Copy-to-clipboard for each endpoint
    setTimeout(() => {
        document.querySelectorAll('.copy-btn').forEach(el => {
            el.onclick = () => {
                navigator.clipboard.writeText(el.dataset.url);
                el.innerText = 'Copied!';
                setTimeout(() => { el.innerText = 'Copy'; }, 1500);
            };
        });
    }, 100);

    console.log('\u2705 SAAS injector ready \u2014 click the floating button.');
})();
