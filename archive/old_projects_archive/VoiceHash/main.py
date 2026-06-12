from flask import Flask, render_template_string, request, jsonify
import hashlib, time, json, random

app = Flask(__name__)

def is_prime(n):
    return n > 1 and all(n % i for i in range(2, int(n**0.5) + 1))

HTML = """
<!DOCTYPE html>
<body style="background:#0a0a0a;color:#0f0;font-family:monospace;text-align:center;padding:50px;">
    <h2>--- THE DIGITAL RITUAL ---</h2>
    <div id="status">Speak your intent or type below...</div>
    <input id="textInput" style="background:#000;color:#0f0;border:1px solid #0f0;padding:10px;width:300px;">
    <button onclick="startRitual()" style="background:#0f0;color:#000;border:none;padding:10px 20px;cursor:pointer;">INVOKE</button>
    <div id="scroll" style="font-size:2em;margin:30px;height:50px;"></div>
    <div id="result"></div>
    <script>
        let interval, lastPrime = 2;
        function startRitual() {
            const input = document.getElementById('textInput').value;
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.onresult = (e) => process(e.results[0][0].transcript);
            recognition.onerror = () => process(input || "VOID");
            document.getElementById('status').innerText = "LISTENING...";
            recognition.start();
        }
        function process(text) {
            document.getElementById('status').innerText = "RITUAL IN PROGRESS. Press 'S' to Stop.";
            interval = setInterval(() => {
                let p = Math.floor(Math.random() * 9000) + 100;
                document.getElementById('scroll').innerText = " > " + p;
                lastPrime = p; // Simplification: assume prime for visual, server verifies
            }, 1000);
            window.addEventListener('keydown', (e) => { if(e.key.toLowerCase() === 's') seal(text); });
        }
        async function seal(text) {
            clearInterval(interval);
            const res = await fetch('/save', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text, prime: lastPrime})
            });
            const data = await res.json();
            document.getElementById('result').innerHTML = `<h3>Ritual Sealed</h3>Hash: ${data.hash}<br>Secret Prime: ${data.prime}`;
        }
    </script>
</body>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    # Ensure we store an actual prime if the UI was just cycling numbers
    p = data['prime']
    while not is_prime(p): p += 1
    h = hashlib.sha256(data['text'].encode()).hexdigest()[:32]
    entry = {"hash": f"0x{h}", "prime": p, "timestamp": time.time()}
    with open("me.json", "w") as f: json.dump(entry, f, indent=4)
    return jsonify(entry)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)