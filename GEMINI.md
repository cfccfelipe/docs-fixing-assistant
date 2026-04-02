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
- **SupervisorNode (Inherits BaseNode):** Lead Architect & Intent Router. Analyzes the `Project Plan` (stored in `state.content`) to delegate tasks.
- **WorkerFactory:** Surgically assembles specialized `BaseWorkerNode` instances by injecting specific agent configurations and system prompts.

### 2. Registry Pattern
- **AgentRegistry:** Inventory of initialized nodes. Maps agent IDs to their respective node instances.
- **ToolRegistry:** Bridge between LLM intent and actual implementation. All infrastructure tools MUST be registered here. 
  - **Current Capability:** Currently, the toolset is exclusively focused on **File System Management** (list, read, write, delete). Future expansions may include search or external API integrations.

### 3. Model Integrity
- **No Duplication:** Data models and DTOs MUST reside in `src/domain/models`. Avoid creating redundant models in other layers.
- **State Management:** Use `AgentState` for tracking workflow progress and `StateUpdate` for node transitions.

## 🛠 Tech Stack
- **Runtime:** Python 3.12+ (managed via `uv`)
- **Orchestration:** LangGraph (Stateful multi-agent workflows)
- **Inference:** Ollama (Optimized for 8B models: Llama 3, Qwen 2.5)
- **API Framework:** FastAPI
- **Parsing & Validation:** `lxml`, `defusedxml`, Pydantic V2
- **Storage:** Local File System (Obsididan/VS Code compatible structures)

## 📐 Engineering Standards (Strict)

### 1. Architecture & Design
- **Hexagonal / DDD:** Maintain strict separation between **Infrastructure** (adapters, tools), **Domain** (logic, entities), and **Application** (orchestrator, nodes).
- **Patterns:** Use Repository, Strategy, and Dependency Injection to ensure testability.
- **Python Style:** Object-Oriented (OO). Use concise docstrings. **NO comments** within the code.
- **80/20 Rule:** Prioritize simplicity and results. If a feature is ambiguous, implement the 20% effort that provides 80% of the value.

### 2. Testing Strategy
- **Structure:** Integration tests are separated from Unit tests.
- **Shadowing:** Tests MUST follow the exact same folder structure as the `src/` directory.
- **Pattern:** Use the **AAA** (Arrange, Act, Assert) pattern.
- **Scope:** Focus only on **core functionality** initially; avoid over-testing edge cases.

### 3. Workflow & CI/CD
- **Automation:** Use `uv`, `ruff`, `mypy`, `pytest`, `ty`, and a `Makefile` for local tasks.
- **Configuration:** All environment variables in `config/local.env` and secrets in `config/secrets.json`.
- **Integrity:** Use `.github` for workflows, `CODEOWNERS`, and PR templates. Implement pre-commit/pre-push hooks to guarantee formatting.

### 4. Feedback Loop
- **Memory:** Post-hook feedback should update `GEMINI.md` or the relevant agent configuration.

## 📐 Surgical Agent Design (SDD Standard)
To mitigate small context window limitations, every new agent must follow this "Single Responsibility" design:
1. **Input:** Strictly defined (e.g., a single XML fragment or a list of filenames).
2. **System Prompt:** Optimized for 8B models (Noun-first, no prose, zero-shot/few-shot examples).
3. **Tool Access:** Limited to ONLY the tools required for its specific task.
4. **Validation:** MUST pass through a dedicated `Infrastructure/Parser` before the state is updated.
5. **Persistence:** Results must be written to disk immediately to keep the memory footprint low.

### 1. Prompt Management
- **Centralized Constants:** All system and user prompts MUST be defined in `src/domain/orchestrator/constants/system_prompts.py` or `src/domain/constants/users_prompts.py`.
- **Optimization:** Prompts are optimized for **8B Parameter Models** (Ollama: Llama3, Qwen2.5).
- **Dynamic Formatting:** Use `{state}`, `{current_state}`, and `{plan_content}` placeholders within prompts for runtime context injection.
- **Stop Sequences:** Always use `stop=["}\n", "###", "User:"]` in `BaseNode` to ensure clean JSON termination.

### 2. Specialized Agents (Small Tasks)
To handle small context windows and ensure precision, tasks are broken down into specialized agents:
- **planner_agent:** Explores folders, maps dependencies, and initializes the Project Plan.
- **atomicity_agent:** Transforms raw text into `<atomic_structure>` XML.
- **reorder_agent:** Consolidates and reorders XML nodes for logical flow.
- **tag_agent:** Generates Obsidian-compatible YAML properties.
- **matrix_agent:** Produces Fast Recall Matrices (Value vs. Complexity).
- **diagram_agent:** Renders Mermaid.js architectural diagrams.
- **coder_agent:** Performs filesystem operations (create/rename/update) using registered tools.

### 4. Code Maintenance
- **Dead Code Removal:** Upon the successful completion of a Project Plan or a major migration phase, all redundant or "dead" code (e.g., legacy service layers, unused endpoints, or superseded DTOs) MUST be surgically removed to maintain system health and prevent technical debt.

