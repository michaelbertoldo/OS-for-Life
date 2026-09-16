# LifeOS Progress

**Current phase:** 1 · **Last updated:** 2026-09-16

Key: `[ ]` to do · `[x]` done · `[~]` partially done (see note) · `BLOCKED` · **you** = Michael · **cc** = Claude Code
Rule for cc: update this file after every task. Stop at each gate until Michael confirms.

---

## Phase 0: Foundation

- [x] **P0-01 cc** Ask the 3 blocking questions (vault path, macOS, Canvas URL). Record answers in Decisions. — 2026-09-16: answered via AskUserQuestion.
- [x] **P0-02 cc** Scaffold the repo: `uv`, pyproject, src layout, pytest, typer CLI stubs, `.gitignore`. Move the prompt to `docs/SPEC.md`. Write a short repo `CLAUDE.md` with a Lessons section. — 2026-09-16: done; git repo initialized (not yet committed).
- [x] **P0-03 cc** Config loader, plus an example `~/.config/lifeos/config.toml`. — 2026-09-16: `lifeos.config`; example written to `~/.config/lifeos/config.toml`.
- [x] **P0-04 cc** Keychain helper and `lifeos secret set` (no echo). — 2026-09-16: `lifeos.secrets`, service "lifeos".
- [x] **P0-05 cc** Item model, routing, and scoring, including the 4 required test cases. — 2026-09-16: `tests/test_scoring.py` (4/4), `tests/test_routing.py`.
- [x] **P0-06 cc** Vault writer: field-ownership merge, reconcile, `done_at` cleanup, snooze reset. Tests. — 2026-09-16: `lifeos.engine.vault`, `tests/test_vault.py`.
- [x] **P0-07 cc** `state.json`, logging (no secrets or content), `sync-status.md` writer. — 2026-09-16: `lifeos.engine.state`, `lifeos.logging_setup`, `lifeos.engine.sync_status`.
- [x] **P0-08 cc** `lifeos doctor`: config, paths, auth status, secret scan. — 2026-09-16: `lifeos.doctor`; `tests/test_doctor.py`.
- [x] **P0-09 cc** Scaffold the vault: folders, 6 placeholder tab notes, templates, `habits.md`, `about-me.md` stub, `CLAUDE.md`, and an `AGENTS.md` symlink. Never overwrite existing files. — 2026-09-16: `lifeos.scaffold`; vault created at `~/LifeOS`.
- [x] **P0-10 you** Open the vault in Obsidian. Enable the Bases and Templates core plugins. Turn on FileVault if it's off. — 2026-09-16: confirmed by Michael.
- [x] **P0-11 cc** Fixture source and a test Base. Verify property types render and sort correctly. — 2026-09-16: `lifeos.collectors.fixture`, `00 Home/Fixture Test.base` written; `--dry-run` showed 5 sample items to Michael before the real write; 5 items now live in `90 Sync/`.
- [x] **GATE 0** pytest green (23/23 ✓) · doctor passes (✓, exit 0) · fixture items visible in Obsidian · **Michael confirmed 2026-09-16**

---

## Phase 1: School, calendars, habits

**Canvas**
- [ ] **P1-01 you** Create a Canvas access token (Account → Settings → New Access Token), then run `lifeos secret set canvas_token`. — steps sent to Michael 2026-09-16, waiting.
- [x] **P1-02 cc** Canvas collector: planner items, missing submissions, unread announcements and conversations (student enrollments only). Fixtures and tests. — 2026-09-16: `lifeos.collectors.canvas`, `tests/test_canvas.py` (4 tests, all via `httpx.MockTransport`, no network). Field names verified against developerdocs.instructure.com for planner items / missing submissions / enrollment grades; announcement and conversation field names follow stable convention but weren't independently re-verified this session (see Decisions) — the first real `--dry-run` against Michael's token is the checkpoint.
- [x] **P1-03 cc** Teaching course routed to mentors: events and due dates only, no student data. — 2026-09-16: `_collect_teaching_course_items` in canvas.py pulls only `calendar_events` and `assignments` (id/name/due_at), no roster/submission endpoints touched.
- [x] **P1-04 cc** Canvas grades written to course notes (`letter: hidden` when totals are hidden). — 2026-09-16: `lifeos.engine.course_notes`, wired into `lifeos sync` via `GRADE_COLLECTORS`.
- [ ] **BLOCKED on P1-01** Can't run `lifeos sync --source canvas` for real or confirm the announcement/conversation field names against live data until Michael's token exists.

