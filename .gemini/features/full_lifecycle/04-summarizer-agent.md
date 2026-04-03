# Subtask 4: Iterative Summarizer Agent

## Description
The Summarizer Agent takes the output of the Atomicity Agent and creates both technical XML summaries and human-comfortable Markdown summaries. It operates iteratively: summarizing deep child nodes first, then bubbling up to a root summary.

## Subtasks
- [ ] Create `SYSTEM_PROMPT_SUMMARIZER` instructing bottom-up summary generation.
- [ ] Ensure it reads the `<atomic_structure>` XML.
- [ ] Instruct the agent to inject `<summary>` tags inside `<topic>` tags within the XML.
- [ ] Instruct the agent to produce a separate Human-Comfortable Markdown file (e.g., in `summaries/` directory) with headers and bullet points.
- [ ] Write integration test verifying both outputs (XML enriched + Markdown).