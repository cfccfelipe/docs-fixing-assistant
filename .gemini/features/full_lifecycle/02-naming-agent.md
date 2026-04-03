# Subtask 2: Naming Agent Refinement

## Description
The Naming Agent ensures files have significant, mindmap-ready names.

## Subtasks
- [ ] Review existing `SYSTEM_PROMPT_NAMING` in `src/domain/orchestrator/constants/system_prompts.py`.
- [ ] Ensure the prompt explicitly instructs the generation of a concise, mindmap-significant name.
- [ ] Ensure the agent uses filesystem tools (`write_file`, `delete_file`) to rename the physical file to the generated name.
- [ ] Write/verify integration test for the renaming process.