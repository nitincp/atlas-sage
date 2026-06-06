Run the ATLAS-SAGE ingestion pipeline on a target file or directory.

Usage: /ingest <path>   (relative to repo root, e.g. eshoponweb/src/Web/Controllers/OrderController.cs)

Steps:
1. Confirm the target path exists
2. Run the ingestion entry point: `python -m atlas_sage.ingest <path>`
3. Report: how many nodes written, edges extracted, skill used, any gap report entries
4. If the skill registry had no skill for the file type, report what skill was created
5. Show the node_id(s) written so they can be used in /query

If the ingestion module doesn't exist yet, report what needs to be built (AS-01 through AS-07) rather than failing silently.
