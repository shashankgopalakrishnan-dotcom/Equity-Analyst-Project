# FIN 67110 Week 1 / Lab 01 Restart Point

**Workspace:** `/Users/shashankgopalakrishnan/Documents/Courses/Mastering AI for finance`
**Updated:** 2026-10-26
**Conversation log:** [`CONVERSATION.md`](CONVERSATION.md)
**Course checklist:** [`WEEK_1_SETUP.md`](WEEK_1_SETUP.md)
**Reading notes:** [`WEEK_1_READING_NOTES.md`](WEEK_1_READING_NOTES.md)

## Goal

Finish any remaining Week 1 and Lab 01 work, preserving user secrets and the professor's ordered Orca checks.

## Week 2 handoff (updated 2026-10-26)

- Week 2 instructions and status: [`WEEK_2/README.md`](WEEK_2/README.md).
- Lab 02 program: [`WEEK_2/desk.py`](WEEK_2/desk.py). Costco and Walmart filing/fact runs are in `WEEK_2/runs/`; use the later Costco and Walmart folders named in the Week 2 README.
- Manual review template: [`WEEK_2/AUDIT_TEMPLATE.md`](WEEK_2/AUDIT_TEMPLATE.md). The SEC extraction and arithmetic ran, but student line-by-line and hand-calculation checks, two partner marks, and the partner reflection are pending.
- Reading notes: [`WEEK_2/PREP_NOTES.md`](WEEK_2/PREP_NOTES.md). The linked Kim, Muhn & Nikolaev arXiv paper is marked withdrawn; ask the instructor which version to use.
- Lab 03 app: [`WEEK_2/lab03_app.py`](WEEK_2/lab03_app.py). Do not run until the exposed Purdue GenAI Studio key is rotated locally and `GENAI_MODEL` is set in `.env`. Install the SDK from `WEEK_2/requirements-lab03.txt` after key rotation.
- Remaining Week 2 human steps: complete audit, partner checks/reflection, run Lab 03, ask partner to choose a company and check two claims, audit all eleven claims, and submit Brightspace Checkpoint 1 with repository commit permalink.
- The supplied PDFs, `.env`, `.vscode/`, and `CONVERSATION.md` are private/local and must not be committed.
- Week 2 coursework was pushed to the private GitHub repository on 2026-10-26. Latest commit: [`63a8fc1`](https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project/commit/63a8fc1478ce60b8b03c7ab36cf27ad6d07766dd). Verified remotely: Week 2 README exists; `.env` and raw SEC Company Facts JSON return 404. Repository visibility remains Private.

## Verified or reported complete

- `python3.12 --version` returned `Python 3.12.14` in this workspace on 2026-10-26. The live Orca chat also showed the same result. The user reports partner sign-off is complete.
- `.gitignore` excludes `.env` and `.env.*`, preserves `.env.example`, and `git check-ignore -v .env` confirms `.env` is ignored.
- `check_env.py` is standard-library-only. It reads `.env`, prints only the first four key characters plus `...`, and prints the SEC User-Agent. It does not validate the key or make an API call.
- Both Orca agents created and opened `hello.md` on 2026-10-26. Codex reported model `GPT-6` (Orca session model shown as `gpt-6-luna`); Antigravity reported `Claude Sonnet 4.6 (Thinking)`. The shared file currently contains the date and Antigravity model name.
- Both Orca agents completed the session-instruction and `.gitignore` checks. Codex named `GEMINI.md` and confirmed the exact ASD-STE100 line was present. Antigravity also answered the `.gitignore` question in short sentences, one claim per sentence.
- The user entered a Purdue GenAI Studio key and a Purdue SEC User-Agent in the workspace `.env`. A value-safe local check confirmed both fields are populated; `python3.12 check_env.py` read them and masked the key. This confirms file reading only, not key validity or an API call.
- Screenshots shared in chat exposed part of the API key. The user must revoke that key and create a replacement. Do not handle the credential rotation or ask the user to paste the replacement into chat. Update `.env` locally after rotation and rerun the masked check.
- The user reports LSEG, WRDS, and Capital IQ Purdue-email registration is complete.
- The user reports partner sign-off and Brightspace Session 1 checkout are complete. Their individual evidence and submitted contents were not reviewed in this session.
- The user reports the repository is `https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project.git`. The owner tab showed it is **Private** and empty. The user has now authorized adding Week 1 and Week 2 coursework files. Keep it private unless the user separately asks to change visibility. The Lab 01 logged-out public file check remains pending.
- Earlier placeholder-only checks were superseded on 2026-10-26: the user later populated both `.env` fields, and the script read them. The key was then exposed in screenshots and must be rotated.
- Assigned Francis & Zhang sections, Costco SEC research, and Anthropic through the end of “Prompt chaining” are marked complete in the course notes.
- Draft responses to the two Week 1 preparation questions are now in `WEEK_1_READING_NOTES.md`. Confirm figure-specific interpretation against the supplied paper if needed.

## Pending / blocked / unverified

1. **Credential rotation — user action:** Revoke the exposed Purdue GenAI Studio key and make a replacement. Enter the replacement in `.env` locally, then run `python3.12 check_env.py` again. Never share the key or a screenshot that shows it.
2. **Lab 01 public file check — pending:** The repository is private. The user authorized a private coursework upload, but did not authorize changing visibility. The logged-out Lab 01 check still needs a public repository. Keep the repo private until the user explicitly asks to change its visibility. Verify `.env` stays absent from GitHub.
3. **Partner evidence — user-reported, not independently reviewed:** The user reports partner sign-off and Brightspace Session 1 checkout are complete. The paper initials, partner name, and submitted checkout contents are not in this workspace. The in-class model/harness/agent gap list and reflection also cannot be verified here; complete or confirm these with the partner if needed.
4. **Provider requirement — unverified:** The course's earlier setup notes specified an OpenAI API key. The local key is from Purdue GenAI Studio. Whether this provider satisfies the course requirement is not verified. The script does not validate a key or call the provider.
5. **Errors:** No lab error text was reported. If a check fails, record the exact command and error after removing keys and personal account details.

## GitHub and file safety

The authenticated owner tab showed the intended repository is private and empty. The local `origin` now points to that repository. The user authorized uploading Week 1 and Week 2 coursework files to the private repo, but this machine has no working GitHub push credential. `.env` is ignored. Keep `.env`, `FRL-CanAIReplaceAnalyst.pdf`, `.vscode/`, and `CONVERSATION.md` out of the upload.

## Resume here

Rotate the exposed key yourself, replace it in the local `.env`, and rerun `python3.12 check_env.py`. The repo is private; the user authorized a coursework upload without a visibility change. Check the partner paper initials, reflection, and Brightspace contents if proof is needed. See [`WEEK_1_SETUP.md`](WEEK_1_SETUP.md) for the course checklist and [`CONVERSATION.md`](CONVERSATION.md) for the activity log.
