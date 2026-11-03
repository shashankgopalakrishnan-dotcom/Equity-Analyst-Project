# Lab 04: Orchestrator, Evaluator, and Reflection

## Orchestrator and evaluator

### What is it?

The **Strategy Manager** is closest to Anthropic's **orchestrator-workers** pattern. It reviews the specialist roles' sections, asks a role to revise a failing section once, and compiles the report. The Flow code sets the node order. The Manager's model call does not choose the next graph node.

The **Verifier** is closest to the evaluator in **evaluator-optimizer**. It checks the compiled report against the saved filings and facts. The Verifier marks claims and corrects claims that the saved evidence does not support. In this implementation, it does not send the report back through another role call. The code saves a verified report after the check.

### What does the Verifier receive?

The Verifier receives a JSON task, context, and expected output. Its context contains the compiled report sections under review, saved filing texts, and saved facts. It does not receive the Investment Advisor's thesis or section. The Verifier also receives its own instructions from `roles/verifier.md`.

The Verifier does not receive the other roles' instructions. It does not receive the omitted Investment Advisor thesis. This separation lets it check the claims against the saved evidence without reading how the analyst roles were told to interpret that evidence.

### Why could role instructions make the Verifier weaker?

If the Verifier reads the analyst instructions, it may follow the same assumptions or definitions as the analysts. It may then confirm their claims instead of checking each claim independently against the filing. The Verifier should use its own checking rules and the saved evidence.

## Reflect: partner explanation

1. **One thing a model decided in Lab 03 that code decides now:** In Lab 03, the Strategy Manager model could choose which role should revise a failing section. In Lab 04, the Flow code fixes the normal node order and always runs the Verifier after the Manager. The Manager can still identify a section for one revision, within the code's limit.
2. **One thing the Verifier cannot catch by design:** It cannot check whether the Investment Advisor's thesis is correct. The Flow removes that section before the Verifier call. The verified report therefore does not certify that thesis.

These are prepared answers for the partner discussion. The discussion itself is not recorded as complete here.
