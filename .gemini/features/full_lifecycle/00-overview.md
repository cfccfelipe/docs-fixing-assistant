# Feature: Full Document Lifecycle Orchestration

This directory contains the subtasks and agent definitions for implementing a complete documentation lifecycle pipeline. The overarching goal is to transform raw documents into a classified, well-named, structured (XML), summarized, and metadata-rich knowledge base.

## Workflow Sequence
1. `01-classifier-agent.md`: Order and classify documents into target folders.
2. `02-naming-agent.md`: Rename files with significant, mindmap-ready names.
3. `03-atomicity-agent.md`: Convert contents into structured XML chunks.
4. `04-summarizer-agent.md`: Create iterative hierarchical summaries (XML & Human-readable).
5. `05-metadata-agent.md`: Generate Obsidian YAML metadata.

**Goal:** Integrate these subtasks into the `AgentRegistry` and update the core `PlannerAgent` to generate tasks sequencing these 5 phases.