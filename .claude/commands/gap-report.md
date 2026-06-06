Show the most recent ATLAS-SAGE gap report.

Steps:
1. Find the latest gap report: look for `gap-report-*.md` or `gap_report_*.json` in the repo root or an `artifacts/` folder
2. Print a summary:
   - Unparseable files (count + file types)
   - Unresolved edges (count + reason)
   - Low-confidence inferred edges (count)
   - Skills created in the last run
   - Skills still missing (require engineer action)
3. For each missing skill, suggest the next step (create_skill call, manual implementation, or SME escalation)

If no gap report exists yet, note that Sprint 5 (AS-30) has not run yet.
