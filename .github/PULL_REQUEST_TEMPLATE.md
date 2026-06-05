## What changed

Brief description of the change.

---

## Checklist

- [ ] Task from TODO.md — which one: **[task name]**
- [ ] Changes limited to ONE task
- [ ] Tests pass: `node --test tests/*.test.js`
- [ ] Code style preserved (no new comments, escapeHtml on all innerHTML)

---

## Safety checks (if syncing to RSL-Buddy)

- [ ] No `data/heroes.json` or any file from `data/`
- [ ] No `i18n/heroes-uk.json` or `i18n/ui-uk.json`
- [ ] No files from `tools/`
- [ ] No `.claude/` files
- [ ] No `tests/` files
- [ ] No `docs/superpowers/` files
- [ ] No `obs/obs-guest.*` files
- [ ] No `cf-feedback-worker/` files
- [ ] No API keys, tokens, or secrets in any file

---

## Ready to sync to RSL-Buddy?

- [ ] Yes — only panel/, obs/, shared/, extension/ changes (safe to copy)
- [ ] No — contains private data/config (stay in BRSL only)
