# ATLAS-SAGE: Environment & Setup

**Audience:** anyone opening this repo for the first time, or after a devcontainer rebuild.  
**Primary dev environment:** VS Code devcontainer (`.devcontainer/`). Everything below assumes you are inside it.

---

## 1. Getting started

```bash
# 1. Clone
git clone git@github.com:nitincp/atlas-sage.git
cd atlas-sage

# 2. Pull the eShopOnWeb sample codebase (ingestion test input)
git submodule update --init

# 3. Open in VS Code → "Reopen in Container"
#    devcontainer builds, postCreateCommand runs, extensions install automatically
```

After the container starts, `pip install -r requirements.txt` has already run. Ollama, LiteLLM, LanceDB, and BGE-M3 are available immediately.

---

## 2. Devcontainer

**File:** [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json)

### Base image

```
mcr.microsoft.com/devcontainers/python:3.12
```

**Why Python-specific, not universal:** the `universal` image is ~3 GB and ships runtimes we don't need (.NET, Ruby, Go). The Python image is ~1 GB and is purpose-built for this stack. Claude Code extension is excluded from the devcontainer definition — it is installed at the VS Code host level and propagates into the container automatically.

### Features

| Feature | Why |
|---|---|
| `ghcr.io/devcontainers/features/node:lts` | The Python base image has no Node.js. All MCP servers in `.mcp.json` use `npx` — without this feature they fail silently at container start. |

### Environment variables

| Variable | Value | Why |
|---|---|---|
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Lets Python code and the Ollama MCP server reach an Ollama instance running on the host machine. `host.docker.internal` resolves to the host from inside the container. Also picked up automatically by `litellm` when routing to `ollama/` models. |
| `HF_HOME` | `/workspaces/.cache/huggingface` | HuggingFace model weights (BGE-M3 and others) are stored in the workspace volume, not the container layer. Weights survive `Rebuild Container` — no re-download needed. |
| `SSH_AUTH_SOCK` | `/ssh-agent` | Forwards the host SSH agent into the container so `git push` and submodule operations work without re-entering credentials. |

### SSH agent mount

```json
"mounts": [
  "source=${localEnv:SSH_AUTH_SOCK},target=/ssh-agent,type=bind"
]
```

Binds the host SSH agent socket into the container at `/ssh-agent`. The `postCreateCommand` appends `export SSH_AUTH_SOCK=/ssh-agent` to `~/.bashrc` so every terminal session picks it up.

---

## 3. Python toolchain

**File:** [requirements.txt](../requirements.txt)

| Package | Role | Backlog |
|---|---|---|
| `litellm` | Model-agnostic LLM gateway. Swap between Ollama, Claude, vLLM without code changes. Reads `OLLAMA_HOST` automatically. | AS-40 |
| `ollama` | Python client for local Ollama inference — used when calling models directly rather than through LiteLLM. | AS-41 |
| `sentence-transformers` | Provides BGE-M3 and other embedding models. Used to embed summaries before writing nodes to LanceDB. | AS-07 |
| `lancedb` | Vector + graph store for nodes, edges, communities, and corrections. Not SQLite — schema is defined in ARCHITECTURE.md. | AS-01 |
| `networkx` | Graph representation for community detection traversal. | AS-20 |
| `leidenalg` + `python-igraph` | Leiden algorithm for community detection over AST edges. Leiden outperforms Louvain on resolution. | AS-20 |
| `huggingface_hub` | `huggingface-cli download` to pull BGE-M3 and other models into `HF_HOME` before first run. | AS-07 |
| `pytest` + `pytest-asyncio` | Test runner. `asyncio` mode needed because the orchestrator and tool calls are async. | all sprints |
| `ruff` | Linter and formatter. Configured as the default formatter in `.vscode/settings.json`. | dev toolchain |

---

## 4. VS Code extensions

**File:** [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) — `customizations.vscode.extensions`

