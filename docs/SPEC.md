# LifeOS Build Prompt for Claude Code

> **How to use:** Put this file and `PROGRESS.md` in an empty folder (it becomes the sync repo). Open Claude Code in that folder and say: *"Read lifeos-claude-code-prompt.md and PROGRESS.md, then start Phase 0."*

---

## 0. Your role and how to work

You are building **LifeOS** for Michael. It is a Python sync engine that pulls school, calendar, email, Slack, and Shopify data into an Obsidian vault. Six pinned tabs in that vault show what matters, ranked by priority, with school first. You write all the code. Michael handles the setup steps that need his logins.

These rules sit on top of Michael's global `CLAUDE.md`. For this project, this file wins when they conflict.

1. **PROGRESS.md is the source of truth.** Read it at the start of every session. After each task, check the box, add a dated one-line note, and update the Blockers ledger and Decisions log. Never mark a task done unless its gate or "done when" condition is actually met.
2. **One phase at a time.** Finish a phase, stop at its gate, and wait for Michael to confirm before starting the next.
3. **Build exactly this spec.** Don't add features, views, fields, plugins, dependencies, or widgets beyond what's written here. Michael wants the dashboard clean and simple. If something seems worth adding, put it in PROGRESS.md → Parking lot and ask.
4. **Human steps.** When a task needs Michael (tokens, OAuth clients, app installs), stop. Give him exact numbered steps, including the exact command to paste, then wait. Never guess credentials or work around missing ones.
5. **Blocked? Ledger it.** If due diligence can't resolve something (API limit, missing secret, unclear rule), add `- [ ] <task-id> | <what is missing> | <why it blocks>` to the Blockers ledger. Mark the task `BLOCKED` and keep going on unblocked tasks in the same phase.
6. **Verify current docs before each integration.** APIs change. For example, Shopify stopped allowing new admin-created custom apps on January 1, 2026. Before writing each coector, check the provider's current official docs for auth, endpoints, scopes, and rate limits. Before writing any `.base` file, check Obsidian's Bases docs (https://help.obsidian.md/bases) for filter, sort, grouping, limit, formula, and embed syntax. Never write Bases YAML from memory. If the docs contradict this spec, follow the docs and log it in Decisions.
7. **Show before writing.** For each new source, run `--dry-run` on real data first. Show Michael 5 sample items (title, domain, score) before the first real write to the vault.
8. **Lessons.** When a fix takes real effort, add a one-line lesson to the repo `CLAUDE.md` under "Lessons."
9. **Tests.** Every collector gets unit tests that use saved fixtures scrubbed of personal data. Tests never touch the network.

**Stop and ask immediately if:**
- a design would put email or Slack bodies, attachments, student information, or Mentors International participant data into the vault
- a secret would need to live in a file
- a provider requires payment, a security review, or an admin approval Michael hasn't given
- a change would overwrite or delete a note Michael wrote

---

## 1. Blocking questions (ask at the start of Phase 0, and only these)

1. Vault path (default `~/LifeOS`) and repo path (default: this folder).
2. Confirm macOS. The scheduler, Keychain, and iCloud setup assume it.
3. BYU Canvas base URL (`https://<school>.instructure.com`).

Everything else has a default below. Act on it.

---

## 2. Architecture

Three layers that never mix:

1. **Collectors (Python):** one module per source, read-only access, each returning normalized `Item`s.
2. **Engine (Python):** routes each item to a domain, scores it, merges it into the vault using field ownership rules, reconciles stale items, and writes the AI snapshot.
3. **Display (Obsidian):** six tab notes in `00 Home/` that embed Bases views over note properties. No community plugins. Obsidian's native pinned tabs are the tab system.

**Stack:** Python 3.12, `uv`, `typer`, `pydantic`, `httpx`, `python-frontmatter`, `keyring`, `icalendar`, `caldav`, `google-api-python-client`, `google-auth-oauthlib`, `msal`, `slack_sdk`, `pytest`. Ask before adding anything else.

**Time zone:** `America/Denver` everywhere. Store datetimes as ISO 8601 with an offset.

### CLI

```
lifeos sync [--source NAME] [--dry-run]   # all sources by default; one failing source never stops the others
lifeos auth SOURCE [--account NAME]       # interactive login flows
lifeos secret set KEY                     # prompts and stores in Keychain; never echoes
lifeos doctor                             # config, auth status, vault paths, secret scan, last sync per source
```

### Where things live

```
<repo>/                                  # sync code (git). Never inside the vault.
  src/lifeos/collectors/                 # canvas, learning_suite, gcal, icloud, gmail, outlook, slack, shopify, fixture
  src/lifeos/engine/                     # models, routing, scoring, vault, reconcile, snapshot, habits
  tests/  tests/fixtures/
  launchd/com.lifeos.sync.plist
  CLAUDE.md                              # short: pointers to docs/SPEC.md and PROGRESS.md, plus Lessons
  PROGRESS.md
  docs/SPEC.md                           # this file, moved here in Phase 0
~/.config/lifeos/config.toml             # non-secret settings
macOS Keychain, service "lifeos"         # every token, password, client secret, feed URL, OAuth cache
~/.local/state/lifeos/state.json         # last success/error per source, done_at dates
~/Library/Logs/lifeos/sync.log           # never contains secrets or message content
```

### config.toml skeleton

```toml
vault = "~/LifeOS"
timezone = "America/Denver"
canvas_base_url = "https://<school>.instructure.com"

[weights]
school = 40
mentors = 30
spiced = 20
javvas = 20
other = 5

[canvas]
major_points_threshold = 100

[learning_suite]
courses = []                 # feed URLs live in Keychain as ls_feed:<COURSE>

[google]
accounts = []
gcal_exclude = []            # calendars that duplicate Learning Suite feeds
calendar_domains = {}        # "calendar id" = "domain"

[icloud]
calendars = []               # iCloud-native calendars only

[outlook]
accounts = ["personal", "byu"]

[slack]
workspaces = {}              # "workspace" = "domain"

[shopify]
stores = { spiced = "<store>.myshopify.com", javvas = "<store>.myshopify.com" }
order_sla_days = 2
low_stock_threshold = 10

[routing]
senders = {}                 # exact address = domain (checked first)
sender_domains = {}          # "byu.edu" = "school"
vip = []                     # professors, TAs, Mentors leads
```

---

## 3. Vault layout

```
LifeOS/
├── CLAUDE.md          # AI entry point (§10)
├── AGENTS.md          # symlink → CLAUDE.md
├── 00 Home/           # Today, School, Mentors, Ventures, Inbox, Brain (.md), *.base, snapshot.md, sync-status.md
├── 10 School/         # one folder per course, each containing a course note
├── 20 Mentors/
├── 30 Ventures/       # Spiced/, Javvas/
├── 40 Me/             # about-me.md, habits.md, goals/-DD.md, weekly reviews
├── 90 Sync/           # one note per synced item: <uid>.md
└── _templates/        # task.md, goal.md, weekly-review.md
```

The AI snapshot is named `snapshot.md`, not `today.md`, because macOS treats `Today.md` and `today.md` as the same file.

**Write permissions:**
- In Phase 0, Claude Code scaffolds the vault once and never overwrites a file that already exists.
- After that, the sync engine may write only these: `00 Home/snapshot.md`, `00 Home/sync-status.md`, `90 Sync/`, course notes in `10 School/` (only the fields listed in §5), and daily notes in `50 Journal/` (§9).
- It never edits the body of a note Michael wrote.

---

## 4. Item schema

Every synced item and every manual task is one note. Views never show more than 7 columns.

**Core properties**

| Property | Type | Values |
|---|---|---|
| `domain` | text | school, mentors, spiced, javvas, other |
| `type` | text | assignment, exam, event, announcement, message, email, slack, order, inventory, task |
| `due` | date | the deadline, or the start time for events; empty if none |
| `score` | number | computed by Python (§6) |
| `status` | text | open, done, snoozed |
| `source` | text | canvas, learning-suite, gcal, icloud, gmail, outlook, slack, shopify, manual |
| `link` | text | URL back to the original |

**Context properties** (hidden unless a view needs them):
- `title`: display name
- `uid`: `<source>-<native id>`, also used as the filename
- `course`: school items only
- `platform`: canvas or learning-suite
- `received`: email and Slack only
- `account`: which mailbox, workspace, or store
- `goal`: a link, manual tasks only

**Field ownership (the merge rule):**
- On synced items, Python owns every property except `status`. Michael owns `status`.
- On manual tasks (`source: manual`), Michael owns everything except `score`, which Python recomputes every sync.
- Synced item bodies are empty or one generated line, and Python may rewrite them.

**Status behavior:**
- `snoozed` hides an item from Today only. The first sync after midnight resets it to `open`.
- An item becomes `done` when Michael sets it or the source reports it (for example, a Canvas submission). Record `done_at` in state.json, then delete the note 14 days later.
- **Reconcile:** if a source stops returning an item that's still `open` (email read, DM read, order fulfilled), delete its note. There are four exceptions:
  - Learning Suite items and manual tasks are never auto-removed; they wait for `done`.
  - Past-due Canvas items stay until they're submitted or marked done.
  - Events are deleted once they end.

**Property types:** register datetime, number, and checkbox types wherever Obsidian stores property types (verify; likely `.obsidian/types.json`) so views sort correctly.

---

## 5. Sources

Only pull what needs action. Store metadata, never message bodies.

### 5.1 Canvas (Phase 1)
**Auth:** personal access token in Keychain `canvas_token`; base URL from config.

**Student enrollments** (active, `enrollment_type=student`):
- **Planner items:** `/api/v1/planner/items`, from 14 days back to 30 days ahead. Creates assignment/exam items with submission status; submitted items become `done`.
- **Missing work:** `/api/v1/users/self/missing_submissions`.
- **Unread announcements** (last 14 days) and **unread Canvas inbox conversations:** type announcement or message, metadata only.
- **Grades:** `/api/v1/users/self/enrollments?type[]=StudentEnrollment&state[]=active`. Update `grade`, `letter`, and `grade_updated` on the course note. If the professor hides totals, leave `grade` empty and set `letter: hidden`. Create the course note if it's missing.

**Teacher enrollments** (the Mentors International pilot course): domain `mentors`. Pull only course calendar events and assignment due dates. Never pull student names, submissions, grades, or conversations (FERPA).

**`is_major`** is true when any of these hold: type is exam, `points_possible` ≥ the config threshold, or the title matches exam, midterm, final, or project.

**Fallback:** if token creation is disabled or tokens are short-lived, use the Canvas calendar feed (dates only) and ledger it.

### 5.2 BYU Learning Suite (Phase 1)
There's no API. Each course's Schedule tab has a "Get iCalendar Feed" link. Michael stores each URL with `lifeos secret set ls_feed:<COURSE>` and lists his courses in config.
- **Due times:** feed items are all-day events, and the feed only updates upstream once a day. Set `due` to 00:00 America/Denver on that date, so items surface early rather than late.
- **Filtering:** the feed also includes class days, holidays, devotionals, forums, and exam info. Before writing the filter, fetch Michael's real feeds, show him the distinct event titles, and agree on the filter together.
- **No submission status:** items stay `open` until Michael marks them done. Set `platform: learning-suite`.
- **Grades:** not available. Create a course note with empty `grade`, `letter`, and `grade_updated` for Michael to fill in during his weekly review. Python never writes Learning Suite grade fields. Do not scrape Learning Suite.
- **Duplicates:** any Google calendar that subscribes to a Learning Suite feed goes in `gcal_exclude`.

### 5.3 Google Calendar (Phase 1) and Gmail (Phase 2)
**Auth:**
- One Google Cloud project with a "Desktop app" OAuth client. Store the client JSON in Keychain `google_client`, and one token per account in `google_token:<account>`.
- The publishing status must be **In production**, because Testing-mode refresh tokens expire after 7 days. The unverified-app warning is expected for personal use.

**Calendar:** scope `calendar.readonly`. Pull events for the next 7 days from every calendar not in `gcal_exclude`. Map calendars to domains via config.

**Gmail:** scope `gmail.readonly`. Pull unread inbox mail from the last 7 days, excluding the Promotions, Social, Updates, and Forums categories. Store only sender name and address, subject, a snippet of at most 140 characters, received time, and a thread link. No bodies, no attachments. Route by exact sender, then sender domain, and apply the VIP list.

### 5.4 iCloud Calendar (Phase 1)
Use CalDAV at `https://caldav.icloud.com` via the `caldav` library, with the Apple ID and an app-specific password stored in Keychain. Pull only the calendars in `icloud.calendars`. Dedupe across all calendar sources by iCal UID.

### 5.5 Outlook: personal and BYU (Phase 2; consent test in Phase 1)
**Auth:** one Microsoft Entra app registration with the audience set to organizational directories plus personal Microsoft accounts. MSAL public client, authority `common`, device-code flow, scopes `Mail.Read Calendars.Read offline_access`. Serialize the token cache into Keychain.

**Mail:** unread inbox from the last 7 days, metadata only (same rules as Gmail).

**Calendar:** calendarView for the next 7 days.

**BYU account:** the path is decided by task P1-12.
- **Path A (consent works):** same as personal.
- **Path B (admin approval required):**
  - Calendar: use a published ICS link, if BYU allows publishing.
  - Mail: use a forwarding rule to Gmail, only if BYU IT policy allows it.
  - Otherwise: leave BYU mail out and log it in Decisions.

### 5.6 Slack (Phase 2)
One internal Slack app per workspace. Give Michael a ready-to-paste app manifest. Store the user token in Keychain `slack_token:<workspace>`.
- **Pull:** unread DMs, group DMs, and @mentions from the last 7 days.
- **Store:** sender, channel, received time, link, and a snippet of at most 140 characters (except for the mentors domain; see §7).
- **Before building:** verify current scopes and rate limits.
- **Fallback:** if a workspace blocks app installs, route Slack email notifications through the Gmail collector and ledger it.

### 5.7 Shopify: Spiced and Javvas (Phase 3)
**Auth:**
- Create new custom apps in the **Shopify Dev Dashboard** (admin-created custom apps can't be made after Jan 1, 2026). Use one app per store with scopes `read_orders`, `read_products`, and `read_inventory`.
- Get an access token through the **client credentials grant**, using the client ID and secret from Keychain (`shopify:<store>:client_id`, `shopify:<store>:client_secret`). Verify the current flow and token lifetime in Shopify's docs.

**GraphQL Admin API:**
- **Unfulfilled open orders** become type `order`, with `due` = created_at + `order_sla_days`.
- **Variants below `low_stock_threshold`** become type `inventory`, with no due date.
- Pull nothing else (no sales numbers).

### 5.8 Manual tasks (Phase 1)
Michael creates these in Obsidian from `_templates/task.md`, in any domain folder. Python only computes `score`.

---

## 6. Routing and scoring

**Routing precedence:** source rules (teaching course → mentors, store → spiced/javvas) come first. Then config maps (exact sender, sender domain, calendar, Slack workspace). Anything left is `other`.

```python
def score(item, now, weights, vip):
    s = weights[item.domain]
    if item.due:
        h = (item.due - now).total_seconds() / 3600
        if h < 0:      s += 50   # overdue or missing
        elif h <= 24:  s += 40
        elif h <= 72:  s += 25
        elif h <= 168: s += 10
    if item.sender in vip: s += 15
    if item.is_major:      s += 10
    return s
```

**Required test cases:**
- A school assignment due in 20h (80) outranks a Spiced order due in 20h (60).
- An overdue Spiced order (70) outranks a school item due in 6 days (50).
- A VIP professor email (55) ranks below a school assignment due in 60h (65).
- A Learning Suite item dated tomorrow is scored as due at 00:00 tomorrow.

---

## 7. Data rules (non-negotiable)

- **Secrets live only in Keychain.** Never in the repo, vault, config, logs, fixtures, or terminal output. `lifeos doctor` scans the repo and vault for token patterns (`shpat_`, `xoxp-`, `xoxb-`, `ya29.`, `-----BEGIN`, Canvas-style `<digits>~<long string>`) and fails loudly on a match.
- **Email and Slack:** metadata plus a snippet of at most 140 characters. No bodies, attachments, or full threads.
- **Mentors domain:** store only sender, subject or channel, received time, and link. No snippet text, because messages may mention program participants. Never ingest Mentors International WhatsApp bot data, mentee conversations, or research datasets from any source.
- **Teaching course (FERPA):** only Michael's own course events and due dates. No student names, submissions, grades, or messages.
- **Sync health:** each source records its last success and last error in state.json.
  - `snapshot.md` always lists sync status.
  - `sync-status.md` stays empty while everything is healthy. It shows one line per source that has been failing for more than 2 hours.

---

## 8. The six tabs

Each tab is a note in `00 Home/` that embeds Bases views. Keep tabs spacious: no extra headings, callouts, or widgets. Column lists below are maximums. Michael pins the tabs himself; Obsidian restores pinned tabs on launch.

### Today.md (in this order)
1. **Agenda:** events plus any item due today or tomorrow, all domains, sorted by `due`. Columns: due, title, domain.
2. **Top 7:** `status = open`, `type != event`, sorted by score descending, limit 7. Columns: title, domain, due, score, status, link.
3. **Habits:** the last 7 daily notes in `50 Journal/`, newest first, with one checkbox column per habit. Columns: date, plus the habits.
4. **Navigation line:** `[[School]] · [[Mentors]] · [[Ventures]] · [[Inbox]] · [[Brain]]`, followed by links to each course note.
5. **Sync status:** an embed of `sync-status.md` (renders nothing when healthy).

### School.md
1. **Due in the next 14 days:** domain school, open, grouped by course (if grouping isn't supported, use one view per course), sorted by due. Columns: title, due, score, status, platform, link.
2. **Missing:** Canvas missing submissions plus past-due Learning Suite items that are still open. Columns: title, course, due, status, link.
3. **Grades:** course notes. Columns: course, platform, grade, letter, grade_updated.
4. **Announcements and messages:** open announcements and messages. Columns: title, course, received, link.

### Mentors.md
One view: domain mentors, open, sorted by score. Columns: title, type, due, score, status, link. Below it, a link to `20 Mentors/`.

### Ventures.md
Two views, **Spiced** and **Javvas**, each filtered to that domain, open, sorted by score. Columns: title, type, due, status, link.

### Inbox.md
One view: type email or slack, open, sorted by score. Columns: title (formatted as "Sender: Subject"), domain, account, received, status, link. Michael replies in the original app.

### Brain.md
1. **Goals:** notes in `40 Me/goals/` with `status: active`, grouped by level (year, quarter, week). Columns: title, level, parent, status.
2. **This week's tasks:** open manual tasks whose `goal` links to a week-level goal. Columns: title, goal, due, status.
3. **Links:** `[[about-me]] · [[habits]]` and the latest weekly review.

**Goal note properties:** `level` (year, quarter, or week), `parent` (link), `status` (active, done, or dropped).

---

## 9. Habits

- **The list:** `40 Me/habits.md` holds one habit per line as `- habit name`. Michael writes it; about 5 habits max.
- **Daily notes:** the first sync after midnight creates `50 Journal/YYYY-MM-DD.md` if it's missing, with one unchecked checkbox property per habit (the key is the slugified habit name).
  - Only today's note can receive a newly added habit property.
  - Past notes are never modified.
- **Streaks:** consecutive checked days through yesterday, plus today if checked. They appear in `snapshot.md` only.
- **Score:** habits never affect `score`.

---

## 10. AI layer and scheduler

### `00 Home/snapshot.md`
Rewritten every sync as plain markdown, kept under about 150 lines. It contains:
- the generation timestamp and sync status per source
- the agenda for today and tomorrow
- the top 10 open items (title, domain, due, score, link)
- school: missing work, what's due in the next 7 days, and one line of grades
- habit streaks

### Vault `CLAUDE.md`
At most 60 lines. `AGENTS.md` is a symlink to it, so Codex and other agents read the same file. It contains:
- **Who Michael is:** a pointer to `40 Me/about-me.md` (Michael writes that file).
- **Vault map:** 8 lines.
- **Start here:** "For what matters now, read `00 Home/snapshot.md` first."
- **Priority order:** school, then Mentors International, then Spiced and Javvas.
- **Rules:** don't edit `90 Sync/` except `status`; create tasks from `_templates/task.md`; don't copy vault content outside the vault without asking.

### Scheduler
- Use a **LaunchAgent**, not a LaunchDaemon, so the login Keychain is available. It runs `lifeos sync` every 15 minutes and logs to `~/Library/Logs/lifeos/`.
- Expect a one-time Keychain "Always Allow" prompt per secret.
- Point the plist at a stable interpreter path, because rebuilding the venv can change the path and trigger the prompts again.

---

## 11. Phase gates

Task IDs and owners live in PROGRESS.md.

- **Gate 0:** `pytest` is green, `lifeos doctor` passes, and fixture items appear in a test Base in Obsidian with correct property types. Michael confirms.
- **Gate 1:** after 3–5 days of daily use, every Canvas and Learning Suite deadline in the next 14 days appears correctly on School, grades are right, and the habits grid works. Michael confirms.
- **Gate 2:** Inbox shows only needs-reply items, and anything read elsewhere disappears within one sync. Michael confirms.
- **Gate 3:** for both stores, the unfulfilled order count and the low-stock list match Shopify admin. Michael confirms.
- **Gate 4:** a fresh Claude Code session opened in the vault correctly answers "What matters today?" from `snapshot.md` alone, and the secret scan comes back clean. Michael confirms.
