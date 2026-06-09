// ===== TinyLink — frontend logic =====
// Talks to the Python (FastAPI) backend:
//   POST /api/shorten  { long }  -> { code, short, long }
//   GET  /{code}                 -> 302 redirect to long URL
// History list is still cached in localStorage for quick UI rendering.

// -------- 1. DOM references --------
const form        = document.querySelector('#shorten-form');
const input       = document.querySelector('#long-url');
const submitBtn   = document.querySelector('#submit-btn');
const errorEl     = document.querySelector('#form-error');
const resultCard  = document.querySelector('#result-card');
const resultLink  = document.querySelector('#result-link');
const copyBtn     = document.querySelector('#copy-btn');
const historyList = document.querySelector('#history-list');
const emptyState  = document.querySelector('#empty-state');
const clearBtn    = document.querySelector('#clear-history');

const STORAGE_KEY = 'tinylink.history';
const BASE_URL    = window.location.origin; // e.g. http://localhost:8000

// -------- 2. URL validation --------
function isValidUrl(str) {
  try {
    const u = new URL(str);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

// -------- 3. Real backend call (Python / FastAPI) --------
// POST /api/shorten with { long: "<url>" }
// Server assigns DB id, Base62-encodes it, returns { code, short, long }.
async function shorten(longUrl) {
  const res = await fetch('/api/shorten', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ long: longUrl })
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${msg || 'request failed'}`);
  }
  return res.json();
}

// -------- 4. History (localStorage) --------
function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveHistory(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function addToHistory(entry) {
  const list = loadHistory();
  list.unshift({ ...entry, at: Date.now() });
  saveHistory(list.slice(0, 20)); // keep last 20
  renderHistory();
}

function deleteFromHistory(code) {
  const list = loadHistory().filter(e => e.code !== code);
  saveHistory(list);
  renderHistory();
}

function clearHistory() {
  localStorage.removeItem(STORAGE_KEY);
  renderHistory();
}

// -------- 5. Render history list --------
function renderHistory() {
  const list = loadHistory();
  historyList.innerHTML = '';

  if (list.length === 0) {
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;

  for (const entry of list) {
    const li = document.createElement('li');
    li.className = 'history-item';
    li.innerHTML = `
      <div class="history-meta">
        <a class="history-short" href="${entry.short}" target="_blank" rel="noopener">${entry.short}</a>
        <span class="history-long" title="${entry.long}">${entry.long}</span>
      </div>
      <div class="history-actions">
        <button class="icon-btn" data-action="copy" data-short="${entry.short}" title="Copy">📋</button>
        <button class="icon-btn del" data-action="del" data-code="${entry.code}" title="Delete">✕</button>
      </div>
    `;
    historyList.appendChild(li);
  }
}

// -------- 6. Copy to clipboard --------
async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    if (btn) {
      const original = btn.textContent;
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.textContent = original;
        btn.classList.remove('copied');
      }, 1200);
    }
  } catch (err) {
    console.error('Clipboard failed', err);
  }
}

// -------- 7. Show / hide error --------
function showError(msg) {
  errorEl.textContent = msg;
  errorEl.hidden = false;
}
function clearError() {
  errorEl.textContent = '';
  errorEl.hidden = true;
}

// -------- 8. Submit handler --------
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();
  resultCard.hidden = true;

  const longUrl = input.value.trim();
  if (!isValidUrl(longUrl)) {
    showError('Please enter a valid http(s) URL.');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Shortening…';

  try {
    const data = await shorten(longUrl);
    resultLink.href = data.short;
    resultLink.textContent = data.short;
    resultCard.hidden = false;

    addToHistory(data);
    input.value = '';
  } catch (err) {
    showError('Something went wrong. Try again.');
    console.error(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Shorten';
  }
});

// -------- 9. Result copy button --------
copyBtn.addEventListener('click', () => {
  copyText(resultLink.textContent, copyBtn);
});

// -------- 10. History delegation (copy / delete) --------
historyList.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;

  if (btn.dataset.action === 'copy') {
    copyText(btn.dataset.short, btn);
  } else if (btn.dataset.action === 'del') {
    deleteFromHistory(btn.dataset.code);
  }
});

// -------- 11. Clear-all --------
clearBtn.addEventListener('click', () => {
  if (confirm('Clear all history?')) clearHistory();
});

// -------- 12. Boot --------
renderHistory();
