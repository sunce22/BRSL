# RSL Hero Guide — Backlog & Security Issues

_Last updated: 2026-05-29_

> **Repo split:**
> - 🌐 **PUBLIC** → `twitch-extension` (GitHub) — source code, UI, docs
> - 🔒 **PRIVATE** → `twitch-extension-private` (GitLab/GitHub private) — `data/`, `tools/`, `i18n/heroes-uk.json`, `cf-feedback-worker/`

---

## Security Issues

### Done ✓
- [x] Rate limiting logic added to worker.js (5 req/IP/min via KV) `🔒`
- [x] CORS restricted to twitch.tv + localhost + OBS local files `🌐`
- [x] source param type validation added `🔒`
- [x] Unescaped `data-effect` / `data-hero-id` — fixed with `escapeHtml()` `🌐`

---

## Feature Backlog

### Streamer / OBS `🌐`

- [x] **Гостьове OBS посилання** — `obs/obs-guest.html`

- [ ] **OBS watermark / copyright** `🌐` — small, unobtrusive branding visible on stream
  (streamer name, extension name, or logo). Hidden from crop zone or shown in overlay corner.

- [x] **OBS: hero image** `🔒+🌐` — портрети 140×182px. URL в `heroes.json` (🔒), логіка відображення в `hero-card.js` (🌐).

- [x] **OBS: ∞ pin-режим за замовчуванням** `🌐`

- [x] **OBS: пошук українською (с = C key конфлікт)** `🌐`

- [x] **Картка героя виходить за краї при відкритому меню** `🌐` — fixed: calc(100vh - 72px) в obs.css

### Panel / Twitch Extension `🌐`

- [ ] **Прибрати donate-посилання з Twitch Panel** `🌐` — залишити тільки Discord/Twitch/YouTube.

- [ ] **Test feedback form in production Twitch extension context** `🔒+🌐`
  Twitch extension iframe has a strict CSP. Confirm that `fetch()` to the CF Worker
  (`*.workers.dev`) is not blocked. If it is, add the Worker domain to the extension's
  allowlist in the Twitch Developer Console.

- [ ] **Розмістити як опублікований Twitch Extension** `🌐`
  Кроки:
  1. **Twitch Developer Console** — зареєструвати новий extension на https://dev.twitch.tv/console/extensions
     - Тип: Panel
     - Назва, опис, категорія (Gaming Tools / Raid Shadow Legends)
  2. **Hosting** — Twitch вимагає HTTPS CDN для файлів extension. Варіанти:
     - Cloudflare Pages (безкоштовно, git deploy) — рекомендовано
     - GitHub Pages — теж варіант
  3. **CSP (Content Security Policy)** — у Twitch Developer Console додати до allowlist:
     - `hellhades.com` — портрети героїв
     - `ayumilove.net` — fallback портрети
     - `*.workers.dev` — CF Worker для feedback
  4. **Перевірити fetch() до CF Worker** — Twitch iframe може блокувати запити до `*.workers.dev`; якщо так — додати домен у extension allowlist
  5. **manifest.json** — заповнити: version, description, icon (640×480 та 320×240), screenshots
  6. **Review submission** — Twitch перевіряє extension вручну (зазвичай 3-7 днів)
     - Вимоги: немає зовнішніх JS бібліотек без whitelist, HTTPS скрізь, no tracking
  7. **Після approve** — активувати на каналі, протестувати в production iframe

