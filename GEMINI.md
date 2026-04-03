# GEMINI.md - Docs Fixing Assistant

## 🎯 Project Vision & Goals
The **Docs Fixing Assistant** is an AI-powered POC designed to resolve "documentation debt" by autonomously organizing and fixing documentation folders.
- **Objective:** Input a folder → Supervisor iterates → Output: Ordered atomic topics.
- **Key Strategy:** Generate 80% results from 20% content through iterative summarization and strategic extraction.
- **Output Artifacts:** Atomic XML structures, Fast Recall Matrices, Mermaid diagrams, Flashcards, and Case Studies.

## 🏗 Architectural Mandates

### 1. Orchestration & Node Hierarchy
The system follows a strict hierarchical node structure for task execution:
- **BaseNode:** Core execution engine. Handles context filtering, JSON auto-healing, and telemetry.
- **BaseWorkerNode (Inherits BaseNode):** Specialist executor. Integrates with the `ToolRegistry` to perform infrastructure actions.
- **SupervisorNode (Inherits BaseNode):** Lead Architect & Intent Router. Analyzes the `Project Plan` to delegate tasks.
- **WorkerFactory:** Surgically assembles specialized `BaseWorkerNode` instances by injecting specific agent configurations and system prompts.

### 2. Registry Pattern
- **AgentRegistry:** Inventory of initialized nodes. Maps agent IDs to their respective node instances.
- **ToolRegistry:** Bridge between LLM intent and actual implementation. All infrastructure tools MUST be registered here. 

### 3. Model Integrity
- **No Duplication:** Data models and DTOs MUST reside in `src/domain/models`. Avoid creating redundant models in other layers.
- **State Management:** Use `AgentState` for tracking workflow progress and `StateUpdate` for node transitions.

## 🛠 Tech Stack
- **Runtime:** Python 3.12+ (managed via `uv`)
- **Orchestration:** LangGraph (Stateful multi-agent workflows)
- **Inference:** Ollama (Optimized for 8B models: Llama 3, Qwen 2.5)
- **API Framework:** FastAPI
- **Parsing & Validation:** `lxml`, `defusedxml`, Pydantic V2
- **Storage:** Local File System (Obsidian/VS Code compatible structures)

## 📐 Engineering Standards (Strict)

### 1. Architecture & Design
- **Hexagonal / DDD:** Maintain strict separation between **Infrastructure** (adapters, tools), **Domain** (logic, entities), and **Application** (orchestrator, nodes).
- **Patterns:** Use Repository, Strategy, and Dependency Injection to ensure testability.
- **Python Style:** Object-Oriented (OO). Use concise docstrings. **NO comments** within the code.
- **80/20 Rule:** Prioritize simplicity and results. If a feature is ambiguous, implement the 20% effort that provides 80% of the value.

## 🔄 Workflow Logic (LangGraph Orchestrator)
1. **Initialization:** Planner Agent explores folders and generates an initial `PLAN.md` (Markdown Task List).
2. **Deterministic Routing:** Supervisor Node performs a deterministic read of `PLAN.md`. It extracts the `next_agent` from the first `- [ ]` task and routes the graph state directly to that node.
3. **Execution:** LangGraph enforces the workflow sequence. Each worker node performs its file operation and returns to the Supervisor.
4. **State Persistence:** Each successful worker execution triggers an automatic update to `PLAN.md`, marking the task as `[x]`, ensuring crash recovery.
5. **Completion:** When `PLAN.md` contains no `- [ ]` tasks, the graph terminates via `END`.

## 🛠 Tech Stack Update
- **Orchestration:** LangGraph (Stateful graph-based multi-agent workflows).
- **Persistence:** Local file system `PLAN.md` (Atomic tracking).
- **Execution:** Deterministic routing (Supervisor + Registry), replacing probabilistic LLM routing.

## 🗺️ Migration Roadmap

### Feature Blueprint: Full Document Lifecycle Orchestration
A new comprehensive documentation pipeline is being planned. The subtasks and architectural blueprints for this feature are stored in `.gemini/features/full_lifecycle/`. 

### Phase 1: Core Orchestration (The Brain & Navigator) - **COMPLETED**
- **Objective:** Establish the supervisor-led LangGraph routing and initial folder analysis.
- **Milestones:**
  1. **Planner Agent:** Implemented to analyze structure and generate `PLAN.md`.
  2. **LangGraph Implementation:** Migrated from manual loops to `StateGraph` for deterministic orchestration.
  3. **Task Tracking:** Persistence established via `PLAN.md` with incremental `[ ]` to `[x]` transitions.
  4. **Validation:** E2E integration tests confirmed for sequential routing and state recovery.

### Phase 2: Specialist Integration (The Workers) - **IN PROGRESS**
- **Objective:** Wrap existing agent logic into the `BaseWorkerNode` hierarchy.
- **Status:** Registry and `WorkerFactory` fully operational. Agent-specific business logic implementation now required.

### Phase 3: Unified API Entry (The Interface)
- **Objective:** Expose the orchestrator through a single, robust FastAPI endpoint.

### Phase 4: Final Cleanup (Dead Code Removal)
- **Objective:** Sanitize the codebase by removing legacy service layers and refining schemas.

## 🛡️ Resilience & Strategy
... (omitted for brevity)
