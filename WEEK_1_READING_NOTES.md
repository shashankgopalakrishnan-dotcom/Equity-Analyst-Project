# Week 1 reading notes

## Francis & Zhang (2026)

**Citation:** Austin Francis and Cinder Xinde Zhang, “Can AI Match Professional Analysts? Evidence from a Multi-Agent System,” *Finance Research Letters*, vol. 103 (2026), article 110127. DOI: https://doi.org/10.1016/j.frl.2026.110127. The course also points to the authors' SSRN manuscript: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5584131.

**Publicly visible abstract / introduction takeaways:** The study compares 50 matched pairs of AI-generated and Value Line reports for U.S. firms in 2024Q3. Evaluations are blinded and include language-model judges, finance graduate students, and general-population readers. Non-expert readers perceive the AI reports as comparable or better; the MSF-student sample is split and underpowered; LLM-judge results vary by model. Neither AI nor Value Line recommendations outperform an equal-weight 1/N benchmark in the reported portfolio tests. The authors distinguish report quality from investment performance.

**Assigned reading status:** Read from the supplied full-text PDF on October 22, 2026: Introduction, Section 3.1, and Section 4. Study notes follow. The paper also provides useful limitations in Section 5, noted briefly below, but the main summary stays focused on the assigned sections.

### Study guide: assigned sections

#### Introduction: question, motivation, and contribution

- **Problem:** Equity research requires costly synthesis of filings, earnings calls, industry conditions, and market developments. Coverage gaps may leave some firms with more information asymmetry and slower price discovery. The authors ask whether a multi-agent system can produce full-length equity research comparable in perceived quality to a professional benchmark.
- **Why multiple agents:** A single model may struggle to handle long, varied inputs and maintain consistency. Specializing and sequencing work is intended to divide the task into more manageable stages and allow a coordinating agent to check completeness and consistency.
- **Study design at a glance:** The authors produce research reports for 50 U.S. firms in 2024Q3 and match each one to a Value Line report for the same firm and quarter. Blinded evaluators include multiple language-model judges, 15 MSF students, and a larger non-expert Prolific sample.
- **Main distinction:** Report quality as perceived by readers is not the same outcome as investment performance. The introduction previews that non-expert readers view the AI reports favorably, but the recommendations do not beat equal-weight diversification in the reported tests.
- **Contribution and scope:** The authors study end-to-end analyst-style narrative production, evaluator differences, and portfolio performance. They frame this 2024Q3 work as a pre-contamination baseline, before widespread analyst adoption of AI-intensive workflows. Professional analysts were not the adequately powered human evaluator group, so expert acceptance remains an open question.

#### Section 3.1: how the multi-agent system works

- **Architecture:** Four hierarchical agents use GPT-4o in CrewAI. A Strategy Manager coordinates three specialists: a Research Analyst, a Financial Analyst, and an Investment Advisor.
- **Research Analyst:** Covers qualitative business analysis, competitive position, catalysts, recent developments, and filings; tools include web search and SEC filing parsers.
- **Financial Analyst:** Calculates financial-statement measures, ratios such as P/E, debt-to-equity and ROE, growth metrics, and peer comparisons; it has SEC, web-search, and calculator tools.
- **Investment Advisor:** Integrates the upstream analysis into a thesis and Buy/Hold/Sell recommendation, relying mainly on the team's internal outputs.
- **Manager and workflow:** The manager assigns tasks in sequence, passing task, context, and expected output as structured JSON. Agents return markdown findings in JSON. The manager applies a five-part report template, checks completeness and consistency, and can send targeted revision instructions. The paper describes qualitative research, filings analysis, financial analysis, and final recommendation as the four workflow steps.
- **Useful interpretation:** The system is a controlled workflow with specialized model calls and tools, not simply four independent chatbots. Specialization decomposes work; the manager provides coordination and a revision loop. The paper does not establish that this particular architecture is superior to a single-model baseline, because that is not the reported comparison.

