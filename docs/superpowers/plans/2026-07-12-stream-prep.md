# Stream Prep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `node tools/stream-prep/index.js` — one command that updates Twitch title/category, posts a chat announcement, switches Restream's YouTube source, runs the Discord/Telegram announce script, and repoints+restarts `history-facts-bot`, reporting ✅/❌ per step.

**Architecture:** Each integration lives in its own pure-logic-first module under `tools/stream-prep/lib/`, with side effects (fetch, child_process, fs, Playwright) passed as injectable params defaulting to the real implementation — this makes every module unit-testable without live credentials. `index.js` orchestrates the five steps, catching each independently, and prints a numbered ✅/❌ report. Two setup tasks (Twitch token, Restream selectors) are manual — no code to write, just instructions and a config file to fill in.

**Tech Stack:** Node.js 22 (native `fetch`, ESM, `node:test`), Playwright (`playwright` npm package), existing `python` + `D:\projects\personal_youtube\stream_announce.py` (untouched), existing `d:\history-facts-bot\index.js` (only `YOUTUBE_LIVE_ID` line is machine-edited).

**Reference:** [docs/superpowers/specs/2026-07-12-stream-prep-design.md](../specs/2026-07-12-stream-prep-design.md)

---

### Task 1: Scaffold + secrets config module

**Files:**
- Create: `tools/stream-prep/lib/config.js`
- Modify: `.gitignore` (append stream-prep secrets section)
- Test: `tests/stream-prep-config.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-config.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { readSecrets, requireSecret } from '../tools/stream-prep/lib/config.js';

test('readSecrets: throws with a clear message when file is missing', () => {
  assert.throws(
    () => readSecrets(path.join(tmpdir(), 'does-not-exist-secrets.json')),
    /Секрети не знайдено/
  );
});

test('readSecrets: parses an existing JSON file', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-'));
  const file = path.join(dir, 'secrets.json');
  writeFileSync(file, JSON.stringify({ twitchClientId: 'abc' }));
  assert.deepEqual(readSecrets(file), { twitchClientId: 'abc' });
  rmSync(dir, { recursive: true, force: true });
});

test('requireSecret: returns the value when present', () => {
  assert.equal(requireSecret({ foo: 'bar' }, 'foo'), 'bar');
});

test('requireSecret: throws naming the missing key', () => {
  assert.throws(() => requireSecret({}, 'twitchAccessToken'), /twitchAccessToken/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-config.test.js`
Expected: FAIL — `Cannot find module '../tools/stream-prep/lib/config.js'`

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/lib/config.js
import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const SECRETS_PATH = path.join(__dirname, '..', '.secrets.json');

export function readSecrets(secretsPath = SECRETS_PATH) {
  if (!existsSync(secretsPath)) {
    throw new Error(`Секрети не знайдено: ${secretsPath}. Дивись tools/stream-prep/README.md.`);
  }
  return JSON.parse(readFileSync(secretsPath, 'utf8'));
}

export function requireSecret(secrets, key) {
  const value = secrets[key];
  if (!value) {
    throw new Error(`Секрет "${key}" відсутній у .secrets.json`);
  }
  return value;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-config.test.js`
Expected: PASS (4 tests)

- [ ] **Step 5: Add gitignore entries**

Append to `.gitignore`:

```
# Stream prep secrets (contains Twitch tokens / Playwright session)
tools/stream-prep/.secrets.json
tools/stream-prep/restream-state.json
```

- [ ] **Step 6: Commit**

```bash
git add tools/stream-prep/lib/config.js tests/stream-prep-config.test.js .gitignore
git commit -m "feat: add stream-prep secrets config module"
```

---

### Task 2: YouTube ID extraction

**Files:**
- Create: `tools/stream-prep/lib/youtubeId.js`
- Test: `tests/stream-prep-youtube-id.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-youtube-id.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extractYoutubeId } from '../tools/stream-prep/lib/youtubeId.js';

test('extractYoutubeId: passes through a bare ID', () => {
  assert.equal(extractYoutubeId('5zgU5tfTlHg'), '5zgU5tfTlHg');
});

test('extractYoutubeId: extracts from youtube.com/live/<id>', () => {
  assert.equal(extractYoutubeId('https://www.youtube.com/live/5zgU5tfTlHg'), '5zgU5tfTlHg');
});

test('extractYoutubeId: extracts from studio.youtube.com livestreaming URL', () => {
  assert.equal(
    extractYoutubeId('https://studio.youtube.com/video/5zgU5tfTlHg/livestreaming'),
    '5zgU5tfTlHg'
  );
});

test('extractYoutubeId: extracts from a watch?v= URL', () => {
  assert.equal(extractYoutubeId('https://www.youtube.com/watch?v=5zgU5tfTlHg'), '5zgU5tfTlHg');
});

test('extractYoutubeId: extracts from youtu.be short link', () => {
  assert.equal(extractYoutubeId('https://youtu.be/5zgU5tfTlHg'), '5zgU5tfTlHg');
});