**Learning Suite**
- [ ] **P1-05 you** For each Learning Suite course: Schedule → Get iCalendar Feed → run `lifeos secret set ls_feed:<COURSE>`. Add the course names to config. — steps sent to Michael 2026-09-16, waiting.
- [ ] **P1-06 cc** Fetch the feeds, show Michael the distinct event titles, and agree on the assignment/exam filter. — blocked on P1-05.
- [ ] **P1-07 cc** Learning Suite collector (due at 00:00, marked done manually), plus Learning Suite course notes with empty grade fields. — blocked on P1-06.

**Calendars and the BYU consent test**
- [ ] **P1-08 you** Create the Google Cloud project, enable the Calendar and Gmail APIs, create a Desktop OAuth client, and set publishing status to In production. Run `lifeos auth google --account <name>` for each account. — steps sent to Michael 2026-09-16, waiting.
- [ ] **P1-09 cc** Google Calendar collector, with `gcal_exclude` for calendars that duplicate Learning Suite. — blocked on P1-08 for the auth flow / real testing.
- [ ] **P1-10 you** Create an Apple app-specific password and store it in Keychain. List the iCloud-native calendars in config. — steps sent to Michael 2026-09-16, waiting.
- [ ] **P1-11 cc** iCloud CalDAV collector, plus UID dedupe across all calendar sources. — blocked on P1-10 for real testing.
- [ ] **P1-12 you + cc** cc gives the steps for the Entra app registration and builds `lifeos auth outlook`. Michael runs it for **personal** and **byu**. Record **Path A** (consent works) or **Path B** (admin approval required) for BYU in Decisions. — cc's steps not sent yet.

**Dashboard**
- [x] **P1-13 cc** `Today.md` and `School.md` Bases views, per spec §8. Verify the Bases docs first. — 2026-09-16: `lifeos.bases`, `Today.base` (Agenda/Top 7/Habits), `School.base` (Due in 14 days/Missing/Grades/Announcements). Docs fetched live (help.obsidian.md/bases) before writing, same `sort`-key caveat as the Decisions log.
- [x] **P1-14 cc** Habits: daily note creation, the 7-day grid on Today, streaks. — 2026-09-16: `lifeos.engine.habits`; wired into `lifeos sync`; `tests/test_habits.py` (6 tests).
- [ ] **P1-15 you** Write your habits (about 5 max) in `40 Me/habits.md`. — once done, tell me so I can regenerate `Today.base`'s Habits view columns (they're generated from your habit list, not hardcoded).
- [x] **P1-16 cc** `snapshot.md` writer. — 2026-09-16: `lifeos.engine.snapshot`; wired into `lifeos sync`; `tests/test_snapshot.py` (2 tests).
- [~] **P1-17 cc** LaunchAgent running every 15 minutes with a stable interpreter path. Walk Michael through the Keychain "Always Allow" prompts. — 2026-09-16: `launchd/com.lifeos.sync.plist` written with the real `.venv/bin/lifeos` path. NOT loaded into launchd yet — holding until real sources (Canvas etc.) are syncing cleanly, since loading it starts a recurring background job. Load command is in the plist's own comment.
- [ ] **P1-18 you** Pin the Today and School tabs, then use them daily for 3–5 days.
- [ ] **GATE 1** every Canvas and Learning Suite deadline in the next 14 days is correct · grades correct · habits grid works · **Michael confirms**

