"""
Centralized storage for User Prompts.
"""

USER_PROMPT_PLANNER = """
### TASK:
1. Examine the current Project Plan in 'content'.
2. If 'content' is empty, delegate to 'planner_agent' with stop_reason="CALL".
3. If there are incomplete tasks "[ ]", identify the first one and delegate it.
4. If all tasks are complete "[x]", set stop_reason="END" and provide a summary in 'final_response'.

### CURRENT PROJECT PLAN:
{plan_content}

### INSTRUCTION:
Provide the next step strictly in the required JSON format.
"""

USER_PROMPT_SUPERVISOR = """
Analyze the project plan and current status, then delegate to the next appropriate specialist.
"""

USER_PROMPT_CLASSIFIER = """
Task: Classify this document into its technical domain.
File: {current_file}
"""

USER_PROMPT_ATOMICITY = """
Task: Structure the content of the file provided in the context into XML blocks.
Content: {current_state}
"""

USER_PROMPT_SUMMARIZER = """
Task: Read the atomic XML file and create both technical and human-readable summaries.
File: {current_file}
"""
