# my-llm-agent

A minimal terminal coding agent built on Pydantic AI: a persistent REPL, a tool-calling
agent loop, per-session storage, long-term memory, sub agents, progressive skills, and a
read-only plan mode.

## Requirements

- Python 3.12 (provisioned by uv)
- [uv](https://docs.astral.sh/uv/)
- A real terminal (TTY): the UI is built on prompt_toolkit
- Linux, macOS or Windows; Linux is the target deployment platform

## Install

```bash
uv sync --frozen
```

`uv sync` creates `.venv` from `uv.lock` and installs the `ruff` dev dependency.

## Configure

The model endpoint comes from the environment. With no `LLM_*` variables set the app
talks to the hosted DeepSeek API:

```bash
cp .env.example .env      # then set API_KEY
uv run --env-file .env python main.py
```

To use a self-hosted OpenAI-compatible server, point it at the endpoint instead:

```bash
LLM_BASE_URL=http://127.0.0.1:8000/v1 \
LLM_MODEL=Qwen3-0.6B \
LLM_API_KEY=local \
LLM_CONTEXT_WINDOW=32768 \
LLM_JSON_MODE=0 \
LLM_MAX_COMPLETION_TOKENS=0 \
LLM_STRICT_TOOLS=0 \
uv run python main.py
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_BASE_URL` | DeepSeek API | OpenAI-compatible base URL, including `/v1` |
| `LLM_MODEL` | `deepseek-flash` | Model id served by the endpoint |
| `LLM_API_KEY` | `API_KEY`, else `local` | Key; a placeholder works for keyless local servers |
| `LLM_CONTEXT_WINDOW` | `131072` | Must match the server's real context size |
| `LLM_JSON_MODE` | `1` | Set `0` when `response_format` is unsupported |
| `LLM_MAX_COMPLETION_TOKENS` | `1` | Set `0` to send `max_tokens` instead |
| `LLM_STRICT_TOOLS` | `1` | Set `0` when strict tool schemas are rejected |

Variables can also live in `.env` and be loaded with `uv run --env-file .env python main.py`.

## Run

```bash
uv run python main.py
```

Slash commands (autocompleted in the input line):

| Command | Purpose |
| --- | --- |
| `/help` | list every command |
| `/new` / `/resume` | start a new session / reopen a past one |
| `/rewind` | roll both files and conversation back to a checkpoint |
| `/compact [instructions]` | compact the context, optionally with extra guidance |
| `/status` | model, permission mode, history size, context usage |
| `/memory` / `/dream` | inspect long-term memory / consolidate it now |
| `/agents` | list the sub agent types available to `run_agent` |
| `/mcp` | MCP server status and tools |
| `/jobs` | background jobs |
| `/api-detail` | model API calls from the last round |
| `/exit` | quit |

`Shift+Tab` cycles the permission modes: `default → acceptEdits → plan → auto → bypass`.

## Deploying on a Linux server

The app is an interactive TUI, so run it on a TTY: an SSH session, `tmux`/`screen`, or a
service configured with a pty. It is not a headless daemon.

```bash
git clone <repo> && cd my-llm-agent
uv sync --frozen
uv run --env-file .env python main.py
```

Server notes:

- **Locale.** All file I/O passes `encoding="utf-8"` explicitly, so transcripts and task
  state survive a `LANG=C` environment. Still set a UTF-8 locale
  (`export LANG=en_US.UTF-8`) so the TUI glyphs render correctly.
- **Clipboard images.** Pasting images requires `xclip` and an X display. On a headless
  server the paste shortcut does nothing; reference images with `@path` instead.
- **git.** @-mention completion uses `git ls-files`, so the `git` binary is expected.
- **Data.** Everything is stored in `./.my-llm-agent/` inside the repository; back up
  that directory, and keep it out of the repository history (already gitignored).

## Data directory

```
<repo>/.my-llm-agent/
├── agents/                        custom sub agent definitions (tracked)
├── skills/                        custom skills (tracked)
└── projects/<encoded-path>/
    ├── memory/                    long-term memory shared by every session
    └── sessions/<session-id>/     one self-contained bundle per session
        ├── transcript.jsonl
        ├── meta.json
        ├── tasks/
        ├── jobs/
        ├── file-history/
        ├── images/
        ├── archives/
        └── plans/
```

`projects/<encoded-path>` is the absolute project path flattened with dashes, so sessions
of different repositories never mix.

## Project layout

```
main.py           entry point and event loop
agent/            agent wiring, hooks, tools, sub agents, skills, plan mode, compaction
state/            sessions, task store, file history, background jobs
security/         permission modes, approval flow, LLM classifier
media/            clipboard images and @-mention ingestion
integrations/     MCP server lifecycle
memory/           long-term memory storage, recall, background extraction
core/             shared path discovery and console primitives
ui/               persistent REPL and slash commands
```

## Development

```bash
uv run ruff check .
uv run ruff format --check .
```

Style: line length 100, target Python 3.12, imports sorted, PEP 604/585 typing.
