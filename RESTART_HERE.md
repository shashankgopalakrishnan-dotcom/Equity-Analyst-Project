# FIN 67110 Workspace Restart Point

**Workspace:** `/Users/shashankgopalakrishnan/Documents/Courses/Mastering AI for finance`
**Updated:** 2026-11-02
**Course checklist:** [`WEEK_1_SETUP.md`](WEEK_1_SETUP.md)
**Week 2 checklist:** [`WEEK_2/README.md`](WEEK_2/README.md)
**Report run status:** [`WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md`](WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md)
**Audit worksheet:** [`WEEK_2/AUDIT_TEMPLATE.md`](WEEK_2/AUDIT_TEMPLATE.md)
**Conversation log:** [`CONVERSATION.md`](CONVERSATION.md) (local file; not in GitHub)

## Current status

- **Lab 02 data runs:** Completed for COST, WMT, TGT, BJ, AAPL, MSFT, and partner-selected CMG. Saved run folders are under `WEEK_2/runs/`.
- **Lab 03 reports:** Generated sequentially for COST, WMT, TGT, BJ, AAPL, MSFT, and partner-selected CMG. AI-assisted audits and corrected report drafts are saved beside the originals. The user confirmed that AI may be used to complete the audit. See [`WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md`](WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md) for every audit and reviewed-draft path.
- **Audit corrections:** The CMG revenue and capex units were each 1,000x too high; the corrected draft fixes them. The COST P/E-to-peer-margin comparison was invalid; its corrected draft removes that comparison. WMT, TGT, BJ, AAPL, and MSFT now also have corrected drafts.
- **Partner checks:** Not yet confirmed. Ask the partner to check two Lab 02 marks and two claims in the CMG report, and record the source and line for each. The partner should also discuss the reflection questions below.
- **Audit status:** AI-assisted audit is complete for all seven Lab 03 reports under the user's confirmed course allowance. The CMG worksheet also records two older Lab 02 extraction issues and the missing peer filing texts. The corrected Lab 03 CMG draft uses the 10-K debt disclosure and saved Company Facts peer margins.
- **Reflection and submission:** Complete the partner reflection, then submit Checkpoint 1 in Brightspace with the repository commit link. Submission is not verified here.

## Repository and secret status

- **GitHub repository:** [Equity-Analyst-Project](https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project).
- **Visibility:** Public. Verified with GitHub on 2026-11-02. Anyone can view the repository.
- **Latest checked commit:** [`cd9c09ea1599b60fd987374a22c51d4bfe730dd5`](https://github.com/shashankgopalakrishnan-dotcom/Equity-Analyst-Project/commit/cd9c09ea1599b60fd987374a22c51d4bfe730dd5).
- **Partner access:** Since the repository is public, the partner can view it with the link. To restrict access, change visibility in **Settings → Danger Zone → Change visibility**. Then invite the partner in **Settings → Collaborators** and have them accept. A personal private repository grants collaborators write access.
- **Credential check:** `.env` is ignored and is not tracked. A scan of the repository's Git objects found no credential-pattern matches. `.env` stays local. Do not paste, commit, or upload API keys.
- **Excluded local files:** `.vscode/`, `CONVERSATION.md`, the course PDFs, and several extra run folders are untracked. They are not part of the checked GitHub commit.

## Next actions

1. Review the seven audit notes and corrected drafts listed in [`WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md`](WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md).
2. If needed for Lab 02 completion, obtain peer 10-K statement lines for CMG's MCD, YUM, and CAVA margin comparison; the original run did not save those texts.
3. Ask the partner to check two CMG report claims and record the source lines. Complete the partner reflection.
4. Submit Checkpoint 1 in Brightspace with the commit permalink. Submission is not verified here.

## Key report paths

The six baseline reports and the CMG partner-company report are listed in [`WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md`](WEEK_2/LAB03_ALL_TICKERS_RUN_STATUS.md). The CMG report is:

`WEEK_2/runs/CHIPOTLE_MEXICAN_GRILL_INC_20261101_101158_EST/CMG_lab03_report_20261101_101604.md`

The CMG filing texts, manifest, and Company Facts file are in that same run folder. Use the AI-reviewed draft and audit worksheet; the partner check remains outstanding.
