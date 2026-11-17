const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const API = '';
const OFFICIAL_DICTIONARY = 'https://divyangjan.depwd.gov.in/islrtc/';

const vocabulary = [
  {word:'Hello', hindi:'नमस्ते', category:'Greetings'},
  {word:'Thank you', hindi:'धन्यवाद', category:'Greetings'},
  {word:'Sorry', hindi:'माफ़ कीजिए', category:'Conversation'},
  {word:'Please', hindi:'कृपया', category:'Conversation'},
  {word:'Help', hindi:'मदद', category:'Everyday'},
  {word:'Water', hindi:'पानी', category:'Everyday'},
  {word:'Food', hindi:'खाना', category:'Everyday'},
  {word:'Home', hindi:'घर', category:'Places'},
  {word:'School', hindi:'विद्यालय', category:'Places'},
  {word:'Friend', hindi:'दोस्त', category:'People'},
  {word:'Family', hindi:'परिवार', category:'People'},
  {word:'Good', hindi:'अच्छा', category:'Descriptions'},
  {word:'Bad', hindi:'बुरा', category:'Descriptions'},
  {word:'Yes', hindi:'हाँ', category:'Responses'},
  {word:'No', hindi:'नहीं', category:'Responses'},
  {word:'Name', hindi:'नाम', category:'Conversation'},
  {word:'Today', hindi:'आज', category:'Time'},
  {word:'Tomorrow', hindi:'कल', category:'Time'},
  {word:'Understand', hindi:'समझना', category:'Conversation'},
  {word:'Learn', hindi:'सीखना', category:'Education'}
];
let modelConfig = null;
let mediaStream = null;
let ws = null;
let frameTimer = null;
let sentenceWords = [];
let lastPrediction = '';
let lastPredictionAt = 0;
let questionSet = [];
let questionIndex = 0;
let score = 0;
let answered = false;
let currentPage = 'home';
let toastTimer = null;

function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function go(page) {
  if (!$('#page-' + page)) return;
  if (currentPage === 'translate' && page !== 'translate') stopCamera(true);
  currentPage = page;
  $$('.page').forEach(el => el.classList.toggle('active', el.id === 'page-' + page));
  $$('.nav-item[data-page]').forEach(el => el.classList.toggle('active', el.dataset.page === page));
  const labels = {home:'Overview',translate:'Live translation',learn:'Learn ISL',practice:'Practice',history:'History',about:'About & feedback'};
  $('#crumb-label').textContent = labels[page] || 'SanketSetu';
  if (page === 'history') loadHistory();
  if (page === 'home') updateStats();
  window.scrollTo({top:0,behavior:'smooth'});
}

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    headers: {'Content-Type':'application/json', ...(options.headers || {})},
    ...options
  });
  let body = {};
  try { body = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(body.detail || body.message || body.error || `Request failed (${response.status})`);
  return body;
}

