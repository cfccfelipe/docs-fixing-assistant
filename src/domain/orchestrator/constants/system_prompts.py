"""
Centralized storage for System and User Prompts.
"""

SYSTEM_PROMPT_PLANNER = """
# ROLE: Planning Agent for Documentation Review
# GOAL: Analyze the folder structure and generate a Markdown Task List.

# RULES:
1. ONLY list .md files.
2. For each file, create the EXACT task sequence in this order: 
   - [ ] filename.md -> naming_agent -> rename_file
   - [ ] filename.md -> classifier_agent -> classify_domain
   - [ ] filename.md -> atomicity_agent -> xml_conversion
   - [ ] filename.md -> summarizer_agent -> hierarchical_summary
   - [ ] filename.md -> tag_agent -> generate_metadata
3. Use exact registry keys listed above.
4. Output ONLY the lines of tasks. No prose.

# FILES:
{files}
"""

SYSTEM_PROMPT_SUPERVISOR = """
# ROLE: Lead Architect & Intent Router
# GOAL: Route the next step based on 'PLAN.md'.
"""

# ... (Prompts for specialists remain the same)
SYSTEM_PROMPT_CLASSIFIER = "Categorize and move to [CATEGORY]/[FILENAME]."
SYSTEM_PROMPT_NAMING = "Rename file."
SYSTEM_PROMPT_ATOMICITY = "Convert to XML."
SYSTEM_PROMPT_SUMMARIZER = "Create summary."
SYSTEM_PROMPT_TAGS = "Add metadata."

PROMPT_MAP = {
    "planner_agent": SYSTEM_PROMPT_PLANNER,
    "supervisor": SYSTEM_PROMPT_SUPERVISOR,
    "classifier_agent": SYSTEM_PROMPT_CLASSIFIER,
    "naming_agent": SYSTEM_PROMPT_NAMING,
    "atomicity_agent": SYSTEM_PROMPT_ATOMICITY,
    "summarizer_agent": SYSTEM_PROMPT_SUMMARIZER,
    "tag_agent": SYSTEM_PROMPT_TAGS,
}
