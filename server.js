require('dotenv').config();
const express = require('express');
const { WebSocketServer } = require('ws');
const cors = require('cors');
const { exec } = require('child_process');
const http = require('http');
const https = require('https');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// ── Translation helper ──
function callTranslation(text, targetLang, callback) {
  const postData = JSON.stringify({ text, targetLang });
  const options = {
    hostname: 'hermia-translation.onrender.com',
    port: 443,
    path: '/',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };
  const req = https.request(options, (res) => {
    let d = '';
    res.on('data', chunk => d += chunk);
    res.on('end', () => {
      try { callback(null, JSON.parse(d)); }
      catch(e) { callback(e); }
    });
  });
  req.on('error', (e) => callback(e));
  req.write(postData);
  req.end();
}

app.get('/health', (req, res) => {
  res.json({ 
    status: 'Hermia is running',
    version: '1.0.0',
    models: {
      transcription: 'faster-whisper',
      translation: 'LibreTranslate via hermia-translation.onrender.com'
    }
  });
});

app.post('/translate', (req, res) => {
  const { text, targetLang } = req.body;
  if (!text || !targetLang) return res.status(400).json({ error: 'Missing text or targetLang' });
  callTranslation(text, targetLang, (err, result) => {
    if (err) return res.status(500).json({ error: 'Translation server error' });
    res.json(result);
  });
});

app.post('/transcribe', (req, res) => {
  const { audio, language } = req.body;
  if (!audio) return res.status(400).json({ error: 'Missing audio' });
  const audioPath = path.join(__dirname, `temp_${Date.now()}.wav`);
  fs.writeFileSync(audioPath, Buffer.from(audio, 'base64'));
  const cmd = `venv\\Scripts\\python.exe transcribe.py "${audioPath}" "${language || 'en'}"`;
  exec(cmd, { cwd: __dirname }, (err, stdout) => {
    fs.unlinkSync(audioPath);
    if (err) return res.status(500).json({ error: err.message });
    try { res.json(JSON.parse(stdout)); }
    catch(e) { res.status(500).json({ error: 'Parse error' }); }
  });
});

wss.on('connection', (ws) => {
  console.log('Client connected');
  ws.send(JSON.stringify({ type: 'connected', message: 'Hermia ready' }));

  ws.on('message', async (data) => {
    try {
      const msg = JSON.parse(data);

      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong' }));
      }

      if (msg.type === 'translate') {
        const { text, targetLangs } = msg;
        targetLangs.forEach(lang => {
          callTranslation(text, lang, (err, result) => {
            if (err) return;
            ws.send(JSON.stringify({
              type: 'translation',
              language: lang,
              original: text,
              translated: result.translated
            }));
          });
        });
      }

      if (msg.type === 'transcribe') {
        const audioPath = path.join(__dirname, `temp_${Date.now()}.wav`);
        fs.writeFileSync(audioPath, Buffer.from(msg.audio, 'base64'));
        const cmd = `venv\\Scripts\\python.exe transcribe.py "${audioPath}" "${msg.language || 'en'}"`;
        exec(cmd, { cwd: __dirname }, (err, stdout) => {
          fs.unlinkSync(audioPath);
          if (err) return;
          try {
            const result = JSON.parse(stdout);
            ws.send(JSON.stringify({
              type: 'caption',
              text: result.text,
              language: result.language,
              latency: result.latency
            }));
          } catch(e) {}
        });
      }

    } catch(e) {
      ws.send(JSON.stringify({ type: 'error', message: e.message }));
    }
  });

  ws.on('close', () => console.log('Client disconnected'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`
  ╔════════════════════════════════╗
  ║   Hermia Server Running        ║
  ║   Translation: Render Cloud    ║
  ║   http://localhost:${PORT}         ║
  ╚════════════════════════════════╝
  `);
});