async function loadConfig() {
  try {
    modelConfig = await api('/api/config');
    const pill = $('#model-pill');
    if (modelConfig.model_configured) {
      const online = modelConfig.model?.status === 'online';
      pill.classList.toggle('online', online);
      pill.classList.toggle('offline', !online);
      pill.innerHTML = `<span class="status-dot"></span><span>${online ? 'Model service online' : 'Model endpoint configured · checking'}</span>`;
      $('#model-warning').hidden = online;
      if (!online) {
        $('#model-warning').innerHTML = `<strong>Model service could not be reached</strong><p>${escapeHtml(modelConfig.model?.message || 'Check the configured service URL and start the model server.')}</p>`;
      }
    } else {
      pill.classList.add('offline');
      pill.innerHTML = '<span class="status-dot"></span><span>AI model not connected</span>';
    }
  } catch (error) {
    $('#model-pill').classList.add('offline');
    $('#model-pill').innerHTML = '<span class="status-dot"></span><span>Backend unavailable</span>';
    console.warn('Backend status:', error);
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function renderVocabulary(query = '') {
  const filtered = vocabulary.filter(item => `${item.word} ${item.hindi} ${item.category}`.toLowerCase().includes(query.toLowerCase().trim()));
  $('#vocab-grid').innerHTML = filtered.length ? filtered.map((item, index) => `
    <article class="vocab-card">
      <span class="vocab-id">${String(index + 1).padStart(2,'0')} / ${escapeHtml(item.category.toUpperCase())}</span>
      <h3>${escapeHtml(item.word)}</h3><p>${escapeHtml(item.hindi)}</p>
      <a href="${OFFICIAL_DICTIONARY}" target="_blank" rel="noreferrer">Find video sign ↗</a>
    </article>`).join('') : '<div class="empty-state"><strong>No matching words</strong><p>Try another word or meaning.</p></div>';
}

async function loadResources() {
  const fallback = [
    {title:'Official ISL Dictionary',description:'Video signs with English and Hindi equivalents.',url:OFFICIAL_DICTIONARY,source:'ISLRTC'},
    {title:'ISLRTC',description:'Indian Sign Language Research and Training Centre.',url:'https://islrtc.nic.in/',source:'Government of India'},
    {title:'DIKSHA',description:'Education resources including ISL learning material.',url:'https://diksha.gov.in/',source:'Ministry of Education'},
    {title:'ISLRTC YouTube',description:'Official video learning resources.',url:'https://www.youtube.com/@islrtcnewdelhi4069',source:'ISLRTC'}
  ];
  let resources = fallback;
  try { resources = (await api('/api/resources')).resources; } catch (_) {}
  $('#resource-list').innerHTML = resources.map(item => `<div class="resource-item"><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.description)}</p></div><a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">Open resource ↗</a></div>`).join('');
}

async function updateStats() {
  try {
    const history = await api('/api/history?limit=200');
    $('#stat-count').textContent = history.items.length;
    $('#stat-words').textContent = vocabulary.length;
  } catch (_) {
    $('#stat-count').textContent = '—';
    $('#stat-words').textContent = vocabulary.length;
  }
}

function setCameraState(text, active = false) {
  $('#camera-state').textContent = text.toUpperCase();
  $('#camera-state').classList.toggle('active', active);
}

async function enableCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast('Camera access requires HTTPS or localhost in a supported browser.');
    return;
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:640},height:{ideal:480}},audio:false});
    const video = $('#camera-video');
    video.srcObject = mediaStream;
    await video.play();
    $('#camera-stage').classList.add('is-live');
    $('#camera-placeholder').hidden = true;
    $('#camera-start').disabled = true;
    $('#stream-toggle').disabled = false;
    $('#camera-stop').disabled = false;
    setCameraState('Camera ready', true);
    $('#camera-overlay-text').textContent = 'CAMERA READY';
    toast('Camera ready. Start recognition when you are prepared.');
  } catch (error) {
    setCameraState('Camera unavailable');
    toast(error.name === 'NotAllowedError' ? 'Camera permission was denied.' : `Could not open camera: ${error.message}`);
  }
}