#### Section 4: what the results show

- **Human report ratings:** Prolific evaluators gave the system reports a mean quality score of 8.129 versus 6.644 for Value Line (difference 1.485, p < 0.01) and preferred the system report in 76.8% of comparisons. The 15 MSF students gave scores of 7.088 versus 6.466; this difference was not statistically significant, and their choices were nearly even (51.1%). The student sample is small and explicitly described as underpowered, so it is not evidence of equivalence.
- **LLM judges:** Across four judge models, average score favored the system overall, but model-level preference varied widely: Gemini 2.5 preferred the system 48% of the time, Gemma 3 96%, MistralNemo 56%, and Llama 3.1 82%. That spread cautions against treating one LLM judge as an objective measure of quality.
- **Analyst coverage:** Prolific ratings favored the system in both above- and below-median analyst-coverage groups, with a larger gap among lower-coverage firms (1.833 versus 1.098 points). Student and LLM patterns were less conclusive. This is suggestive of a possible role in information-sparse settings, not proof that the system closes the coverage gap in practice.
- **Portfolio performance:** The equal-weight 1/N benchmark returned 2.89% over one month versus 1.87% for the system's Buy portfolio and 1.47% for Value Line. At two months, returns were 1.43%, 1.63%, and 1.40%, respectively. None of the strategy-versus-benchmark differences was statistically significant; six-factor alphas were also insignificant.
- **Interpretation:** The evidence supports favorable perceived narrative quality among non-experts in this blinded, matched-report exercise. It does not show that AI reports produce alpha or that professional analysts judge them equally. The authors' proposed value is potentially lower-cost synthesis and broader coverage, not demonstrated stock-picking outperformance.

#### Questions to bring to class

1. If the four-agent manager workflow is compared only with Value Line reports, what can we conclude about agent quality—and what would a single-model control add?
2. How might the Prolific results change if participants were asked to assess factual accuracy, valuation quality, or calibrated uncertainty separately from readability and actionability?
3. What validation, citations, and human review would be needed before using the system's recommendation in a client-facing research process?
4. Why can a report be preferred by readers while its recommendations fail to beat 1/N, and what does that imply for how we evaluate an AI research desk?

**Scope note:** These are concise notes from the assigned sections, not a claim that the study establishes professional analyst replacement, causal productivity gains, or investment alpha. Section 5 reiterates that the most supportable application is assistive drafting and synthesis, with domain-specific judgment retained by humans.

### Week 1 pre-class responses (draft, October 26, 2026)

1. **What did the paper not verify?** It did not show that this multi-agent workflow outperforms a single-model workflow, that professional analysts would accept its reports, or that its recommendations generate statistically significant alpha.
2. **Is Figure 1 a workflow or an agent?** Figure 1 is best described as an agent-driven workflow: a strategy manager coordinates specialist agents through an ordered analysis process.

These are concise draft responses based on the assigned-section notes above. Check the figure in the supplied paper if the instructor expects a different label or a figure-specific detail.

## Anthropic, “Building effective agents”

**Read through the end of the first workflow section, “Prompt chaining.”** Source: https://www.anthropic.com/engineering/building-effective-agents

- A **model** is the language model that interprets input and generates output.
- A **harness** is the surrounding software that supplies context and tools, controls the model/tool loop, and handles execution, permissions, and results. This is a practical working definition for the course discussion.
- An **agent** uses a model within that harness to act toward a task. Anthropic distinguishes fixed-path **workflows** (code decides the sequence) from **agents** (the model dynamically directs its process and tool use).
- **Prompt chaining**, the first workflow, breaks a task into fixed steps. Each model call consumes the previous step's output. Programmatic checks can gate progress. It fits tasks that decompose cleanly; smaller calls may improve accuracy at the cost of latency.
- Anthropic's examples are drafting copy and then translating it, or drafting an outline, checking it against criteria, then writing the document from the outline.
