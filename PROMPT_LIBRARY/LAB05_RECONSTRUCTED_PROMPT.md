# Lab 5 reconstructed prompt

Update my existing agent team.

## Analyst role outputs

Make each analyst role's output end with exactly one `Insight:` line. The line must:

- Begin with `Insight:`.
- State one claim.
- Cite the filing and the line that supports the claim.

## Strategy Manager checks

Add these two checks:

1. A report part fails if it has no `Insight:` line.
2. A report part fails if its `Insight:` line only repeats a figure stated in the first paragraph of the earnings release.

Send each failed part back to its role for one revision only. Keep the current revision limit.

## Verifier

Check the number in each `Insight:` line in the same way as every other sourced number.

## Requirements

- Keep the graph order unchanged.
- Do not name a company in the code.
- Give me the exact command to run the agent team.