function connectSocket() {
  return new Promise((resolve, reject) => {
    if (ws && ws.readyState === WebSocket.OPEN) return resolve(true);
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${scheme}//${location.host}/ws/translate`);
    ws.binaryType = 'arraybuffer';
    const timeout = setTimeout(() => reject(new Error('WebSocket connection timed out.')), 8000);
    ws.onopen = () => {};
    ws.onmessage = event => {
      if (typeof event.data !== 'string') return;
      let message;
      try { message = JSON.parse(event.data); } catch (_) { return; }
      if (message.type === 'ready') {
        clearTimeout(timeout);
        if (!message.model_configured) showModelUnavailable(message.message || 'No model endpoint configured.');
        else if (!message.landmarks_enabled) {
          $('#model-warning').hidden = false;
          $('#model-warning').innerHTML = `<strong>Landmark processing is disabled</strong><p>${escapeHtml(message.landmark_status || 'Install MediaPipe and its task assets for the expected preprocessing path.')}</p>`;
        }
        resolve(true);
      } else if (message.type === 'prediction') {
        showPrediction(message);
      } else if (message.type === 'model_unavailable') {
        showModelUnavailable(message.message);
      } else if (message.type === 'model_error' || message.type === 'error') {
        $('#prediction-description').textContent = message.message || 'The model service returned an error.';
        $('#prediction-label').textContent = 'MODEL ERROR';
      } else if (message.type === 'stream_status') {
        $('#camera-overlay-text').textContent = `STREAMING · ${message.frames_received} FRAMES`;
      }
    };
    ws.onerror = () => { clearTimeout(timeout); reject(new Error('Cannot connect to the SanketSetu backend.')); };
    ws.onclose = () => {
      if (frameTimer) { clearInterval(frameTimer); frameTimer = null; }
    };
  });
}

function showModelUnavailable(message) {
  $('#model-warning').hidden = false;
  $('#model-warning').innerHTML = `<strong>AI inference is not connected</strong><p>${escapeHtml(message || 'Set GEMINI_API_KEY for experimental Gemini vision or MODEL_API_BASE_URL for a dedicated ISL model. No prediction has been generated.')}</p>`;
  $('#prediction-label').textContent = 'WAITING FOR MODEL';
  $('#prediction-description').textContent = 'The camera stream is running, but no AI provider is configured.';
}

function showPrediction(result) {
  const label = String(result.label || '').trim();
  if (!label) return;
  $('#prediction-label').textContent = 'MODEL PREDICTION';
  $('#prediction-text').textContent = label.replaceAll('_',' ');
  const confidence = Number(result.confidence);
  if (Number.isFinite(confidence)) {
    const percent = `${Math.round(Math.max(0,Math.min(1,confidence))*100)}%`;
    $('#confidence-value').textContent = percent;
    $('#confidence-bar').style.width = percent;
  } else {
    $('#confidence-value').textContent = 'Not supplied';
    $('#confidence-bar').style.width = '0%';
  }
  $('#prediction-description').textContent = `Live model result · ${result.latency_ms ? `${result.latency_ms} ms` : 'latency not reported'} · ${result.model || 'Configured ISL model'}`;
  const now = Date.now();
  if (label.toLowerCase() !== lastPrediction.toLowerCase() || now - lastPredictionAt > 2500) {
    appendWord(label.replaceAll('_',' '));
    lastPrediction = label; lastPredictionAt = now;
  }
  $('#model-warning').hidden = true;
  $('#model-pill').classList.add('online');
  $('#model-pill').classList.remove('offline');
  $('#model-pill').innerHTML = '<span class="status-dot"></span><span>Model returning predictions</span>';
}

function frameLoop() {
  const video = $('#camera-video');
  const canvas = $('#camera-canvas');
  const context = canvas.getContext('2d', {alpha:false});
  frameTimer = setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN || video.readyState < 2 || !video.videoWidth) return;
    const targetW = 480;
    const ratio = video.videoHeight / video.videoWidth;
    canvas.width = targetW;
    canvas.height = Math.max(1, Math.round(targetW * ratio));
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async blob => {
      if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return;
      try { ws.send(await blob.arrayBuffer()); } catch (error) { console.warn('Frame send failed', error); }
    }, 'image/jpeg', 0.78);
  }, 220);
}

async function toggleRecognition() {
  const button = $('#stream-toggle');
  if (frameTimer) {
    clearInterval(frameTimer); frameTimer = null;
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({type:'stop'}));
    button.textContent = 'Start recognition';
    $('#rec-indicator').classList.remove('active');
    $('#camera-overlay-text').textContent = 'CAMERA READY';
    setCameraState('Camera ready', true);
    return;
  }
  button.disabled = true;
  try {
    await connectSocket();
    frameLoop();
    button.textContent = 'Pause recognition';
    $('#rec-indicator').classList.add('active');
    $('#camera-overlay-text').textContent = 'STREAMING';
    setCameraState('Streaming', true);
  } catch (error) {
    toast(error.message);
    setCameraState('Connection failed');
  } finally { button.disabled = false; }
}

