// Global state
let currentJobId = null;
let pollInterval = null;
let currentResult = null;
let selectedFile = null;

// DOM Elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsDrawer = document.getElementById('settingsDrawer');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const modelSelect = document.getElementById('modelSelect');
const sourceLangSelect = document.getElementById('sourceLangSelect');
const geminiKeyInput = document.getElementById('geminiKey');

const quickSourceLang = document.getElementById('quickSourceLang');
const quickUrlSourceLang = document.getElementById('quickUrlSourceLang');

// Synchronize language dropdowns
function syncLang(val) {
  if (sourceLangSelect) sourceLangSelect.value = val;
  if (quickSourceLang) quickSourceLang.value = val;
  if (quickUrlSourceLang) quickUrlSourceLang.value = val;
}
[sourceLangSelect, quickSourceLang, quickUrlSourceLang].forEach(el => {
  if (el) el.addEventListener('change', (e) => syncLang(e.target.value));
});

const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

const dropZone = document.getElementById('dropZone');
const videoFileInput = document.getElementById('videoFileInput');
const selectedFileInfo = document.getElementById('selectedFileInfo');
const selectedFileName = document.getElementById('selectedFileName');
const selectedFileSize = document.getElementById('selectedFileSize');
const startUploadBtn = document.getElementById('startUploadBtn');

const instaUrlInput = document.getElementById('instaUrlInput');
const startUrlBtn = document.getElementById('startUrlBtn');

const progressCard = document.getElementById('progressCard');
const progressTitle = document.getElementById('progressTitle');
const progressStatus = document.getElementById('progressStatus');
const progressBar = document.getElementById('progressBar');

const stepIngest = document.getElementById('stepIngest');
const stepExtract = document.getElementById('stepExtract');
const stepTranscribe = document.getElementById('stepTranscribe');
const stepTranslate = document.getElementById('stepTranslate');
const stepReady = document.getElementById('stepReady');

const resultsSection = document.getElementById('resultsSection');
const videoPlayer = document.getElementById('videoPlayer');
const detectedLangBadge = document.getElementById('detectedLangBadge');
const metaDuration = document.getElementById('metaDuration');
const metaSegments = document.getElementById('metaSegments');
const metaConfidence = document.getElementById('metaConfidence');

const viewTabs = document.querySelectorAll('.view-tab');
const viewPanes = document.querySelectorAll('.view-pane');

const hindiFullText = document.getElementById('hindiFullText');
const originalFullText = document.getElementById('originalFullText');
const sideHindiText = document.getElementById('sideHindiText');
const sideOriginalText = document.getElementById('sideOriginalText');
const segmentsList = document.getElementById('segmentsList');

const copyBtn = document.getElementById('copyBtn');
const ttsBtn = document.getElementById('ttsBtn');
const exportSrtHindi = document.getElementById('exportSrtHindi');
const exportTxt = document.getElementById('exportTxt');
const exportJson = document.getElementById('exportJson');
const toast = document.getElementById('toast');

// Settings Drawer Toggle
settingsBtn.addEventListener('click', () => {
  settingsDrawer.classList.toggle('hidden');
});
closeSettingsBtn.addEventListener('click', () => {
  settingsDrawer.classList.add('hidden');
});

// Tab Switcher (Upload vs URL)
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    const targetTab = document.getElementById(btn.dataset.tab);
    if (targetTab) targetTab.classList.add('active');
  });
});

// Drop Zone Handlers
dropZone.addEventListener('click', () => videoFileInput.click());

['dragenter', 'dragover'].forEach(eventName => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('drag-over');
  });
});

['dragleave', 'drop'].forEach(eventName => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
  });
});

dropZone.addEventListener('drop', (e) => {
  const dt = e.dataTransfer;
  const files = dt.files;
  if (files && files.length > 0) {
    handleFileSelected(files[0]);
  }
});

videoFileInput.addEventListener('change', (e) => {
  if (e.target.files && e.target.files.length > 0) {
    handleFileSelected(e.target.files[0]);
  }
});