## 🔄 Workflow Logic
1. **Initialization:** If `state.content` (Project Plan) is empty, Supervisor MUST route to `planner_agent`.
2. **Analysis:** `planner_agent` uses `list_files` and `read_file` tools to understand the current state and populate the task list in `state.content`.
3. **Execution:** Supervisor identifies the first pending task `[ ]` in the plan and delegates to the appropriate specialized agent.
4. **Tool Use:** Specialized agents use tools to read input and write output files.
5. **Iteration:** Workers return control to Supervisor after each task update.
6. **Completion:** When all tasks are `[x]`, Supervisor sets `stop_reason` to `END` and provides a `final_response`.

## 🗺️ Migration Roadmap

### Phase 1: Core Orchestration (The Brain & Navigator)
- **Objective:** Establish the supervisor-led routing and initial folder analysis.
- **Steps:**
    1. **Implement `PlannerAgent`:** Define the system prompt in `system_prompts.py` to analyze folder structures and generate a Markdown task list.
    2. **Initialize `AgentRegistry`:** Register the `SupervisorNode` and the newly created `PlannerAgent`.
    3. **Bootstrapping Logic:** Ensure `SupervisorNode` correctly identifies an empty `state.content` and routes to the `PlannerAgent`.
    4. **Validation:** Verify the state update correctly populates the `next_task` and `content` fields.

### Phase 2: Specialist Integration (The Workers)
- **Objective:** Wrap existing agent logic into the `BaseWorkerNode` hierarchy.
- **Steps:**
    1. **Worker Factory Assembly:** Use `WorkerFactory` to create node instances for `atomicity_agent`, `reorder_agent`, `tag_agent`, etc.
    2. **Logic Mapping:** Port existing logic from `src/domain/agents/` to the `BaseWorkerNode` configuration.
    3. **Tool Injection:** Register `FileSystemTools` in the `ToolRegistry` and inject them into the worker nodes.
    4. **Task Delegation:** Test the Supervisor's ability to pick a `[ ]` task from the plan and route it to the correct specialist.

### Phase 3: Unified API Entry (The Interface)
- **Objective:** Expose the orchestrator through a single, robust FastAPI endpoint.
- **Steps:**
    1. **New Route:** Create `src/api/routes/orchestration.py` with a `/run` endpoint.
    2. **State Initialization:** The endpoint must accept a `folder_path`, initialize `AgentState`, and start the execution loop.
    3. **Stream/Async Support:** Implement proper async handling for long-running folder fixes.
    4. **Telemetry Integration:** Return consolidated metadata (tokens, duration) from `state.metadata` in the final response.

### Phase 4: Final Cleanup (Dead Code Removal)
- **Objective:** Sanitize the codebase by removing legacy service layers.
- **Steps:**
    1. **Decommission Services:** Delete `FixingService`, `ReorderingService`, and `StrategicService`.
    2. **Route Cleanup:** Remove old endpoints in `api/routes/` that are now redundant.
    3. **Schema Refinement:** Consolidate any duplicate models or DTOs in `src/domain/models`.
    4. **Regression Testing:** Run the full integration suite to ensure the new orchestrator-led flow is stable and complete.

## 🛡️ Resilience & Strategy
...
### 1. Circuit Breakers
- **Iteration Limit:** Every node MUST respect the `max_iterations` circuit breaker defined in `BaseNode`. This prevents infinite loops and uncontrolled token consumption in 8B models.
- **Error Thresholds:** If an agent fails validation (via Parser) more than 3 times consecutively, the Supervisor MUST escalate to an `ERROR` state rather than retrying.

### 2. Provider Abstraction
- **Port-Adapter Pattern:** All LLM interactions MUST go through `LLMProviderPort`. Core logic should NEVER depend on provider-specific SDKs (e.g., direct Ollama calls).
- **Swap-Ready:** The system must remain capable of switching from Ollama (local) to Bedrock/OpenAI (cloud) by simply changing the infrastructure adapter.

### 3. Chunking & Large Files
- **Context Management:** For files exceeding the 8B model's context window, the `planner_agent` MUST implement a "Chunked Processing" task.
- **Strategy:** Prefer "Atomic Chunking" (splitting by headers/XML tags) over arbitrary character limits to preserve semantic meaning.

## 🔮 Future Session Recommendations
- **Self-Correction Loop:** Implement a "Reflector" pattern where agents receive their own parser errors as feedback for a single automated retry.
- **Human-in-the-loop (HITL):** Introduce a "Verification" state for the Supervisor where high-impact filesystem changes (e.g., `delete_file`) require user confirmation via the API.
- **Evaluation Framework:** Develop an automated scoring system to compare 8B model outputs against "Golden Answers" to measure documentation quality improvements.
- **ML Integration:** Move beyond GenAI by incorporating traditional ML for document classification and clustering to assist the `planner_agent`.