function stopCamera(closeTracks = false) {
  if (frameTimer) { clearInterval(frameTimer); frameTimer = null; }
  if (ws) { try { ws.send(JSON.stringify({type:'stop'})); ws.close(); } catch (_) {} ws = null; }
  $('#stream-toggle').textContent = 'Start recognition';
  $('#rec-indicator').classList.remove('active');
  if (closeTracks) {
    mediaStream?.getTracks().forEach(track => track.stop());
    mediaStream = null;
    $('#camera-video').srcObject = null;
    $('#camera-stage').classList.remove('is-live');
    $('#camera-placeholder').hidden = false;
    $('#camera-start').disabled = false;
    $('#stream-toggle').disabled = true;
    $('#camera-stop').disabled = true;
    setCameraState('Not started');
    $('#camera-overlay-text').textContent = 'PREVIEW OFF';
  } else if (mediaStream) {
    setCameraState('Camera ready', true);
  }
}

function renderSentence() {
  const text = sentenceWords.join(' ');
  $('#sentence-editor').value = text;
  $('#sentence-output').textContent = text || 'Your recognised words will collect here. You can edit the sentence before speaking or saving it.';
  $('#word-count').textContent = `${text.trim() ? text.trim().split(/\s+/).length : 0} WORDS`;
}
function appendWord(word) {
  const clean = String(word).trim();
  if (!clean) return;
  const last = sentenceWords[sentenceWords.length - 1];
  if (last?.toLowerCase() !== clean.toLowerCase()) sentenceWords.push(clean);
  renderSentence();
}
function currentSentence() {
  return $('#sentence-editor').value.trim() || sentenceWords.join(' ').trim();
}

async function saveSentence(source = 'live') {
  const text = currentSentence();
  if (!text) return toast('There is no message to save yet.');
  const result = await api('/api/history', {method:'POST', body:JSON.stringify({text, confidence:null, source})});
  toast(`Saved: ${result.text}`);
  await loadHistory(); await updateStats();
}