test('extractYoutubeId: throws on unrecognized input', () => {
  assert.throws(() => extractYoutubeId('not a youtube link'), /Не вдалось витягнути YouTube ID/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-youtube-id.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/lib/youtubeId.js
const URL_PATTERNS = [
  /youtube\.com\/live\/([\w-]{10,15})/,
  /studio\.youtube\.com\/video\/([\w-]{10,15})/,
  /youtu\.be\/([\w-]{10,15})/,
  /[?&]v=([\w-]{10,15})/,
];

export function extractYoutubeId(input) {
  const trimmed = input.trim();
  if (/^[\w-]{10,15}$/.test(trimmed)) {
    return trimmed;
  }
  for (const pattern of URL_PATTERNS) {
    const match = trimmed.match(pattern);
    if (match) return match[1];
  }
  throw new Error(`Не вдалось витягнути YouTube ID з "${input}"`);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-youtube-id.test.js`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/stream-prep/lib/youtubeId.js tests/stream-prep-youtube-id.test.js
git commit -m "feat: add YouTube ID extraction for stream-prep"
```

---

### Task 3: Twitch Helix client

**Files:**
- Create: `tools/stream-prep/lib/twitch.js`
- Test: `tests/stream-prep-twitch.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-twitch.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  getBroadcasterId,
  resolveCategoryId,
  updateChannel,
  sendAnnouncement,
} from '../tools/stream-prep/lib/twitch.js';

function fakeFetch(responses) {
  let call = 0;
  return async (url) => {
    const response = responses[call];
    call += 1;
    return {
      ok: response.status < 300,
      status: response.status,
      json: async () => response.body,
      text: async () => JSON.stringify(response.body),
    };
  };
}

test('getBroadcasterId: returns the id from the users endpoint', async () => {
  const fetchImpl = fakeFetch([{ status: 200, body: { data: [{ id: '123' }] } }]);
  const id = await getBroadcasterId({ clientId: 'cid', accessToken: 'tok', login: 'sunce_gaming', fetchImpl });
  assert.equal(id, '123');
});

test('getBroadcasterId: throws when user not found', async () => {
  const fetchImpl = fakeFetch([{ status: 200, body: { data: [] } }]);
  await assert.rejects(
    getBroadcasterId({ clientId: 'cid', accessToken: 'tok', login: 'nobody', fetchImpl }),
    /не знайдено/
  );
});

test('resolveCategoryId: matches category name case-insensitively', async () => {
  const fetchImpl = fakeFetch([
    { status: 200, body: { data: [{ id: '9', name: 'Raid: Shadow Legends' }] } },
  ]);
  const id = await resolveCategoryId({ clientId: 'cid', accessToken: 'tok', name: 'raid: shadow legends', fetchImpl });
  assert.equal(id, '9');
});

test('resolveCategoryId: throws listing candidates when no exact match', async () => {
  const fetchImpl = fakeFetch([
    { status: 200, body: { data: [{ id: '9', name: 'Raid: Shadow Legends' }] } },
  ]);
  await assert.rejects(
    resolveCategoryId({ clientId: 'cid', accessToken: 'tok', name: 'Raid Shadow', fetchImpl }),
    /Схожі: Raid: Shadow Legends/
  );
});

test('updateChannel: sends PATCH with title and game_id', async () => {
  let captured;
  const fetchImpl = async (url, opts) => {
    captured = { url, opts };
    return { ok: true, status: 204, json: async () => ({}), text: async () => '' };
  };
  await updateChannel({ clientId: 'cid', accessToken: 'tok', broadcasterId: '123', title: 'Hi', gameId: '9', fetchImpl });
  assert.match(captured.url, /broadcaster_id=123/);
  assert.equal(captured.opts.method, 'PATCH');
  assert.deepEqual(JSON.parse(captured.opts.body), { title: 'Hi', game_id: '9' });
});

test('updateChannel: throws a clear message on 401', async () => {
  const fetchImpl = fakeFetch([{ status: 401, body: {} }]);
  await assert.rejects(
    updateChannel({ clientId: 'cid', accessToken: 'tok', broadcasterId: '123', title: 'Hi', fetchImpl }),
    /токен прострочений/
  );
});

test('sendAnnouncement: posts message to the announcements endpoint', async () => {
  let captured;
  const fetchImpl = async (url, opts) => {
    captured = { url, opts };
    return { ok: true, status: 204, json: async () => ({}), text: async () => '' };
  };
  await sendAnnouncement({ clientId: 'cid', accessToken: 'tok', broadcasterId: '123', message: 'Стрім почався!', fetchImpl });
  assert.match(captured.url, /chat\/announcements\?broadcaster_id=123&moderator_id=123/);
  assert.deepEqual(JSON.parse(captured.opts.body), { message: 'Стрім почався!' });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-twitch.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/lib/twitch.js
const HELIX = 'https://api.twitch.tv/helix';
const TOKEN_EXPIRED_MESSAGE =
  'Twitch токен прострочений — згенеруй новий на twitchtokengenerator.com і онови .secrets.json';

export async function getBroadcasterId({ clientId, accessToken, login, fetchImpl = fetch }) {
  const res = await fetchImpl(`${HELIX}/users?login=${encodeURIComponent(login)}`, {
    headers: { 'Client-Id': clientId, Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`Twitch users lookup failed: ${res.status} ${await res.text()}`);
  const body = await res.json();
  if (!body.data?.length) throw new Error(`Twitch user "${login}" не знайдено`);
  return body.data[0].id;
}

export async function resolveCategoryId({ clientId, accessToken, name, fetchImpl = fetch }) {
  const res = await fetchImpl(`${HELIX}/search/categories?query=${encodeURIComponent(name)}`, {
    headers: { 'Client-Id': clientId, Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`Twitch category search failed: ${res.status} ${await res.text()}`);
  const body = await res.json();
  const match = body.data?.find((c) => c.name.toLowerCase() === name.toLowerCase());
  if (!match) {
    const candidates = (body.data || []).map((c) => c.name).join(', ') || '(нічого)';
    throw new Error(`Категорію "${name}" не знайдено. Схожі: ${candidates}`);
  }
  return match.id;
}

export async function updateChannel({ clientId, accessToken, broadcasterId, title, gameId, fetchImpl = fetch }) {
  const body = { title };
  if (gameId) body.game_id = gameId;
  const res = await fetchImpl(`${HELIX}/channels?broadcaster_id=${broadcasterId}`, {
    method: 'PATCH',
    headers: {
      'Client-Id': clientId,
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (res.status === 401) throw new Error(TOKEN_EXPIRED_MESSAGE);
  if (!res.ok) throw new Error(`Twitch channel update failed: ${res.status} ${await res.text()}`);
}

export async function sendAnnouncement({ clientId, accessToken, broadcasterId, message, fetchImpl = fetch }) {
  const res = await fetchImpl(
    `${HELIX}/chat/announcements?broadcaster_id=${broadcasterId}&moderator_id=${broadcasterId}`,
    {
      method: 'POST',
      headers: {
        'Client-Id': clientId,
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    }
  );
  if (res.status === 401) throw new Error(TOKEN_EXPIRED_MESSAGE);
  if (!res.ok) throw new Error(`Twitch announcement failed: ${res.status} ${await res.text()}`);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-twitch.test.js`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/stream-prep/lib/twitch.js tests/stream-prep-twitch.test.js
git commit -m "feat: add Twitch Helix client for stream-prep"
```

---

### Task 4: Share script wrapper

**Files:**
- Create: `tools/stream-prep/lib/share.js`
- Test: `tests/stream-prep-share.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-share.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runShareScript, parseShareOutput } from '../tools/stream-prep/lib/share.js';

test('parseShareOutput: detects a successful Discord post + Telegram text', () => {
  const stdout = [
    '✅ Стрім опубліковано в Discord: 🔴 Стрім по Raid',
    '',
    '--- Скопіюй це для Telegram (HTML): ---',
    '',
    '🔴 Наближається стрім!\n🎮 Тест\n🕒 Початок о 21:30',
  ].join('\n');
  const result = parseShareOutput(stdout, '', null);
  assert.equal(result.status, 'ok');
  assert.equal(result.discordPosted, true);
  assert.match(result.telegramText, /Наближається стрім/);
});

test('parseShareOutput: flags when RSS has not picked up the new stream yet', () => {
  const stdout = 'ℹ️ Нового стріму немає або відсутній символ 🔴 у назві.\n';
  const result = parseShareOutput(stdout, '', null);
  assert.equal(result.status, 'no-new-stream');
  assert.equal(result.discordPosted, false);
});

test('parseShareOutput: reports error when script failed and nothing posted', () => {
  const result = parseShareOutput('', 'Traceback...', new Error('exit 1'));
  assert.equal(result.status, 'error');
});

test('runShareScript: invokes python with the script path and cwd', async () => {
  let captured;
  const execFileImpl = (cmd, args, opts, cb) => {
    captured = { cmd, args, opts };
    cb(null, '✅ Стрім опубліковано в Discord: X\n--- Скопіюй це для Telegram (HTML): ---\ntext', '');
  };
  const result = await runShareScript({ execFileImpl, scriptPath: 'script.py', cwd: 'C:\\somewhere' });
  assert.equal(captured.cmd, 'python');
  assert.deepEqual(captured.args, ['script.py']);
  assert.equal(captured.opts.cwd, 'C:\\somewhere');
  assert.equal(result.discordPosted, true);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-share.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/lib/share.js
import { execFile } from 'node:child_process';

const SCRIPT_PATH = 'D:\\projects\\personal_youtube\\stream_announce.py';
const SCRIPT_CWD = 'D:\\projects\\personal_youtube';
const TELEGRAM_HEADER = '--- Скопіюй це для Telegram (HTML): ---';

export function parseShareOutput(stdout, stderr, error) {
  if (/Нового стріму немає/.test(stdout)) {
    return { status: 'no-new-stream', discordPosted: false, telegramText: null, raw: stdout };
  }
  const discordPosted = /✅ Стрім опубліковано в Discord/.test(stdout);
  const headerIndex = stdout.indexOf(TELEGRAM_HEADER);
  const telegramText = headerIndex >= 0 ? stdout.slice(headerIndex + TELEGRAM_HEADER.length).trim() : null;
  if (error && !discordPosted) {
    return { status: 'error', discordPosted: false, telegramText, raw: stdout + stderr };
  }
  return { status: discordPosted ? 'ok' : 'unknown', discordPosted, telegramText, raw: stdout };
}

export function runShareScript({ execFileImpl = execFile, scriptPath = SCRIPT_PATH, cwd = SCRIPT_CWD } = {}) {
  return new Promise((resolve) => {
    execFileImpl('python', [scriptPath], { cwd }, (error, stdout, stderr) => {
      resolve(parseShareOutput(stdout || '', stderr || '', error));
    });
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-share.test.js`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/stream-prep/lib/share.js tests/stream-prep-share.test.js
git commit -m "feat: add share-script wrapper for stream-prep"
```

---

### Task 5: history-facts-bot repoint + restart

**Files:**
- Create: `tools/stream-prep/lib/historyBot.js`
- Test: `tests/stream-prep-history-bot.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-history-bot.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import {
  updateYoutubeLiveIdInSource,
  applyYoutubeLiveId,
  killIfRunning,
  spawnBot,
  checkLogForMarkers,
  waitForBotHealthy,
} from '../tools/stream-prep/lib/historyBot.js';

test('updateYoutubeLiveIdInSource: replaces the constant value', () => {
  const source = "const YOUTUBE_LIVE_ID = '5zgU5tfTlHg'; \n// comment";
  const updated = updateYoutubeLiveIdInSource(source, 'NEWID12345');
  assert.match(updated, /const YOUTUBE_LIVE_ID = 'NEWID12345';/);
  assert.match(updated, /\/\/ comment/);
});

test('updateYoutubeLiveIdInSource: throws when the constant is missing', () => {
  assert.throws(() => updateYoutubeLiveIdInSource('no constant here', 'X'), /YOUTUBE_LIVE_ID/);
});

test('applyYoutubeLiveId: rewrites the constant in a real file', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-bot-'));
  const file = path.join(dir, 'index.js');
  writeFileSync(file, "const YOUTUBE_LIVE_ID = 'OLD'; \nconsole.log('hi');");
  applyYoutubeLiveId(file, 'NEWID');
  assert.match(readFileSync(file, 'utf8'), /const YOUTUBE_LIVE_ID = 'NEWID';/);
  rmSync(dir, { recursive: true, force: true });
});

test('killIfRunning: returns false when no pid file exists', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-bot-'));
  const pidFile = path.join(dir, 'bot.pid');
  assert.equal(killIfRunning(pidFile), false);
  rmSync(dir, { recursive: true, force: true });
});

test('killIfRunning: calls killImpl with the stored pid', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-bot-'));
  const pidFile = path.join(dir, 'bot.pid');
  writeFileSync(pidFile, '4242');
  let killedPid;
  const killed = killIfRunning(pidFile, (pid) => { killedPid = pid; });
  assert.equal(killed, true);
  assert.equal(killedPid, 4242);
  rmSync(dir, { recursive: true, force: true });
});

test('spawnBot: spawns node index.js in cwd and writes the pid file', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-bot-'));
  const logFilePath = path.join(dir, 'bot.log');
  const pidFilePath = path.join(dir, 'bot.pid');
  let captured;
  const spawnImpl = (cmd, args, opts) => {
    captured = { cmd, args, opts };
    return { pid: 999, unref() {} };
  };
  const pid = spawnBot({ cwd: dir, logFilePath, pidFilePath, spawnImpl });
  assert.equal(pid, 999);
  assert.equal(captured.cmd, 'node');
  assert.deepEqual(captured.args, ['index.js']);
  assert.equal(captured.opts.cwd, dir);
  assert.equal(captured.opts.detached, true);
  assert.equal(readFileSync(pidFilePath, 'utf8'), '999');
  rmSync(dir, { recursive: true, force: true });
});

test('checkLogForMarkers: reports found/missing markers and a failure line', () => {
  const log = '✅ Успішно підключено до Streamlabs WebSocket!\n❌ Помилка YouTube чату: boom\n';
  const result = checkLogForMarkers(log, ['✅ Успішно підключено до Streamlabs WebSocket!', '✅ Підключено до YouTube live чату!']);
  assert.equal(result.allFound, false);
  assert.deepEqual(result.missing, ['✅ Підключено до YouTube live чату!']);
  assert.match(result.failureLine, /Помилка YouTube чату/);
});

test('checkLogForMarkers: allFound true when every marker present', () => {
  const log = 'A\nB\n';
  const result = checkLogForMarkers(log, ['A', 'B']);
  assert.equal(result.allFound, true);
});

test('waitForBotHealthy: resolves as soon as markers appear, without waiting full timeout', async () => {
  let call = 0;
  const readFileImpl = () => {
    call += 1;
    return call < 3 ? 'nothing yet' : 'A\nB\n';
  };
  const sleepImpl = async () => {};
  const result = await waitForBotHealthy('unused.log', ['A', 'B'], { timeoutMs: 5000, readFileImpl, sleepImpl });
  assert.equal(result.allFound, true);
  assert.equal(call, 3);
});

test('waitForBotHealthy: gives up after timeout and reports what is missing', async () => {
  const readFileImpl = () => 'nothing here';
  let sleeps = 0;
  const sleepImpl = async () => { sleeps += 1; };
  const result = await waitForBotHealthy('unused.log', ['A'], { timeoutMs: 3, intervalMs: 1, readFileImpl, sleepImpl });
  assert.equal(result.allFound, false);
  assert.ok(sleeps > 0);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-history-bot.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/lib/historyBot.js
import { readFileSync, writeFileSync, existsSync, openSync } from 'node:fs';
import { spawn } from 'node:child_process';

const YOUTUBE_LIVE_ID_PATTERN = /const YOUTUBE_LIVE_ID = '[^']*';/;

export function updateYoutubeLiveIdInSource(sourceText, newId) {
  if (!YOUTUBE_LIVE_ID_PATTERN.test(sourceText)) {
    throw new Error('YOUTUBE_LIVE_ID constant не знайдено в index.js');
  }
  return sourceText.replace(YOUTUBE_LIVE_ID_PATTERN, `const YOUTUBE_LIVE_ID = '${newId}';`);
}

export function applyYoutubeLiveId(filePath, newId) {
  const source = readFileSync(filePath, 'utf8');
  writeFileSync(filePath, updateYoutubeLiveIdInSource(source, newId), 'utf8');
}

export function killIfRunning(pidFilePath, killImpl = process.kill) {
  if (!existsSync(pidFilePath)) return false;
  const pid = Number(readFileSync(pidFilePath, 'utf8').trim());
  if (!pid) return false;
  try {
    killImpl(pid);
    return true;
  } catch {
    return false;
  }
}

export function spawnBot({ cwd, logFilePath, pidFilePath, spawnImpl = spawn }) {
  const logFd = openSync(logFilePath, 'a');
  const child = spawnImpl('node', ['index.js'], { cwd, detached: true, stdio: ['ignore', logFd, logFd] });
  child.unref();
  writeFileSync(pidFilePath, String(child.pid), 'utf8');
  return child.pid;
}

export function checkLogForMarkers(logText, requiredMarkers) {
  const failureLine = logText.split('\n').find((line) => line.includes('❌')) || null;
  const found = requiredMarkers.filter((marker) => logText.includes(marker));
  const missing = requiredMarkers.filter((marker) => !logText.includes(marker));
  return { allFound: missing.length === 0, found, missing, failureLine };
}

export async function waitForBotHealthy(
  logFilePath,
  requiredMarkers,
  { timeoutMs = 15000, intervalMs = 500, readFileImpl = readFileSync, sleepImpl = (ms) => new Promise((r) => setTimeout(r, ms)) } = {}
) {
  const deadline = Date.now() + timeoutMs;
  let last = { allFound: false, found: [], missing: requiredMarkers, failureLine: null };
  do {
    let text = '';
    try {
      text = readFileImpl(logFilePath, 'utf8');
    } catch {
      text = '';
    }
    last = checkLogForMarkers(text, requiredMarkers);
    if (last.allFound) return last;
    await sleepImpl(intervalMs);
  } while (Date.now() < deadline);
  return last;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-history-bot.test.js`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/stream-prep/lib/historyBot.js tests/stream-prep-history-bot.test.js
git commit -m "feat: add history-facts-bot repoint/restart/health-check for stream-prep"
```

---

### Task 6: Restream selectors + Playwright skeleton

**Files:**
- Create: `tools/stream-prep/lib/restream.js`
- Modify: `package.json` (add `playwright` dependency)
- Test: `tests/stream-prep-restream.test.js`

Note: `switchRestreamSource` itself drives a real logged-in browser session against the live restream.io dashboard — that can't be meaningfully unit-tested (no fake server to assert against). Only `loadRestreamSelectors` (pure config validation) is unit-tested here; `switchRestreamSource` gets exercised for real in Task 9 once selectors exist.

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-restream.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { loadRestreamSelectors } from '../tools/stream-prep/lib/restream.js';

test('loadRestreamSelectors: returns parsed selectors when all required keys exist', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-restream-'));
  const file = path.join(dir, 'selectors.json');
  writeFileSync(file, JSON.stringify({
    sourcePickerButton: '#picker',
    streamOptionTemplate: '[data-video-id="{{id}}"]',
    twitchChatConnectedIndicator: '.twitch-connected',
    youtubeChatConnectedIndicator: '.youtube-connected',
  }));
  const selectors = loadRestreamSelectors(file);
  assert.equal(selectors.sourcePickerButton, '#picker');
  rmSync(dir, { recursive: true, force: true });
});

test('loadRestreamSelectors: throws naming the first missing required key', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'stream-prep-restream-'));
  const file = path.join(dir, 'selectors.json');
  writeFileSync(file, JSON.stringify({ sourcePickerButton: '#picker' }));
  assert.throws(() => loadRestreamSelectors(file), /streamOptionTemplate/);
  rmSync(dir, { recursive: true, force: true });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-restream.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Add the playwright dependency**

Edit `package.json`, add a `dependencies` block:

```json
{
  "name": "raid-twitch-extension",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "test": "node --test tests/*.test.js"
  },
  "dependencies": {
    "playwright": "^1.61.0"
  }
}
```

Run: `npm install`

- [ ] **Step 4: Write minimal implementation**

```javascript
// tools/stream-prep/lib/restream.js
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';

const REQUIRED_SELECTOR_KEYS = [
  'sourcePickerButton',
  'streamOptionTemplate',
  'twitchChatConnectedIndicator',
  'youtubeChatConnectedIndicator',
];

export function loadRestreamSelectors(selectorsPath) {
  const raw = JSON.parse(readFileSync(selectorsPath, 'utf8'));
  for (const key of REQUIRED_SELECTOR_KEYS) {
    if (!raw[key]) throw new Error(`restream-selectors.json: відсутній ключ "${key}"`);
  }
  return raw;
}

export async function switchRestreamSource({
  youtubeId,
  selectorsPath,
  storageStatePath,
  dashboardUrl = 'https://restream.io/dashboard',
  launchImpl = chromium.launch,
}) {
  const selectors = loadRestreamSelectors(selectorsPath);
  const browser = await launchImpl({ headless: true });
  try {
    const context = await browser.newContext({ storageState: storageStatePath });
    const page = await context.newPage();
    await page.goto(dashboardUrl);
    await page.click(selectors.sourcePickerButton);
    await page.click(selectors.streamOptionTemplate.replace('{{id}}', youtubeId));
    await page.waitForSelector(selectors.twitchChatConnectedIndicator, { timeout: 15000 });
    await page.waitForSelector(selectors.youtubeChatConnectedIndicator, { timeout: 15000 });
  } finally {
    await browser.close();
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test tests/stream-prep-restream.test.js`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add tools/stream-prep/lib/restream.js tests/stream-prep-restream.test.js package.json package-lock.json
git commit -m "feat: add Restream dashboard automation skeleton"
```

---

### Task 7: Orchestrator CLI

**Files:**
- Create: `tools/stream-prep/index.js`
- Test: `tests/stream-prep-index.test.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/stream-prep-index.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, runStep, formatReport } from '../tools/stream-prep/index.js';

test('parseArgs: requires --youtube and --title', () => {
  assert.throws(() => parseArgs(['--title', 'x']), /--youtube/);
  assert.throws(() => parseArgs(['--youtube', 'x']), /--title/);
});

test('parseArgs: defaults category and picks up all flags', () => {
  const args = parseArgs(['--youtube', 'abc', '--title', 'T', '--announce', 'A', '--category', 'C']);
  assert.deepEqual(args, { youtube: 'abc', title: 'T', announce: 'A', category: 'C' });
});

test('parseArgs: uses the default category when not given', () => {
  const args = parseArgs(['--youtube', 'abc', '--title', 'T']);
  assert.equal(args.category, 'Raid: Shadow Legends');
});

test('runStep: wraps a successful async function as ok:true with its detail', async () => {
  const result = await runStep('demo', async () => 'done');
  assert.deepEqual(result, { name: 'demo', ok: true, detail: 'done' });
});

test('runStep: wraps a thrown error as ok:false with the error message', async () => {
  const result = await runStep('demo', async () => { throw new Error('boom'); });
  assert.deepEqual(result, { name: 'demo', ok: false, detail: 'boom' });
});

test('formatReport: numbers steps and marks ok/fail with icons', () => {
  const report = formatReport([
    { name: 'A', ok: true, detail: 'fine' },
    { name: 'B', ok: false, detail: 'broke' },
  ]);
  assert.equal(report, '1. ✅ A\n   fine\n2. ❌ B\n   broke');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/stream-prep-index.test.js`
Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```javascript
// tools/stream-prep/index.js
import path from 'node:path';
import { readSecrets, requireSecret } from './lib/config.js';
import { extractYoutubeId } from './lib/youtubeId.js';
import { getBroadcasterId, resolveCategoryId, updateChannel, sendAnnouncement } from './lib/twitch.js';
import { runShareScript } from './lib/share.js';
import { applyYoutubeLiveId, killIfRunning, spawnBot, waitForBotHealthy } from './lib/historyBot.js';
import { switchRestreamSource } from './lib/restream.js';

const DEFAULT_CATEGORY = 'Raid: Shadow Legends';
const BROADCASTER_LOGIN = 'sunce_gaming';
const HISTORY_BOT_DIR = 'd:\\history-facts-bot';
const HISTORY_BOT_INDEX = path.join(HISTORY_BOT_DIR, 'index.js');
const HISTORY_BOT_PID = path.join(HISTORY_BOT_DIR, 'stream-prep.pid');
const HISTORY_BOT_LOG = path.join(HISTORY_BOT_DIR, 'stream-prep.log');
const HISTORY_BOT_MARKERS = [
  '✅ Успішно підключено до Streamlabs WebSocket!',
  '✅ Підключено до YouTube live чату!',
];
const RESTREAM_SELECTORS = path.join(import.meta.dirname, 'restream-selectors.json');
const RESTREAM_STATE = path.join(import.meta.dirname, 'restream-state.json');

export function parseArgs(argv) {
  const args = { category: DEFAULT_CATEGORY };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    if (flag === '--youtube') args.youtube = argv[(i += 1)];
    else if (flag === '--title') args.title = argv[(i += 1)];
    else if (flag === '--announce') args.announce = argv[(i += 1)];
    else if (flag === '--category') args.category = argv[(i += 1)];
  }
  if (!args.youtube) throw new Error('--youtube обов’язковий');
  if (!args.title) throw new Error('--title обов’язковий');
  return args;
}

export async function runStep(name, fn) {
  try {
    const detail = await fn();
    return { name, ok: true, detail: detail ?? null };
  } catch (error) {
    return { name, ok: false, detail: error.message };
  }
}

export function formatReport(results) {
  return results
    .map((r, i) => {
      const icon = r.ok ? '✅' : '❌';
      const detail = r.detail ? `\n   ${String(r.detail).replace(/\n/g, '\n   ')}` : '';
      return `${i + 1}. ${icon} ${r.name}${detail}`;
    })
    .join('\n');
}

export async function runStreamPrep(argv) {
  const args = parseArgs(argv);
  const youtubeId = extractYoutubeId(args.youtube);
  const secrets = readSecrets();
  const clientId = requireSecret(secrets, 'twitchClientId');
  const accessToken = requireSecret(secrets, 'twitchAccessToken');

  const results = [];

  results.push(
    await runStep('Twitch: title/category', async () => {
      const broadcasterId = await getBroadcasterId({ clientId, accessToken, login: BROADCASTER_LOGIN });
      const gameId = await resolveCategoryId({ clientId, accessToken, name: args.category });
      await updateChannel({ clientId, accessToken, broadcasterId, title: args.title, gameId });
      return `title="${args.title}", category="${args.category}"`;
    })
  );

  if (args.announce) {
    results.push(
      await runStep('Twitch: announcement', async () => {
        const broadcasterId = await getBroadcasterId({ clientId, accessToken, login: BROADCASTER_LOGIN });
        await sendAnnouncement({ clientId, accessToken, broadcasterId, message: args.announce });
        return args.announce;
      })
    );
  }

  results.push(
    await runStep('Restream: switch source', async () => {
      await switchRestreamSource({ youtubeId, selectorsPath: RESTREAM_SELECTORS, storageStatePath: RESTREAM_STATE });
      return `youtube id ${youtubeId} обрано, чат підключено на обох платформах`;
    })
  );

  results.push(
    await runStep('Share: Discord/Telegram', async () => {
      const result = await runShareScript();
      if (result.status === 'no-new-stream') {
        throw new Error('RSS ще не підхопив новий стрім — перезапусти stream_announce.py вручну через хвилину');
      }
      return result.telegramText
        ? `Discord: ok. Telegram (встав вручну):\n${result.telegramText}`
        : 'Discord: ok';
    })
  );

  results.push(
    await runStep('history-facts-bot: repoint + restart', async () => {
      applyYoutubeLiveId(HISTORY_BOT_INDEX, youtubeId);
      killIfRunning(HISTORY_BOT_PID);
      spawnBot({ cwd: HISTORY_BOT_DIR, logFilePath: HISTORY_BOT_LOG, pidFilePath: HISTORY_BOT_PID });
      const health = await waitForBotHealthy(HISTORY_BOT_LOG, HISTORY_BOT_MARKERS);
      if (!health.allFound) {
        const tail = health.failureLine ? ` | ${health.failureLine}` : '';
        throw new Error(`Не підключились: ${health.missing.join(', ')}${tail}`);
      }
      return 'Twitch + YouTube чат підключені';
    })
  );

  return results;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runStreamPrep(process.argv.slice(2))
    .then((results) => {
      console.log(formatReport(results));
      process.exit(results.some((r) => !r.ok) ? 1 : 0);
    })
    .catch((error) => {
      console.error(`Фатальна помилка: ${error.message}`);
      process.exit(1);
    });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/stream-prep-index.test.js`
Expected: PASS (6 tests)

- [ ] **Step 5: Run the full test suite**

Run: `npm test`
Expected: PASS — all suites including the pre-existing hero-card/data/effects-list/utils tests plus the seven new `stream-prep-*` files.

- [ ] **Step 6: Commit**

```bash
git add tools/stream-prep/index.js tests/stream-prep-index.test.js
git commit -m "feat: add stream-prep orchestrator CLI"
```

---

### Task 8: Manual setup — Twitch token

This task has no code — it produces the `.secrets.json` file the CLI reads (Task 1's `readSecrets`).

- [ ] **Step 1:** Open https://twitchtokengenerator.com/, choose **Bot Chat Token** (custom scopes), and select scopes:
  - `channel:manage:broadcast`
  - `moderator:manage:announcements`

  (Do not reuse the existing chat-only token from `history-facts-bot/index.js` — that one only has `chat:read`/`chat:edit`.)

- [ ] **Step 2:** Generate the token. Note the **Client ID** and **Access Token** shown on the page.

- [ ] **Step 3:** Create `tools/stream-prep/.secrets.json` (already gitignored from Task 1):

```json
{
  "twitchClientId": "<paste Client ID>",
  "twitchAccessToken": "<paste Access Token>"
}
```

- [ ] **Step 4:** Sanity-check the token works:

```bash
node -e "
import('./tools/stream-prep/lib/twitch.js').then(async ({ getBroadcasterId }) => {
  const secrets = JSON.parse(require('fs').readFileSync('tools/stream-prep/.secrets.json', 'utf8'));
  const id = await getBroadcasterId({ clientId: secrets.twitchClientId, accessToken: secrets.twitchAccessToken, login: 'sunce_gaming' });
  console.log('broadcaster id:', id);
});
"
```
Expected: prints a numeric broadcaster id, no error.

- [ ] **Step 5:** Note the token's expiry shown by twitchtokengenerator.com (commonly a few hours to ~60 days depending on scopes). If `updateChannel`/`sendAnnouncement` ever throw the "токен прострочений" message, repeat Steps 1-3 to mint a fresh one — there is no auto-refresh (no confirmed client secret available from the token generator to implement it safely).

---

### Task 9: Manual setup — Restream selectors + session

This task has no application code — it produces `tools/stream-prep/restream-selectors.json` (consumed by Task 6's `loadRestreamSelectors`) and `tools/stream-prep/restream-state.json` (the saved login session).

- [ ] **Step 1:** Capture a logged-in session once:

```bash
npx playwright codegen --save-storage=tools/stream-prep/restream-state.json https://restream.io/login
```

Log into restream.io in the opened browser window, then close the codegen window once logged in — `restream-state.json` now holds the session cookies.

- [ ] **Step 2:** Re-open the dashboard with the saved session to find the real selectors:

```bash
npx playwright codegen --load-storage=tools/stream-prep/restream-state.json https://restream.io/dashboard
```

Click through: open the YouTube-source picker, pick a different stream from the list, and locate the chat-connected indicators for both Twitch and YouTube. Codegen prints the selector for each click in its inspector panel — copy those.

- [ ] **Step 3:** Fill in `tools/stream-prep/restream-selectors.json` (already gitignored from Task 1) using the selectors found above. `streamOptionTemplate` must contain the literal placeholder `{{id}}` where the YouTube video ID goes in whichever attribute/text Restream uses to distinguish stream entries in the list:

```json
{
  "sourcePickerButton": "<selector for the button/element that opens the YouTube source picker>",
  "streamOptionTemplate": "<selector containing {{id}} for a specific stream entry>",
  "twitchChatConnectedIndicator": "<selector for Twitch's chat-connected indicator>",
  "youtubeChatConnectedIndicator": "<selector for YouTube's chat-connected indicator>"
}
```

- [ ] **Step 4:** Dry-run the real automation against an actual past/test stream ID to confirm the selectors work end-to-end:

```bash
node -e "
import('./tools/stream-prep/lib/restream.js').then(({ switchRestreamSource }) =>
  switchRestreamSource({
    youtubeId: 'PUT_A_REAL_RECENT_ID_HERE',
    selectorsPath: 'tools/stream-prep/restream-selectors.json',
    storageStatePath: 'tools/stream-prep/restream-state.json',
  }).then(() => console.log('OK')).catch((e) => console.error('FAILED:', e.message))
);
"
```
Expected: `OK`, and the Restream dashboard visibly shows the picked stream selected with both chat indicators connected. If a selector was wrong, Playwright's error names which `waitForSelector`/`click` timed out — fix that key in `restream-selectors.json` and rerun.

---

### Task 10: End-to-end verification + docs

**Files:**
- Create: `tools/stream-prep/README.md`

- [ ] **Step 1:** Write a short README so future-you doesn't have to re-derive the setup:

```markdown
# stream-prep

One command to run right after creating the YouTube stream.

## Usage

    node tools/stream-prep/index.js --youtube <url|id> --title "Заголовок" [--announce "Текст в чат"] [--category "Гра"]

`--category` defaults to `Raid: Shadow Legends`.

## One-time setup

1. `.secrets.json` — Twitch Client ID + access token (scopes `channel:manage:broadcast`,
   `moderator:manage:announcements`) from twitchtokengenerator.com. See plan Task 8.
2. `restream-state.json` + `restream-selectors.json` — Playwright login session +
   dashboard selectors. See plan Task 9. Re-run Task 9 Step 1 if Restream ever logs
   the session out.

Both secret files are gitignored — regenerate them locally, never commit them.

## Known limitations

- If YouTube's RSS feed hasn't caught up yet, the "Share" step reports failure with
  instructions to rerun `stream_announce.py` (in `D:\projects\personal_youtube`)
  manually after a minute.
- The Twitch token has no auto-refresh; regenerate it when the CLI reports it expired.
```

- [ ] **Step 2:** Run a real dry run before the next actual stream (with a genuine but already-over YouTube live ID, a harmless test title, and no `--announce` to avoid pinging chat):

```bash
node tools/stream-prep/index.js --youtube <a real recent id> --title "test — ignore"
```

Confirm the printed report shows ✅ for Twitch title/category, Restream switch, and history-facts-bot restart. Fix whichever step is ❌ before relying on this for a real stream.

- [ ] **Step 3: Commit**

```bash
git add tools/stream-prep/README.md
git commit -m "docs: add stream-prep README"
```
