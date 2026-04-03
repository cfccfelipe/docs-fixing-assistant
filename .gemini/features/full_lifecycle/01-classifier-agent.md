# Subtask 1: Classifier Agent Implementation

## Description
The Classifier Agent is responsible for reading a raw document and deciding its optimal folder classification (e.g., `Architecture/`, `Operations/`, `Research/`, `Implementation/`).

## Subtasks
- [ ] Define `SYSTEM_PROMPT_CLASSIFIER` in `src/domain/orchestrator/constants/system_prompts.py`.
- [ ] Create `ClassifierAgent` logic (or just rely on `BaseWorkerNode` wrapper with the prompt).
- [ ] Ensure the agent utilizes `read_file`, `write_file`, and `delete_file` tools to move the content to the new folder and remove the original file.
- [ ] Write integration test mocking the classification flow.