async function loadHistory() {
  try {
    const {items} = await api('/api/history?limit=200');
    $('#history-total').textContent = `${items.length} ITEMS`;
    $('#history-list').innerHTML = items.length ? items.map(item => `
      <div class="history-item"><div><strong>${escapeHtml(item.text)}</strong><small>${new Date(item.created_at).toLocaleString()} · ${escapeHtml(item.source || 'live')}</small></div>
      <div class="history-actions"><span class="history-confidence">${item.confidence == null ? 'Confidence not stored' : `${Math.round(item.confidence*100)}% confidence`}</span><button class="delete-link" data-delete-history="${item.id}">Delete</button></div></div>`).join('') : '<div class="empty-state"><strong>No saved messages yet</strong><p>Recognise a word, build a sentence and save it to see it here.</p></div>';
    $('#history-list').querySelectorAll('[data-delete-history]').forEach(btn => btn.addEventListener('click', async () => {
      try { await api(`/api/history/${btn.dataset.deleteHistory}`, {method:'DELETE'}); await loadHistory(); await updateStats(); toast('History item deleted.'); }
      catch (error) { toast(error.message); }
    }));
  } catch (error) {
    $('#history-list').innerHTML = `<div class="empty-state"><strong>History is unavailable</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
}

function startPractice() {
  const shuffled = [...vocabulary].sort(() => Math.random() - .5);
  questionSet = shuffled.slice(0,5);
  questionIndex = 0; score = 0; answered = false;
  renderQuestion();
}
function renderQuestion() {
  const item = questionSet[questionIndex];
  if (!item) return;
  $('#practice-step').textContent = `QUESTION ${String(questionIndex+1).padStart(2,'0')} / ${questionSet.length}`;
  $('#practice-score').textContent = `SCORE ${score}`;
  $('#practice-prompt').textContent = item.hindi;
  $('#practice-hint').textContent = 'Choose the English word that matches this Hindi meaning.';
  $('#practice-feedback').textContent = '';
  $('#practice-feedback').className = 'practice-feedback';
  $('#practice-next').disabled = true;
  $('#practice-next').textContent = questionIndex === questionSet.length - 1 ? 'Finish round →' : 'Next question →';
  answered = false;
  const distractors = vocabulary.filter(x => x.word !== item.word).sort(() => Math.random() - .5).slice(0,3);
  const choices = [...distractors,item].sort(() => Math.random() - .5);
  $('#answer-grid').innerHTML = choices.map(choice => `<button class="answer-option" data-answer="${escapeHtml(choice.word)}">${escapeHtml(choice.word)}</button>`).join('');
  $('#answer-grid').querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => chooseAnswer(btn, item.word)));
}
function chooseAnswer(button, correct) {
  if (answered) return;
  answered = true;
  const selected = button.dataset.answer;
  const right = selected === correct;
  if (right) score++;
  $$('#answer-grid button').forEach(btn => {
    btn.disabled = true;
    if (btn.dataset.answer === correct) btn.classList.add('correct');
    else if (btn === button) btn.classList.add('wrong');
  });
  $('#practice-score').textContent = `SCORE ${score}`;
  $('#practice-feedback').textContent = right ? 'Correct. Nice work.' : `Not quite — the matching word is “${correct}”. Check the official sign dictionary to learn its sign.`;
  $('#practice-feedback').classList.add(right ? 'good' : 'bad');
  $('#practice-next').disabled = false;
}


function buildPhraseLookup() {
  const raw = $('#phrase-input').value.trim();
  const target = $('#phrase-results');
  target.innerHTML = '';
  if (!raw) return toast('Enter a phrase first.');
  const tokens = [...new Set(raw.split(/\s+/).map(word => word.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '')).filter(Boolean))].slice(0,12);
  if (!tokens.length) return toast('No searchable words were found.');
  const note = document.createElement('p');
  note.className = 'phrase-note';
  note.textContent = 'Each link opens the official dictionary list for the word’s first letter. Search for the exact word there and select its video entry. This is a dictionary shortcut, not an automatic text-to-sign translation.';
  target.append(note);
  tokens.forEach(word => {
    const token = document.createElement('span');
    token.className = 'phrase-token';
    const label = document.createElement('span');
    label.textContent = word;
    const link = document.createElement('a');
    const first = word.match(/^\p{L}/u)?.[0] || '';
    link.href = first && /^[a-z]$/i.test(first)
      ? `https://divyangjan.depwd.gov.in/islrtc/listpage.php?type=${encodeURIComponent(first.toLowerCase())}`
      : OFFICIAL_DICTIONARY;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = 'Open list ↗';
    token.append(label, link);
    target.append(token);
  });
}

