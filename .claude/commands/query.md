Run an SME query against the ATLAS-SAGE knowledge graph.

Usage: /query <natural language question>

Steps:
1. Run: `python -m atlas_sage.query "<question>"`
2. Show the answer and the node_id(s) it was assembled from
3. Show the confidence tier of each edge in the assembled context (deterministic / probabilistic / inferred)
4. If any inferred edges were used, flag them — these are SSR speculation candidates
5. Prompt: "Is this answer correct? If not, describe the correction." — capture any correction the user provides and run the correction store path

If the query module doesn't exist yet, report what needs to be built (AS-08) rather than failing silently.
