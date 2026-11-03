# Lab 4 use of the Financial Researcher skill

**Date:** 2026-11-03

## What carries into Lab 4

The skill informs the four existing roles. The Research Analyst examines business quality, competitive position, catalysts, and risks from the saved filings. The Financial Analyst uses the Python desk's reported facts and calculated ratios. The Investment Advisor weighs value, growth, quality, and risk using only the first two role outputs. The Manager checks consistency. The Verifier checks claims against saved source files.

The skill's core safeguards also apply: code calculates metrics; roles do not invent missing data; each perspective uses only its assigned evidence; and the report identifies data gaps.

## What does not carry into the Lab 4 runtime

FAskills describes nine separate investor analyses, additional market and news feeds, 13-F data, Financial Datasets MCP, and Tavily MCP. Lab 4 specifies seven existing SEC/XBRL steps, four analyst roles, one fixed graph, and one Verifier. The nine analyses and extra services would change the professor's required workflow. They are not added as runtime agents or data sources.

The installed FAskills package is a coding-agent skill. Its installation does not configure the Financial Datasets or Tavily MCP servers. The Lab 4 flow therefore uses only the sources already collected by the seven-step desk. It does not claim Piotroski, Altman, Beneish, market-price, news, or 13-F results unless the existing desk supplies them.

## Source and version

- Repository: https://github.com/CinderZhang/FAskills
- Installed source revision: `41a6db7916bbfb0124e9a2839f6990e0c60dba6`
- Installed user-level skill paths: `~/.codex/skills/financial-researcher` and `~/.claude/skills/financial-researcher`