---

## Phase 2: Inbox

- [ ] **P2-01 cc** Gmail collector for all accounts: metadata only, routing, VIP list. Tests.
- [ ] **P2-02 cc** Outlook personal: mail and calendar.
- [ ] **P2-03 cc** Outlook BYU, using Path A or Path B from P1-12.
- [ ] **P2-04 you** Create an internal Slack app in each workspace from cc's manifest. Run `lifeos secret set slack_token:<workspace>`. Map workspaces to domains in config.
- [ ] **P2-05 cc** Slack collector: unread DMs, group DMs, @mentions. Use the email-notification fallback in any workspace that blocks apps.
- [ ] **P2-06 cc** Reconcile: anything read or handled elsewhere is removed on the next sync.
- [ ] **P2-07 cc** `Inbox.md` view. Michael pins the tab.
- [ ] **GATE 2** Inbox shows only needs-reply items · read items disappear within one sync · **Michael confirms**

---

## Phase 3: Ventures

- [ ] **P3-01 you** In the Shopify Dev Dashboard, create an app for **Spiced** with scopes `read_orders`, `read_products`, `read_inventory`. Install it on the store. Store the client ID and secret with `lifeos secret set`.
- [ ] **P3-02 you** Same for **Javvas**.
- [ ] **P3-03 cc** Client credentials token fetch, plus the Shopify collector (unfulfilled orders, low stock). Tests.
- [ ] **P3-04 cc** `Ventures.md` with Spiced and Javvas views. Michael pins the tab.
- [ ] **GATE 3** unfulfilled order counts and low-stock lists match Shopify admin for both stores · **Michael confirms**

---

## Phase 4: Mentors, Brain, AI layer

- [ ] **P4-01 you** Give cc the Mentors routing info: Slack workspace, email domain or addresses, calendars.
- [ ] **P4-02 cc** Mentors routing rules and the no-snippet rule. Tests.
- [ ] **P4-03 cc** `Mentors.md`. Michael pins the tab.
- [ ] **P4-04 cc** Goal and weekly-review templates, plus `Brain.md`. Michael pins the tab.
- [ ] **P4-05 you** Write `40 Me/about-me.md`. Create goal notes for this year, this quarter, and this week.
- [ ] **P4-06 cc** Final vault `CLAUDE.md` and `AGENTS.md` symlink, per spec §10.
- [ ] **P4-07 you** Choose vault sync (Obsidian Sync or a private Git repo). Point the `daily-founder-brief` and `goal-planner` skills at `00 Home/snapshot.md` and `40 Me/goals/`.
- [ ] **P4-08 cc** Security audit: doctor secret scan, plus a check of the vault for message bodies, student data, and participant data. Report the results to Michael.
- [ ] **GATE 4** a fresh Claude Code session in the vault answers "What matters today?" from snapshot.md alone · scan clean · **Michael confirms**

---

## Blockers ledger

Format: `- [ ] <task-id> | <what is missing> | <why it blocks>`

- [ ] P1-12 | Whether BYU Microsoft 365 allows student app consent | Decides the BYU Outlook path in P2-03
- [ ] P2-04 | Whether each Slack workspace allows app installs | May force the email-notification fallback