function bindEvents() {
  $$('.nav-item[data-page]').forEach(btn => btn.addEventListener('click', () => go(btn.dataset.page)));
  $$('[data-go]').forEach(btn => btn.addEventListener('click', () => go(btn.dataset.go)));
  $('#camera-start').addEventListener('click', enableCamera);
  $('#stream-toggle').addEventListener('click', toggleRecognition);
  $('#camera-stop').addEventListener('click', () => stopCamera(true));
  $('#sample-preview-btn').addEventListener('click', () => {
    $('#prediction-label').textContent = 'SIMULATED SAMPLE · NOT AI';
    $('#prediction-text').textContent = 'Thank you';
    $('#confidence-value').textContent = 'Not applicable';
    $('#confidence-bar').style.width = '0%';
    $('#prediction-description').textContent = 'Illustrative UI sample only. No gesture was analysed and no model prediction was generated.';
    appendWord('Thank you');
    $('#sentence-note').textContent = 'This sample is simulated. Do not report it as an AI recognition result.';
    toast('Demo-only sample displayed — no AI inference.');
  });
  $('#sentence-editor').addEventListener('input', event => {
    sentenceWords = event.target.value.trim() ? event.target.value.trim().split(/\s+/) : [];
    $('#sentence-output').textContent = event.target.value || 'Your recognised words will collect here.';
    $('#word-count').textContent = `${sentenceWords.length} WORDS`;
  });
  $('#speak-btn').addEventListener('click', () => {
    const text = currentSentence();
    if (!text) return toast('Add a message before speaking.');
    if (!('speechSynthesis' in window)) return toast('Speech output is not supported in this browser.');
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-IN'; utterance.rate = 0.9;
    speechSynthesis.speak(utterance);
  });
  $('#copy-btn').addEventListener('click', async () => {
    const text = currentSentence();
    if (!text) return toast('There is no message to copy.');
    try { await navigator.clipboard.writeText(text); toast('Message copied.'); }
    catch (_) { $('#sentence-editor').style.display = 'block'; $('#sentence-editor').select(); toast('Select the message and copy it.'); }
  });
  $('#save-btn').addEventListener('click', () => saveSentence().catch(error => toast(error.message)));
  $('#clear-btn').addEventListener('click', () => { sentenceWords=[]; renderSentence(); $('#sentence-note').textContent='Message cleared.'; });
  $('#vocab-search').addEventListener('input', event => renderVocabulary(event.target.value));
  $('#phrase-lookup-btn').addEventListener('click', buildPhraseLookup);
  $('#practice-restart').addEventListener('click', startPractice);
  $('#practice-next').addEventListener('click', () => {
    if (questionIndex < questionSet.length - 1) { questionIndex++; renderQuestion(); }
    else {
      $('#practice-prompt').textContent = `${score} / ${questionSet.length}`;
      $('#practice-hint').textContent = 'Round complete. Review any unfamiliar words in the official dictionary.';
      $('#answer-grid').innerHTML = '';
      $('#practice-feedback').textContent = 'You completed the vocabulary recall round.';
      $('#practice-next').disabled = true;
      $('#practice-next').textContent = 'Round complete';
    }
  });
  $('#clear-history-btn').addEventListener('click', async () => {
    if (!confirm('Delete all locally saved translation history?')) return;
    try { await api('/api/history', {method:'DELETE'}); await loadHistory(); await updateStats(); toast('All history cleared.'); }
    catch (error) { toast(error.message); }
  });
  $('#feedback-form').addEventListener('submit', async event => {
    event.preventDefault();
    const status = $('#feedback-status'); status.textContent = 'Submitting…';
    try {
      await api('/api/feedback', {method:'POST',body:JSON.stringify({rating:Number($('#feedback-rating').value),message:$('#feedback-message').value})});
      status.textContent = 'Thank you. Your feedback has been saved locally.';
      $('#feedback-message').value = '';
    } catch (error) { status.textContent = error.message; }
  });
  $('#accessibility-btn').addEventListener('click', () => { $('#accessibility-popover').hidden = !$('#accessibility-popover').hidden; });
  $('#close-accessibility').addEventListener('click', () => { $('#accessibility-popover').hidden = true; });
  $('#contrast-toggle').addEventListener('change', event => document.body.classList.toggle('high-contrast', event.target.checked));
  $('#text-toggle').addEventListener('change', event => document.body.classList.toggle('large-text', event.target.checked));
  window.addEventListener('beforeunload', () => stopCamera(true));
}

async function init() {
  bindEvents();
  renderSentence();
  renderVocabulary();
  startPractice();
  await Promise.all([loadConfig(), loadResources(), updateStats()]);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
}

document.addEventListener('DOMContentLoaded', init);
