# Topolox: Complete Architecture & Flow

## Tagline
The topological memory and architecture layer for AI coding agents.

## Vision
Topolox provides AI coding agents (like Claude Code and Cursor) with an instant, deep understanding of massive codebases. Instead of burning tokens reading thousands of files sequentially, Topolox feeds agents exactly the context they need using a high-performance, embedded hybrid graph and vector engine.

---

## 🆚 Topolox vs. Traditional Tools (e.g., Graphify)

While existing tools validated the market for AI codebase memory, Topolox is built for enterprise-scale speed, concurrency, and real-time agent interaction without relying on single-threaded bottlenecks.

| Feature | Traditional Python Tools | Topolox |
| :--- | :--- | :--- |
| **Concurrency** | Single-threaded | Multiprocessing (CPU) + Asyncio (I/O) |
| **Parsing Speed** | Sequential execution | Multi-core parallel AST extraction (C-level via Tree-sitter) |
| **Storage** | Static JSON dumps | Embedded Kùzu Graph + LanceDB (Vector) |
| **Agent Interface**| Manual CLI / Markdown Reports | Real-time FastMCP server for Claude Code |
| **State Sync** | Manual commands or Git Hooks | `watchdog` Daemon for ms-level live background updates |

---

## ⚡ Core Engine & Concurrency Strategy

Topolox is 100% Python-native but structurally designed to bypass standard bottlenecks:

1. **Bypassing the GIL (Indexing):** Uses `concurrent.futures.ProcessPoolExecutor` to spin up parallel Python processes. Thousands of files are parsed simultaneously across all CPU cores.
2. **Handling I/O (Querying):** The FastMCP server and background Daemon use `asyncio`. This ensures sub-second response times to the user's IDE even while traversing the graph or fetching LLM embeddings.
3. **Embedded Databases:** No external servers required. Runs natively in-process using Kùzu for topological mapping and LanceDB for semantic embeddings.

---

## 🌊 The 4-Phase System Flow

### Phase 1: The Cold Start (Indexing)
1. Run `topolox index .`.
2. Multiple CPU cores parse code simultaneously using the C-based `tree-sitter`.
3. Architectural relationships are saved to the **Kùzu Graph DB**.
4. Semantic meanings are saved to the **LanceDB Vector DB**.

### Phase 2: The Background Watcher (The Daemon)
1. Run `topolox daemon`.
2. Attaches to the file system via `watchdog`, consuming almost zero CPU.
3. Instantly detects file saves, micro-patches only the changed files, and updates the graph in milliseconds.

### Phase 3: The AI Connection (MCP)
1. Run `topolox mcp`.
2. Starts an asynchronous FastMCP server. Claude Code connects and gains instant access to the Topolox Knowledge Engine.

### Phase 4: The Real-Time Agent Loop
1. User asks Claude Code: *"What breaks if I rewrite `auth.py`?"*
2. Claude Code silently queries Topolox: `analyze_blast_radius(filepath="auth.py")`.
3. Topolox traces dependencies via Kùzu, prunes the context, and returns an optimized summary.
4. Claude uses this context to write accurate, safe code updates.

---

## 🪟 The Topolox UI: "Tmux" Style Terminal Dashboard

Instead of building a custom terminal emulator from scratch, Topolox utilizes **Textual** to create a powerful, mouse-supported Terminal User Interface (TUI) powered by `asyncio`.

**3-Pane Layout:**
* **Left Pane (Agent Chat):** Integrated text area to converse with the LLM.
* **Top Right Pane (Knowledge Graph Dashboard):** Real-time visualization of Kùzu queries and blast radius analysis.
* **Bottom Right Pane (Daemon Log):** Live stream of `watchdog` background events and database updates.

## 🛠️ The Tech Stack

* **Language:** Python 3.11+ (Strictly typed, Asyncio, Multiprocessing)
* **Databases:** Kùzu (Graph), LanceDB (Vector)
* **Parsing:** Tree-sitter (via Python bindings)
* **Agent Integration:** FastMCP (Anthropic SDK)
* **File Watcher:** Watchdog
* **User Interface:** Textual (TUI Framework), Typer (CLI base)
