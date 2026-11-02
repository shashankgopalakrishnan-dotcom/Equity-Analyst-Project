# FIN 67110 Workspace Restart Point

**Workspace:** `/Users/shashankgopalakrishnan/Documents/Courses/Mastering AI for finance`
**Updated:** 2026-11-02 (Checkpoint 1 status review)
**Conversation log:** [`CONVERSATION.md`](CONVERSATION.md)
**Course checklist:** [`WEEK_1_SETUP.md`](WEEK_1_SETUP.md)
**Reading notes:** [`WEEK_1_READING_NOTES.md`](WEEK_1_READING_NOTES.md)

## Current restart — 2026-11-02

The active work is the Lab 03 report audit for COST and the partner-selected company CMG. Reports for WMT, TGT, BJ, AAPL, and MSFT were also generated at the user's request.

- **Completed:** Lab 02 run folders and saved Financial Datasets quotes are available for all six tickers. The Lab 03 app is [`WEEK_2/lab03_app.py`](WEEK_2/lab03_app.py). Its 10-K extractor now selects the numbered Business and MD&A sections across the saved filing layouts.
- **Generated:** Reports for COST, WMT, TGT, BJ, AAPL, and MSFT completed sequentially on 2026-11-01 with `qwen3:8b`. The partner selected CMG; its seven-step SEC/XBRL run and Lab 03 report also completed on 2026-11-01, using MCD, YUM, and CAVA as peers. Exact paths are in [`WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md`](WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md). The `.env` model setting was not changed.
- **Audit still pending:** These are model drafts. CMG's report has a visible 1,000x unit error in annual revenue and capex. COST also compares P/E with peer operating margins. Check all eleven claims, all other numbers, source lines, and recommendation logic against the filings before submission.
- **Next action:** Audit the required COST and CMG reports. The partner must check two CMG claims. Complete the reflection. Submit Checkpoint 1 with a commit link that the grader can access.
- **Repository:** The selected coursework and Lab 03 run/report artifacts were pushed to the private GitHub repository in commit `9bc9811`. The remote tree check found no `.env`, PDFs, `.vscode/`, or `CONVERSATION.md`. Brightspace was not submitted.
- Keep `.env` private. Do not commit or upload it.

## Previous restart notes

The notes below record the earlier Week 2 Lab 02 status. Week 1 / Lab 01 notes remain for reference.

- Completed a source review of all seven saved Costco Lab 02 steps. The filing selections, saved documents, XBRL values and periods, arithmetic, release figures, and peer margins agree with SEC sources. Detailed evidence and source links are in [`WEEK_2/LAB02_V_KNOWN_ANSWER_VERIFICATION.md`](WEEK_2/LAB02_V_KNOWN_ANSWER_VERIFICATION.md). The instructor-screen price is not independently confirmed, although `$904.70` matches the September 23, 2026 close before the release.
- Recorded one source difference: the saved Costco earnings-release cash-flow table says `$15,825m`; the 10-K and Company Facts say `$15,817m`. The Lab 02 calculation uses the requested 10-K figure.

- Updated [`WEEK_2/desk.py`](WEEK_2/desk.py): non-revenue facts now use candidate tags that contain the revenue fiscal year, and retain the prior year; Step 7 prints the selected current and prior facts for each peer; Step 2 reports when Item 2.02 is verified in the selected 8-K.
- Updated [`WEEK_2/README.md`](WEEK_2/README.md) with implementation status, the exact run command, no-install note, and SEC timestamp source.
- Verified `python3.12 -m py_compile WEEK_2/desk.py` and ran the full seven-step COST example with WMT, TGT, BJ, and price `904.70`. Costco calculations and release lines printed. The saved output is [`WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261026_223242_EDT`](WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261026_223242_EDT/). Target's current-debt fact was unavailable in Company Facts; the program reports it as unavailable rather than guessing.
- No package install is required; the desk uses the Python 3.12 standard library. Example command from the workspace:

  ```sh
  python3.12 WEEK_2/desk.py COST --peers WMT,TGT,BJ --price 904.70
  ```

- **SEC timestamp detail:** The script reads `acceptanceDateTime` from the SEC submissions API. The SEC archive directory index text has no “Accepted” timestamp, so compare the API value with the SEC filing record for the course check.
- **Still pending:** Your handwritten Lab 02 checklist, two partner checks, partner reflection, and Brightspace Checkpoint 1. My independent recalculation and source review do not complete the student/partner evidence steps.
- These latest `desk.py` and README changes are local and not pushed to GitHub. Keep `.env` private. The repository remains private.

## Goal

Finish remaining Week 1 and Week 2 coursework, preserving user secrets and the professor's ordered Orca checks.

## Week 2 handoff (updated 2026-10-26)

