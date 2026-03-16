"""
Dynamic User Prompts (Tasks) for the Fixing Pipeline.
Optimized with Context Injection Anchors for Local LLMs (Llama 3.1 / RTX 4070).
"""

# --- 1. ATOMICITY & REORDER ---

USER_PROMPT_ATOMICITY = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: XML Structuring
Analyze the [CONTEXT_DATA] provided above and transform the segments into a nested <atomic_structure> XML block.

Rules:
1. Return ONLY the <atomic_structure> XML block.
2. Copy text exactly; NO summaries, NO omissions.
3. Use descriptive snake_case IDs.
4. Output ONLY the XML. NO prose, NO markdown fences.
"""

USER_PROMPT_REORDER = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Semantic Reordering
Analyze the [CONTEXT_DATA] and reorder the XML segments into a single unified <atomic_structure> block.
- Copy text exactly.
- Ensure semantic hierarchy and logical flow.
- Return ONLY well-formed XML without markdown fences.
"""

# --- 2. METADATA & STRATEGY ---

USER_PROMPT_TAGS = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Strategic Metadata Generation
Analyze the [CONTEXT_DATA] and fill the YAML template below.
- summary: Write a technical summary of the SUBJECT MATTER. (DO NOT talk about the XML or the analysis process).
- category/moc/moc_stage/moc_verb: Use "[[Value]]" format.

---
category: "[[Broad Domain]]"
moc: "[[Specific Component]]"
moc_stage: "[[Stage]]"
moc_verb: "[[Verb]]"
tags: ["topic-one", "topic-two"]
audience: ["Role1", "Role2"]
importance: 0
urgency: 0
complexity: 0
trade_off: "Benefit vs Cost"
summary: "2-sentence summary of the problem solved."
so_what: "2-5 sentence about the strategic impact"
---

START IMMEDIATELY with `---`.
"""

# --- 3. VISUALS & MATRIX ---

USER_PROMPT_MATRIX = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: High-Utility Recall Matrix
Analyze [CONTEXT_DATA] and create a matrix that serves as a study guide and executive summary.

1. **Strategic Justification**: For every entry, answer: "Why is this critical for a Senior Engineer?".
   - If the XML says "Ensure Responsible AI", you must explain its utility: "[Ethics/Risk] Prevention of model hallucinations and regulatory non-compliance."
2. **Technical Translation**: Convert snake_case or IDs into readable [[WikiLinks]].
3. **Density**: Keep the utility answer between 6-10 words. Focus on the *business or technical risk* mitigated.

START IMMEDIATELY with the table header.
"""

USER_PROMPT_DIAGRAM = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Valid Mermaid Mapping
1. Create 3 subgraphs: Governance, Deployment, Security_Monitoring.
2. Inside each, create 2-3 nodes using the format: ID[Title Case Text].
3. Connect nodes across subgraphs using simple `-->` arrows.
4. 🛑 STRICT: No slashes, no arrow labels, no parentheses.

START IMMEDIATELY with ```mermaid.
"""

# --- 4. LEARNING & CASE STUDIES ---

USER_PROMPT_FLASHCARDS = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Explanatory Fast-Learning Flashcards
Extract 8-10 flashcards from the data above.

1. **Front Side (The Entity)**: Create a concise title for the concept (e.g., [[Data Validation]], [[Network Security]]).
2. **Back Side (The Action)**: Explain the HOW/WHAT using a strong verb (e.g., "Implementing...", "Enforcing...", "Automating...").
3. **Requirement**: If a section has no clear title, derive one from the technical context. NEVER leave the space before '::' empty.

START IMMEDIATELY with [[.
"""

USER_PROMPT_CASE_STUDY = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Narrative Strategic Case Study
Analyze [CONTEXT_DATA] and generate a high-density case study applying Atomic Subjectivity.

### Mandatory Structure:
case_of_use:: [Technical SRE problem statement using Noun-Dominance]
correct_solution:: [Architectural Why + Trade-offs. Integrate XML components and SRE enrichment into a single dense paragraph]
incorrect_solution:: [Anti-pattern description + Failure outcome]

Workflow Steps:
steps_name:: [Concise technical title of the step]
steps_develop:: [Noun-heavy narrative integrating action and reasoning]

steps_name:: [Concise technical title of the step]
steps_develop:: [Noun-heavy narrative integrating action and reasoning]

steps_name:: [Concise technical title of the step]
steps_develop:: [Noun-heavy narrative integrating action and reasoning]

(Repeat steps as needed: 3 or more steps are allowed)

### Constraints:
- START IMMEDIATELY with `case_of_use::`.
- NO notes, NO fences, NO formatting garbage.
- Each step MUST follow the exact two-key format: `steps_name::` then `steps_develop::`.
"""


USER_PROMPT_NAMING = """
### [CONTEXT_DATA_START]
{xml_content}
### [CONTEXT_DATA_END]

### Task: Generate Strategic Filename
Analyze the context in [CONTEXT_DATA] and output ONE Snake_Case_Strategic filename.

⚠️ START IMMEDIATELY with the filename.
⚠️ DO NOT include introductory text.
⚠️ DO NOT include conclusions.
⚠️ DO NOT provide options.
⚠️ DO NOT output metadata or reasoning.
⚠️ DO NOT output system fields (model=, created_at=, done=).
"""


USER_PROMPT_CONTENT = """
### [SOURCE_DATA]
{xml_content}
### [END_SOURCE]

### Task: Exhaustive Architectural Synthesis
Analyze [SOURCE_DATA] and reorganize it into a comprehensive professional document.

1. **Autonomous Pillar Creation**: Group the data into 3-4 dominant technical themes (e.g., Infrastructure Resiliency, Data Governance, Operational Excellence) and establish them as ## headers.
2. **Exhaustive Expansion**: For every distinct technical point in the source, write 2-3 sentences of high-density prose. Do NOT group multiple requirements into a single vague sentence.
3. **Pillar Integrity**: Within each ## Pillar, use ### and #### to categorize specific tools and protocols.
4. **Action-to-Standard Translation**: Convert all instructions (e.g., "Test performance") into "Standards" (e.g., "Performance testing and evaluation standards").

### Strict Constraints:
- Start directly with the first ## header.
- Use only H2, H3, and H4.
- NO introductions, NO "Knowledge Retention" sections, NO meta-comments, and NO footers.
- The document must end immediately after the final technical paragraph.
"""