---

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-09-16 | Weighted scoring; school wins when urgency is equal | A truly urgent venture issue shouldn't get buried |
| 2026-09-16 | Learning Suite items are due at 00:00 on their date | The feed has no times, so items surface early |
| 2026-09-16 | Email and Slack stored as metadata plus a ≤140-char snippet; no snippet for Mentors items | Security and participant privacy |
| 2026-09-16 | Teaching course: only Michael's own events and due dates | FERPA |
| 2026-09-16 | Learning Suite grades entered manually; no scraping | No API, login plus 2FA, BYU policy |
| 2026-09-16 | Habits don't affect score | Ranking stays about deadlines |
| 2026-09-16 | Shopify order `due` = created + 2 days (configurable) | Gives unfulfilled orders urgency |
| 2026-09-16 | AI snapshot file is named `snapshot.md` | `Today.md` and `today.md` collide on macOS |
| 2026-09-16 | Today shows a sync-status line only when a source has failed for more than 2h | A silently broken sync could hide deadlines |
| 2026-09-16 | Native pinned tabs; no community plugins | Clean and simple |
| 2026-09-16 | Vault path `~/LifeOS`, repo path = this folder, macOS confirmed, Canvas base URL `https://byu.instructure.com` | Answers to the 3 P0-01 blocking questions |
| 2026-09-16 | Bases `sort` key follows the documented `groupBy` {property, direction} shape | help.obsidian.md/bases/syntax's schema example shows `groupBy` and column `order` but never shows a `sort` key for row ordering, even though the Views doc describes sortable, multi-property, priority-ordered sort. Needs Michael to verify in the Sort menu once the Fixture Test base is open (P0-10) and correct this file if the UI writes something else. |
| 2026-09-16 | `.obsidian/types.json` used to pre-register `due`/`received` as datetime and `score`/`grade` as number | This file's format isn't in Obsidian's official docs (only that the Properties view UI sets types); treated as best-effort, and Gate 0 has Michael confirm the types actually render correctly in the Fixture Test base |
| 2026-09-16 | Canvas: announcement/conversation field names (`title`/`posted_at`/`read_state`, `subject`/`workflow_state`/`last_message_at`) implemented from stable API convention, not re-verified live this session (a docs fetch timed out) | Planner items, missing submissions, and enrollment grades WERE verified against developerdocs.instructure.com. The real `--dry-run` once Michael's canvas_token exists (P1-01) is the checkpoint that catches any drift before anything is written to the vault |
| 2026-09-16 | Canvas `submitted` status inferred as `submissions.graded or submissions.excused` | The docs confirmed `graded`/`excused`/`late`/`missing`/`needs_grading`/`with_feedback` as submission fields but never confirmed a `submitted` boolean; graded/excused is the safest proxy. Verify against Michael's real overdue-but-submitted assignments once P1-01 is done |
| 2026-09-16 | `received` property (spec §4 says "email and Slack only") also populated on Canvas announcements/messages | §8's School.md spec explicitly lists `received` as a column for "Announcements and messages," so the field's use was widened to match — still just a timestamp, no body/content rule is affected |

---

## Parking lot (not approved; ask Michael before building)

- BYU academic calendar feed (add/drop, withdrawal, finals)
- Shopify sales numbers
- Month-grid calendar view, Kanban boards
- Health, sleep, finance, reading logs, weather
- GitHub issues for the Mentors bot

---

## Session log

| Date | Phase | Summary |
|---|---|---|
| 2026-09-16 | 0 | Repo scaffolded (uv/pyproject/src layout), config loader, Keychain helper, Item model, routing, scoring (4/4 required tests), vault writer (merge/reconcile/prune/snooze), state.json + logging + sync-status.md, `lifeos doctor`, vault scaffolded at `~/LifeOS`, fixture collector + Fixture Test.base written. 23/23 tests pass; doctor exits 0. Waiting on P0-10 (Michael in Obsidian) to close Gate 0. |
| 2026-09-16 | 0→1 | Michael confirmed Gate 0 in Obsidian. Phase 1 started: sent Michael the human-step instructions for P1-01/05/08/10 (Canvas token, Learning Suite feeds, Google OAuth, iCloud password). Built the Canvas collector (planner items, missing submissions, announcements, conversations, teaching-course FERPA-safe events/assignments, grades → course notes), the `Today.base`/`School.base` dashboard views, the habits engine (daily notes, streaks), and the `snapshot.md` writer — all wired into `lifeos sync`. Filled in the real interpreter path in the LaunchAgent plist but held off loading it. 35/35 tests pass. Still blocked on Michael's Phase 1 human steps before Gate 1 is reachable. |