| Extension ID | Why |
|---|---|
| `ms-python.python` | Core Python language support. |
| `ms-python.vscode-pylance` | Fast type-checking and IntelliSense via Pyright. |
| `ms-python.debugpy` | Python debugger — step through ingestion pipeline and orchestrator calls. |
| `charliermarsh.ruff` | Ruff linter/formatter integration. Formats on save via `.vscode/settings.json`. |
| `ms-toolsai.jupyter` | Exploratory notebooks for testing BGE-M3 embeddings, LanceDB writes, and Tier-2 prompts before wiring them into the pipeline. Sprint 0 exploration happens here. |
| `humao.rest-client` | `.http` files for testing Ollama REST API, LiteLLM gateway, and OpenAPI route contracts inline — no external tool needed. Sprint 2 skill loop and Sprint 6 HTTP edge matching. |
| `tamasfe.even-better-toml` | Schema-aware `pyproject.toml` editing. |
| `redhat.vscode-yaml` | Skill registry files are YAML. Schema validation and IntelliSense from Sprint 2 onwards. |
| `ms-azuretools.vscode-docker` | Manage Ollama containers from the sidebar. Pull models, check logs, restart — without leaving the IDE. |

---

## 5. MCP servers

**File:** [.mcp.json](../.mcp.json)

MCP servers are started automatically when Claude Code opens the workspace (`enableAllProjectMcpServers: true` in `.claude/settings.json`). All use `npx -y` so no global install is needed — Node.js LTS (devcontainer feature) provides `npx`.

| Server | Package | Why |
|---|---|---|
| `github` | `@modelcontextprotocol/server-github` | PR, issue, and code search operations. Requires `GITHUB_TOKEN` in the environment. |
| `filesystem` | `@modelcontextprotocol/server-filesystem` | Read/write access to `/workspaces/atlas-sage`. Used for gap reports, skill registry files, and ingestion artifacts. |
| `ollama` | `@iflow-mcp/ollama-mcp` | Browse available local models, pull new ones, run ad-hoc inference — without leaving Claude. Community package (v0.1.1). Uses `OLLAMA_HOST` env var. |
| `memory` | `@modelcontextprotocol/server-memory` | Session-scoped knowledge graph. Holds SME correction context across a chat session — complements (does not replace) the LanceDB correction store. Relevant from Sprint 4 (AS-28). |

**Note on `ollama` server:** `@iflow-mcp/ollama-mcp` is a community package, not an official Anthropic server. It is listed here as the best available option; replace if an official Ollama MCP server is published.

---

## 6. Claude Code configuration

**File:** [.claude/settings.json](../.claude/settings.json)

### Permissions

Pre-approved commands so Claude does not prompt on every run:

```
python / python3 — run ingestion, query, and test scripts
pip install      — install deps during setup or when requirements change
pytest           — run test suite
ruff check/format — lint and format
```

### Hooks

`Stop` hook prints a reminder to check `docs/BACKLOG.md` after each Claude session ends. Lightweight orientation — no build step.

---

## 7. Claude Code custom commands

**Directory:** [.claude/commands/](../.claude/commands/)

| Command | Purpose | Backlog |
|---|---|---|
| `/sprint` | Print current sprint status from `docs/BACKLOG.md`: goal, done/total task count, next unchecked task. | orientation |
| `/ingest <path>` | Run the ingestion pipeline on a file or folder. Reports nodes written, edges extracted, skill used, and any gap report entries. If the module is not built yet, reports what AS-task blocks it. | AS-07, AS-09 |
| `/query <question>` | Run an SME query against the knowledge graph. Shows answer, source node IDs, confidence tiers, and prompts for inline correction capture. | AS-08, AS-28 |
| `/gap-report` | Display the most recent gap report: unparseable files, unresolved edges, missing skills, and recommended next actions. | AS-30 |

---

## 8. Sample codebase (eShopOnWeb)

**Submodule:** `eshoponweb/` → `https://github.com/dotnet-architecture/eShopOnWeb`

Used as the ingestion test target throughout all sprints. A real polyglot enterprise codebase: C#, TypeScript, HTML, CSS, configuration. Satisfies Sprint 0 through Sprint 6 exit criteria without needing access to a client codebase.

```bash
git submodule update --init     # first time
git submodule update --remote   # pull latest upstream
```

---

## 9. Hosting Ollama (host machine)

The devcontainer reaches Ollama on the host via `host.docker.internal:11434`. Ollama is not installed inside the container — it runs on the host or in a separate Docker service.

```bash
# macOS / Linux — install and start Ollama on the host
curl -fsSL https://ollama.com/install.sh | sh
ollama serve

# Pull the models used by the pipeline
ollama pull qwen2.5:7b          # Tier-1 candidate — fast routing and classification
ollama pull qwen2.5:32b         # Tier-2 candidate — large context, deep reasoning
ollama pull bge-m3              # embedding model (or use sentence-transformers directly)
```

Model choices are not hardcoded — LiteLLM routes by model string. Swap models by changing the config, not the code.
