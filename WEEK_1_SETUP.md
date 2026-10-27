# Mastering AI for Finance — Week 1 setup

**Purpose:** Prepare for the first hands-on session. Bring what is working and the exact error text for anything that is not. Session 1 began Thursday, October 22, 2026. The partner check is ungraded.

## Current setup snapshot

Status refreshed October 26, 2026. CLI version details below were last observed October 19 unless noted.

| Requirement | Status | Evidence / next step |
|---|---|---|
| Python 3.11+ available from terminal | **Ready** | Installed Python 3.12.14 with `uv`. Verified in an Orca terminal using `python3.12 --version`. The macOS system `python3` remains 3.9.6; use `python3.12` or `uv run --python 3.12 python` for this course. |
| OpenAI Codex CLI | **Ready** | Running in Orca on this folder; Codex CLI 0.163.0 displayed. |
| Google Antigravity `agy` CLI | **Ready** | Running in Orca's second terminal pane on this folder; CLI 1.2.16 displayed and signed in. |
| Orca installed and running on this folder | **Ready** | `/Applications/Orca.app` is running with this course folder open and two side-by-side terminal panes. |
| Provider API key | **Local values read; rotation pending** | A value-safe check found both `API_KEY` and `SEC_USER_AGENT` populated in `.env`. `python3.12 check_env.py` read them and masked the key. Screenshots in chat exposed part of the key, so the user must revoke it and create a replacement. The course notes previously specified an OpenAI API key; whether a Purdue GenAI Studio key meets that requirement is unverified. |
| Lab 01 agent and key-read checks | **Agent checks complete; repeat key check after rotation** | Both Orca agents created and opened `hello.md` dated `2026-10-26`. Codex reported `GPT-6` (Orca model label `gpt-6-luna`); Antigravity reported `Claude Sonnet 4.6 (Thinking)`. Both completed the instruction-file and `.gitignore` checks. The shared `hello.md` currently contains the Antigravity model. `.env` is ignored by Git. The key-read check works, but rerun it after replacing the exposed key. |
| GitHub repository | **Private; coursework upload authorized, Lab 01 public check incomplete** | The owner tab showed the supplied repo is private and empty. The user has now authorized adding Week 1 and Week 2 coursework files. Keep the repository private unless the user separately asks to change visibility. The Week 1 logged-out public check still needs a public repo. |
| Francis & Zhang (2026), assigned sections | **Complete** | Read the supplied full-text PDF's Introduction, Section 3.1, and Section 4 on October 22, 2026. Section-by-section notes, key results, caveats, and class discussion questions are in `WEEK_1_READING_NOTES.md`. |
| Costco latest earnings release and 10-K | **Complete** | SEC EDGAR source links and the exact total-revenue figures are in `COSTCO_SEC_NOTES.md`. FY 2026 total revenue is $303,154 million in both. |
| Anthropic, “Building effective agents” | **Complete to assigned point** | Read through the end of “Workflow: Prompt chaining.” Notes on model, harness, agent, and prompt chaining are in `WEEK_1_READING_NOTES.md`. |
| Purdue data access | **Access and registration confirmed per user** | Access to LSEG Workspace, WRDS, and Capital IQ was confirmed on October 22, 2026. User reported the Purdue-email registration check complete on October 26, 2026. Course instructions are at the data page linked below. |

## First-session checklist

- [x] Install Python 3.11+ and verify it from an Orca terminal.
- [x] Run Codex CLI and `agy` side by side in Orca on this folder.
- [x] Generate a provider API key in Purdue GenAI Studio (user reported October 26, 2026).
- [x] Enter local `API_KEY` and SEC User-Agent values in `.env`, then run `python3.12 check_env.py` (verified October 26, 2026; file read only, no key validation).
- [ ] Revoke the key exposed in screenshots, create a replacement, update `.env` locally, and rerun `python3.12 check_env.py`.
- [x] Prepare `hello.md` and `check_env.py` locally for Lab 01.
- [x] Have each Orca agent create and open `hello.md` dated `2026-10-26` (Codex: `GPT-6` / Orca label `gpt-6-luna`; Antigravity: `Claude Sonnet 4.6 (Thinking)`).
- [x] Have each Orca agent complete the ASD-STE100 instruction-file and `.gitignore` checks; both reported `GEMINI.md` with the requested line.
- [x] Verify the supplied GitHub repository URL in the open owner tab: it is private and was empty.
- [ ] Complete the Lab 01 logged-out file check. The repository is private. This check requires public visibility, which the user has not requested. Keep it private unless the user explicitly asks to change visibility.
- [x] Read Francis & Zhang (2026), Introduction, Section 3.1, and Section 4 from the full text.
- [x] Locate Costco's latest SEC earnings release and 10-K; record total revenue and source links.
- [x] Read Anthropic's “Building effective agents” through the end of the Prompt chaining workflow section.
- [x] Confirm access to LSEG Workspace, WRDS, and Capital IQ.
- [x] Confirm each account is registered with your Purdue email (user reported October 26, 2026).
- [x] Complete partner sign-off and Brightspace Session 1 checkout (user reported October 26, 2026; individual checkpoint evidence and submission contents not independently reviewed here).
- [ ] Bring exact error text for anything that fails.

## Error log

Paste exact error text here (remove any secrets, tokens, or personal account details):

| Date | Requirement / command | Exact error | What I tried / result |
|---|---|---|---|
| | | | |

## Working notes

- **Python command:** `python3.12` (3.12.14); `uv run --python 3.12 python` also works.
- **Orca:** installed and open; this folder is the active project; Codex and `agy` are running side by side.
- **Provider configured (provider name only):** Purdue GenAI Studio (user reported; key exposed in a screenshot and must be rotated).
- **GitHub repository URL:** https://github.com/shashankgopalakrishnan-dotcom/mastering-ai-for-finance-fall-2026
- **Purdue data access:** User confirmed existing access to LSEG, WRDS, and Capital IQ on October 22, 2026.

## Course references

- Prerequisites and setup: https://cinderzhang.github.io/FIN67110-Fall2026/grading.html#prerequisites--your-setup-is-yours
- Course data instructions: https://cinderzhang.github.io/FIN67110-Fall2026/reference/data.html
