# Phase 3: Unified API Entry (The Interface)

## Objective
Expose the orchestrator through a single, robust FastAPI endpoint.

## Subtasks
- [ ] Create `src/api/routes/orchestration.py` with a `/run` endpoint.
- [ ] Implement `AgentState` initialization accepting a `folder_path` and `user_prompt`.
- [ ] Construct the synchronous/asynchronous execution loop calling the `SupervisorNode` and `AgentRegistry`.
- [ ] Implement proper async handling and stream support for long-running folder fixes.
- [ ] Return consolidated metadata (tokens, duration) from `state.metadata` in the final API response.
- [ ] Ensure API Key authentication is wired up properly on this new endpoint via dependencies.