function handleFileSelected(file) {
  if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|mov|webm|mkv)$/i)) {
    showToast('Please select a valid video file (.mp4, .mov, .webm, .mkv)', 'error');
    return;
  }
  selectedFile = file;
  selectedFileName.textContent = file.name;
  selectedFileSize.textContent = `(${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
  selectedFileInfo.classList.remove('hidden');
  startUploadBtn.disabled = false;
}

// Start File Upload
startUploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('model_size', modelSelect.value);
  formData.append('source_lang', sourceLangSelect.value);
  if (geminiKeyInput.value.trim()) {
    formData.append('gemini_api_key', geminiKeyInput.value.trim());
  }

  showProgressCard('Uploading video file...');
  startUploadBtn.disabled = true;

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await res.json();
    currentJobId = data.job_id;
    startPollingStatus(currentJobId);
  } catch (err) {
    showToast(err.message, 'error');
    hideProgressCard();
    startUploadBtn.disabled = false;
  }
});

// Start URL Fetching
startUrlBtn.addEventListener('click', async () => {
  const url = instaUrlInput.value.trim();
  if (!url) {
    showToast('Please enter an Instagram Reel or video URL', 'error');
    return;
  }

  showProgressCard('Fetching Instagram Reel...');
  startUrlBtn.disabled = true;

  try {
    const res = await fetch('/api/process-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: url,
        model_size: modelSelect.value,
        source_lang: sourceLangSelect.value,
        gemini_api_key: geminiKeyInput.value.trim() || null
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit URL');
    }

    const data = await res.json();
    currentJobId = data.job_id;
    startPollingStatus(currentJobId);
  } catch (err) {
    showToast(err.message, 'error');
    hideProgressCard();
    startUrlBtn.disabled = false;
  }
});

// Polling Pipeline Status
function startPollingStatus(jobId) {
  if (pollInterval) clearInterval(pollInterval);

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      if (!res.ok) throw new Error('Status check failed');

      const data = await res.json();
      updateProgressUI(data);

      if (data.status === 'completed') {
        clearInterval(pollInterval);
        currentResult = data.result;
        renderResults(data.result);
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        showToast(data.message, 'error');
        hideProgressCard();
        startUploadBtn.disabled = false;
        startUrlBtn.disabled = false;
      }
    } catch (err) {
      console.error(err);
    }
  }, 1200);
}

function updateProgressUI(data) {
  progressBar.style.width = `${Math.max(data.progress || 5, 5)}%`;
  progressStatus.textContent = data.message || 'Processing...';

  // Reset steps
  [stepIngest, stepExtract, stepTranscribe, stepTranslate, stepReady].forEach(s => {
    s.classList.remove('active', 'done');
  });

  const p = data.progress || 0;
  if (p >= 15) stepIngest.classList.add('done');
  else if (p > 0) stepIngest.classList.add('active');

  if (p >= 35) stepExtract.classList.add('done');
  else if (p > 15) stepExtract.classList.add('active');

  if (p >= 60) stepTranscribe.classList.add('done');
  else if (p > 35) stepTranscribe.classList.add('active');

  if (p >= 85) stepTranslate.classList.add('done');
  else if (p > 60) stepTranslate.classList.add('active');

  if (p >= 100) stepReady.classList.add('done');
}

function showProgressCard(initialMessage) {
  progressCard.classList.remove('hidden');
  resultsSection.classList.add('hidden');
  progressStatus.textContent = initialMessage;
  progressBar.style.width = '5%';
  progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideProgressCard() {
  progressCard.classList.add('hidden');
}

// Render Results
function renderResults(result) {
  hideProgressCard();
  resultsSection.classList.remove('hidden');

  // Video
  videoPlayer.src = `/api/video/${result.job_id}`;
  videoPlayer.load();

  // Meta Badges
  detectedLangBadge.textContent = `Language: ${result.language.toUpperCase()}`;
  metaDuration.textContent = formatDuration(result.duration);
  metaSegments.textContent = result.segments.length;
  metaConfidence.textContent = `${Math.round(result.language_probability * 100)}%`;

  // 1. Hindi Full Text
  hindiFullText.textContent = result.hindi_full_text || 'No speech detected.';

  // 2. Original Full Text
  originalFullText.textContent = result.original_full_text || 'No speech detected.';

  // 3. Side-by-Side
  sideHindiText.textContent = result.hindi_full_text || '';
  sideOriginalText.textContent = result.original_full_text || '';

  // 4. Segments List
  segmentsList.innerHTML = '';
  result.segments.forEach(seg => {
    const item = document.createElement('div');
    item.className = 'segment-item';
    item.innerHTML = `
      <div class="segment-time">
        <i class="fa-regular fa-clock"></i> ${formatTime(seg.start)} - ${formatTime(seg.end)}
      </div>
      <div class="segment-hindi">${escapeHtml(seg.hindi_text || seg.text)}</div>
      <div class="segment-orig">${escapeHtml(seg.text)}</div>
    `;
    // Click segment to seek video
    item.addEventListener('click', () => {
      videoPlayer.currentTime = seg.start;
      videoPlayer.play();
    });
    segmentsList.appendChild(item);
  });

  // Re-enable buttons
  startUploadBtn.disabled = false;
  startUrlBtn.disabled = false;

  showToast('Hindi transcription complete! 🎉', 'success');
  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// View Tabs (Hindi vs Side-by-Side vs Segments vs Original)
viewTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    viewTabs.forEach(t => t.classList.remove('active'));
    viewPanes.forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    const view = tab.dataset.view;
    if (view === 'hindi') document.getElementById('viewHindi').classList.add('active');
    else if (view === 'sidebyside') document.getElementById('viewSideBySide').classList.add('active');
    else if (view === 'segments') document.getElementById('viewSegments').classList.add('active');
    else if (view === 'original') document.getElementById('viewOriginal').classList.add('active');
  });
});

// Copy Hindi Text
copyBtn.addEventListener('click', () => {
  if (!currentResult || !currentResult.hindi_full_text) {
    showToast('No text available to copy', 'error');
    return;
  }
  navigator.clipboard.writeText(currentResult.hindi_full_text)
    .then(() => showToast('Hindi text copied to clipboard! 📋', 'success'))
    .catch(() => showToast('Failed to copy text', 'error'));
});

// Text to Speech (Hindi Readout)
ttsBtn.addEventListener('click', () => {
  if (!currentResult || !currentResult.hindi_full_text) {
    showToast('No Hindi text available to play', 'error');
    return;
  }

  if (!('speechSynthesis' in window)) {
    showToast('Text-to-speech not supported in this browser', 'error');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(currentResult.hindi_full_text);
  utterance.lang = 'hi-IN';
  utterance.rate = 0.95;

  // Try to find a Hindi voice
  const voices = window.speechSynthesis.getVoices();
  const hindiVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('HI'));
  if (hindiVoice) utterance.voice = hindiVoice;

  window.speechSynthesis.speak(utterance);
  showToast('Playing Hindi voice readout... 🔊', 'info');
});

// Export Handlers
exportSrtHindi.addEventListener('click', () => {
  if (!currentJobId) return;
  window.open(`/api/export/${currentJobId}?format=srt&field=hindi`, '_blank');
});

exportTxt.addEventListener('click', () => {
  if (!currentJobId) return;
  window.open(`/api/export/${currentJobId}?format=txt&field=hindi`, '_blank');
});

exportJson.addEventListener('click', () => {
  if (!currentJobId) return;
  window.open(`/api/export/${currentJobId}?format=json`, '_blank');
});

// Helpers
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function formatDuration(seconds) {
  return formatTime(seconds || 0);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, type = 'info') {
  toast.textContent = message;
  toast.classList.remove('hidden');
  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3500);
}

