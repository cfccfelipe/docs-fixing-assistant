USER_PROMPT_SUPERVISOR = """
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