- Week 2 instructions and status: [`WEEK_2/README.md`](WEEK_2/README.md).
- Lab 02 program: [`WEEK_2/desk.py`](WEEK_2/desk.py). Costco and Walmart filing/fact runs are in `WEEK_2/runs/`; use the later Costco and Walmart folders named in the Week 2 README.
- Manual review template: [`WEEK_2/AUDIT_TEMPLATE.md`](WEEK_2/AUDIT_TEMPLATE.md). The SEC extraction and arithmetic ran, but student line-by-line and hand-calculation checks, two partner marks, and the partner reflection are pending.
- Reading notes: [`WEEK_2/PREP_NOTES.md`](WEEK_2/PREP_NOTES.md). The linked Kim, Muhn & Nikolaev arXiv paper is marked withdrawn; ask the instructor which version to use.
- Lab 03 app: [`WEEK_2/lab03_app.py`](WEEK_2/lab03_app.py). The user reports the key was rotated and saved locally. A value-safe check confirmed it is present; an authenticated model-list request confirmed `qwen3-coder:latest` is available. The SDK is installed in local ignored `.venv/`. Costco's four-role run and report are in `WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261026_221745_EDT/`.
- Report note: the model draft stated a wrong price ($891.67) and omitted quarterly revenue and revenue growth. The raw output is preserved as `COST_lab03_model_draft.md`; `COST_lab03_report.md` corrects the known price and adds an 11-claim source table. Student must still check every claim, the narrative citations, and the recommendation by hand.
- Remaining Week 2 human steps: complete the report and Lab 02 hand audits, get partner claim checks and reflection, run the partner-selected company, and submit Brightspace Checkpoint 1 with the latest repository commit permalink.
- The supplied PDFs, `.env`, `.vscode/`, and `CONVERSATION.md` are private/local and must not be committed.
- Week 2 coursework was pushed to the private GitHub repository on 2026-10-26. The Lab 02 primary Costco and Walmart Company Facts exports were added in [`0532342`](https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project/commit/0532342), under the user's earlier coursework-upload authorization. Verified remotely: both files exist; `.env` returns 404. Peer Company Facts exports remain local and ignored. Repository visibility remains Private.

## Verified or reported complete

- `python3.12 --version` returned `Python 3.12.14` in this workspace on 2026-10-26. The live Orca chat also showed the same result. The user reports partner sign-off is complete.
- `.gitignore` excludes `.env` and `.env.*`, preserves `.env.example`, and `git check-ignore -v .env` confirms `.env` is ignored.
- `check_env.py` is standard-library-only. It reads `.env`, prints only the first four key characters plus `...`, and prints the SEC User-Agent. It does not validate the key or make an API call.
- Both Orca agents created and opened `hello.md` on 2026-10-26. Codex reported model `GPT-6` (Orca session model shown as `gpt-6-luna`); Antigravity reported `Claude Sonnet 4.6 (Thinking)`. The shared file currently contains the date and Antigravity model name.
- Both Orca agents completed the session-instruction and `.gitignore` checks. Codex named `GEMINI.md` and confirmed the exact ASD-STE100 line was present. Antigravity also answered the `.gitignore` question in short sentences, one claim per sentence.
- The user entered a Purdue GenAI Studio key and a Purdue SEC User-Agent in the workspace `.env`. A value-safe local check confirmed both fields are populated; `python3.12 check_env.py` read them and masked the key. This confirms file reading only, not key validity or an API call.
- Screenshots shared in chat exposed part of the earlier API key. The user later reported rotating it; an authenticated model-list request confirmed the replacement works. Keep the replacement local in `.env` and never paste it into chat.
- The user reports LSEG, WRDS, and Capital IQ Purdue-email registration is complete.
- The user reports partner sign-off and Brightspace Session 1 checkout are complete. Their individual evidence and submitted contents were not reviewed in this session.
- The user reports the repository is `https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project.git`. An earlier owner-tab check showed it was **Private** and empty; later, the primary Week 2 files and facts were pushed under the user's coursework-upload authorization (see commit `0532342`). Keep it private unless the user separately asks to change visibility. The Lab 01 logged-out public file check remains pending.
- Earlier placeholder-only checks were superseded on 2026-10-26: the user later populated both `.env` fields, and the script read them. The key shown in screenshots was reported rotated; see the credential status above.
- Assigned Francis & Zhang sections, Costco SEC research, and Anthropic through the end of “Prompt chaining” are marked complete in the course notes.
- Draft responses to the two Week 1 preparation questions are now in `WEEK_1_READING_NOTES.md`. Confirm figure-specific interpretation against the supplied paper if needed.

## Pending / blocked / unverified

1. **Credential status:** The user reports the exposed Purdue GenAI Studio key was rotated and the replacement was saved locally. An authenticated model-list request confirmed `qwen3-coder:latest` was available. Keep the key in `.env`; do not show or upload it.
2. **Lab 01 public file check — pending:** The repository is private. The user authorized a private coursework upload, but did not authorize changing visibility. The logged-out Lab 01 check still needs a public repository. Keep the repo private until the user explicitly asks to change its visibility. Verify `.env` stays absent from GitHub.
3. **Partner evidence — user-reported, not independently reviewed:** The user reports partner sign-off and Brightspace Session 1 checkout are complete. The paper initials, partner name, and submitted checkout contents are not in this workspace. The in-class model/harness/agent gap list and reflection also cannot be verified here; complete or confirm these with the partner if needed.
4. **Provider requirement — unverified:** The course's earlier setup notes specified an OpenAI API key. The local key is from Purdue GenAI Studio. Whether this provider satisfies the course requirement is not verified. The script does not validate a key or call the provider.
5. **Errors:** No lab error text was reported. If a check fails, record the exact command and error after removing keys and personal account details.

## GitHub and file safety

The intended repository is private. Earlier notes that it was empty or that no push credential was available predate the later coursework upload. The primary Week 2 files and facts were pushed in commit `0532342`. The current Lab 02 code and README edits are local and have not been pushed. `.env` is ignored. Keep `.env`, `FRL-CanAIReplaceAnalyst.pdf`, `.vscode/`, and `CONVERSATION.md` out of any upload.

## Resume here

Continue with the Lab 02 handwritten audit and partner checks. If you want the latest code edits on GitHub, upload only the intended coursework files; keep `.env` private. Check the partner paper initials, reflection, and Brightspace contents if proof is needed. See [`WEEK_1_SETUP.md`](WEEK_1_SETUP.md) for the Week 1 checklist and [`CONVERSATION.md`](CONVERSATION.md) for the activity log.