- [x] **Приватний backup repo для data/tools** `🔒`
  ✅ Створено локально: `d:\projects\twitch-extension-private\` (initial commit).
  Залишилось: додати remote і push.
  Створити **private** repo на GitHub/GitLab і:
  ```bash
  cd d:\projects\twitch-extension-private   # або окрема папка
  git init
  git remote add origin git@github.com:YOU/twitch-extension-private.git
  # скопіювати data/, tools/, i18n/heroes-uk.json
  git add . && git commit -m "initial private data"
  git push -u origin main
  ```
  Вміст: `data/heroes.json`, `data/skill-multipliers.*`, `i18n/heroes-uk.json`, `tools/` (всі extraction scripts).
  Доступ: тільки ти.

- [ ] **Юридичний захист та монетизація**

  **Захист авторства (зробити до публічного релізу):**
  - [ ] Domain + сервіси (CF Worker, hosting) — зареєстровані особисто, не на третіх осіб
  - [ ] Перший публічний реліз зафіксувати (GitHub release + дата) — доказ авторства
  - [ ] Git-історія вже є — головний доказ

  **Юридичні документи (потрібні для Twitch review):**
  - [ ] Privacy Policy — обов'язково для Twitch Extension (якщо збираєш дані feedback)
  - [ ] Terms of Service — описує обмеження відповідальності, дані гри Plarium
  - [ ] Disclaimer — "unoffical fan tool, not affiliated with Plarium"
  - Хостити на домені проекту або GitHub Pages

  **Монетизація (MVP спочатку, потім):**
  - [ ] Запустити MVP без реєстрації ТМ — дивитись на traction
  - [ ] Donate (Donatello/Patreon) — для OBS/сайт (не Twitch Panel — порушує TOS)
  - [ ] Підписка — OBS PRO features, серверна перевірка ключів
  - [ ] Якщо є traction → реєстрація ТМ, юридичне оформлення

  **Потенційні ризики:**
  - Twitch відхилить extension → без Privacy Policy або через зовнішні посилання
  - Plarium може: попросити змінити назву / прибрати контент (рідко, але готуватись)
  - Піратство OBS tool → захист: серверна перевірка ліцензійного ключа, підписка замість одноразової оплати
  - Закритий core-код для PRO — не віддавати всю логіку клієнту

### Data `🔒`

- [ ] **Re-run scraper to refresh hero data** `🔒`
  `node tools/scrape-ayumilove.mjs` — picks up newly released heroes.

- [ ] **Add Epic heroes** `🔒` — scraper currently filters to Legendary + Mythical only.

### Content & Data

- [ ] **Зображення героїв** `🔒` — локальні текстури гри → `data/portraits/`.

- [ ] **Зображення ефектів** `🔒` — scraping hellhades/ayumilove або CDN Plarium.

- [ ] **Множники навичок** `🔒` — `data/skill-multipliers.json`, проблема з іменами героїв.

- [ ] **Взаємодія з гайдами по героям** `🌐` — швидкий доступ під час стріму.

- [ ] **Посилання на гайди з картки героя** `🌐` — кнопка на картці → hellhades/ayumilove.

- [ ] **Додавання нових героїв вручну** `🔒+🌐` — механізм для героїв ще не в базі.

- [x] **Оновити описи ефектів** `🌐` — оновлено з hellhades.com.

- [x] **Переклад інтерфейсу українською** `🌐+🔒` — UI (🌐), hero/skill тексти (🔒 heroes-uk.json).

- [x] **Поповнити UA переклади навичок** `🔒` — ✅ **407/407 (100%)**. Pipeline: `read-static-data.py` → `build-heroes-uk.py`.
  Оновлення: гра запущена → `python tools/read-static-data.py` → `python tools/build-heroes-uk.py`.

- [x] **UA: fix &#39; entities** — `sanitize()` більше не HTML-екранує апострофи в JSON. Виправлено 392 значення в heroes-uk.json.

- [x] **Пошук UA: панель зникала при введенні 'кс'** — три окремі баги: (1) IME focus loss при partial DOM update → додано `input.focus()`; (2) race condition між `loadTranslations()` await та введенням → guard `isTranslationsLoaded()`; (3) Ukrainian 'с' = C key закривала OBS панель → guard `if (activeElement.tagName === 'INPUT') return`.

- [ ] **UA: аури не перекладені** — навички-аури (Aura, Passive) мають описи `l10n:skill/description?id=N` що можуть бути відсутні в rslSim.dat (немає static-ключа). Перевірити і знайти l10n ключ для aura-навичок.

- [ ] **UA: гіперпосилання на ефекти в описах** — `highlightDescription()` в `effect-descriptions.js` шукає `[EffectName]` в квадратних дужках (англійські назви). В UA текстах ефекти загорнені в `<color>` теги гри, не в квадратні дужки. Потрібно: або розширити `highlightDescription()` щоб розпізнавала UA назви ефектів, або зберігати `[UA назва]` разом з `<color>` тегами при парсингу rslSim.dat.

- [ ] **UA: 9 героїв без перекладу** — автоматична транслітерація не знайшла відповідності (UA назва — переклад, не транслітерація EN). Потрібне ручне зіставлення або розширення транслітератора.
  **Список (UA назва → EN назва в heroes.json):**
  - Ксілок Лазуровий → Xiloco the Encrusted
  - Фімо Чабан → Phemo the Shepherd
  - Носон Бикоборець → Knosson the Bronze Bull
  - Берд Широкоплечий → Baerd the Broad
  - Фісба Закаменіла → ? (невідомо)
  - Сінда Неопалима → Cinda Forgeheart
  - Сайдакс Царевбивця → Sydax King Killer
  - Одержимий Владика демонів → ? (невідомо, можливо Xena Warrior Princess або ін.)
  - Ронда → Ronda
  - Також у heroes.json без перекладу: Aleksandr the Sharpshooter, Xena Warrior Princess

### UX

- [ ] **Автоматичне відображення картки** — розпізнавати героя на екрані (через OCR або screen capture) і автоматично показувати його картку при виборі у грі. Потребує дослідження: window capture API, OBS source, або screen reader.

- [x] **Panel: remember last open tab** — `localStorage` persists Heroes/Effects tab choice.
- [x] **Panel: back button in hero detail** — "← Back" button collapses hero card.
- [x] **OBS: keyboard shortcut D** — dismisses hero card overlay without closing control panel.
- [x] **Guest OBS: panel auto-hide/show** — ховається при показі картки, повертається при dismiss.

---

## Done ✓

- [x] Panel scroll fix (flex `min-height: 0`)
- [x] HTML entity decoding in scraped descriptions
- [x] Effects tab in panel and OBS
- [x] Inline effect links in skill descriptions
- [x] Effect descriptions popup
- [x] No-limit (pin) timer toggle in OBS
- [x] Skill-by-skill tab navigation in OBS hero card
- [x] Card overlay anchored top-right, below toggle button
- [x] Block Revive / Necrosis / Perfect Veil effects added
- [x] True Fear / Poison / Weaken descriptions corrected
- [x] Support button with Discord / Twitch / YouTube links
- [x] Donatello donate link
- [x] Feedback form (panel + OBS) → Cloudflare Worker → Discord webhook
- [x] Discord webhook URL moved server-side (CF Worker secret, not in source)
