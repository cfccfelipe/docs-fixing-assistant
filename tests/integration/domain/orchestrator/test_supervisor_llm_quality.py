from domain.models.state import AgentState


async def test_supervisor_end_to_end(real_supervisor, real_fs):
    """
    End-to-End Scenario:
    1. Supervisor detects multiple files in examples/Projection and Execution folders.
    2. Routes to atomicity/validation agent (parser + fs).
    3. Applies refactoring with logic_flow and naming_agent if needed.
    4. Consolidates sources with struct_xml, meta_props, prose_writer.
    5. Final review with logic_flow on consolidated Markdown.
    6. Generates recall_table, study_cards, mermaid_map, workflow_sme.
    7. Iterates until satisfactory results.
    """

    - Planning: planner_agent (already executed by orchestrator)
- Atomicity/Validation: atomicity_agent, validation_agent, tag_agent
- Refactor: logic_flow, naming_agent
- Consolidation: struct_xml, meta_props, prose_writer, content_agent
- Final Review: logic_flow
- Artefacts: recall_table, study_cards, mermaid_map, workflow_sm

    # Arrange: capture all Markdown files in examples folder using FS adapter
    md_files = real_fs.list_files(str(real_fs.base_dir), extension="md")
    assert md_files, "No Markdown files found in examples folder"

    # Act: pass folder path to supervisor
    state = AgentState(
        user_feedback="Analyze and consolidate all example files",
        path=str(real_fs.base_dir),
    )
    response = await real_supervisor(state)

    # Assert: initial agents must include atomicity/validation
    assert any(
        "atomicity_agent" in a or "validation_agent" in a
        for a in response.active_agents
    )

    # Assert: consolidation agents must appear
    assert "struct_xml" in response.active_agents
    assert "meta_props" in response.active_agents
    assert "prose_writer" in response.active_agents

    # Assert: final enrichment agents must appear
    enrichment_agents = {"recall_table", "study_cards", "mermaid_map", "workflow_sme"}
    assert enrichment_agents.intersection(set(response.active_agents))

    # Assert: results contain at least one consolidated Markdown and XML output
    md_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".md")
    ]
    xml_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".xml")
    ]
    assert md_outputs, "No consolidated Markdown output found"
    assert xml_outputs, "No consolidated XML output found"

    # Assert: supervisor iterated until satisfactory
    assert any(
        "satisfactory" in r.lower() or "finalized" in r.lower()
        for r in response.results
    )


async def test_supervisor_projection_only(real_supervisor, real_fs):
    """
    End-to-End Scenario focused on Projection folder only.
    Validates that supervisor can work on subfolders.
    """

    projection_path = str(real_fs.base_dir / "Projection")
    md_files = real_fs.list_files(projection_path, extension="md")
    assert md_files, "No Markdown files found in Projection folder"

    state = AgentState(
        user_feedback="Analyze and consolidate Projection files", path=projection_path
    )
    response = await real_supervisor(state)

    # Assert: consolidation agents must appear
    assert "struct_xml" in response.active_agents
    assert "prose_writer" in response.active_agents

    # Assert: results contain consolidated Markdown
    md_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".md")
    ]
    assert md_outputs, "No consolidated Markdown output found for Projection"


def test_graph_structure(real_builder):
    node_ids = list(real_builder.nodes.keys())

    # Nodos que realmente existen en el grafo
    expected_nodes = [
        "atomicity_agent",
        "reordering_agent",
        "tag_agent",
        "naming_agent",
        "struct_xml",
        "meta_props",
        "prose_writer",
        "recall_table",
        "study_cards",
        "mermaid_map",
        "workflow_sme",
    ]

    for node in expected_nodes:
        assert node in node_ids, f"Nodo {node} no encontrado en el grafo"

    # Verifica que el entry_point sea atomicity_agent
    assert real_builder.entry_point == "atomicity_agent"


async def test_supervisor_end_to_end(real_supervisor, real_fs):
    """
    Escenario end-to-end con todo el grafo ejecutándose sobre Projection y Execution.
    """

    md_files = real_fs.list_files(str(real_fs.base_dir), extension="md")
    assert md_files, "No Markdown files found in examples folder"

    state = AgentState(
        user_feedback="Analyze and consolidate all example files",
        path=str(real_fs.base_dir),
    )
    response = await real_supervisor(state)

    # Validaciones de agentes
    assert "atomicity_agent" in response.active_agents
    assert "struct_xml" in response.active_agents
    assert "prose_writer" in response.active_agents

    enrichment_agents = {"recall_table", "study_cards", "mermaid_map", "workflow_sme"}
    assert enrichment_agents.intersection(set(response.active_agents))

    # Validaciones de outputs
    md_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".md")
    ]
    xml_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".xml")
    ]
    assert md_outputs, "No consolidated Markdown output found"
    assert xml_outputs, "No consolidated XML output found"


async def test_supervisor_projection_only(real_supervisor, real_fs):
    """
    Escenario end-to-end enfocado solo en la carpeta Projection.
    """

    projection_path = str(real_fs.base_dir / "Projection")
    md_files = real_fs.list_files(projection_path, extension="md")
    assert md_files, "No Markdown files found in Projection folder"

    state = AgentState(
        user_feedback="Analyze and consolidate Projection files",
        path=projection_path,
    )
    response = await real_supervisor(state)

    assert "struct_xml" in response.active_agents
    assert "prose_writer" in response.active_agents

    md_outputs = [
        r for r in response.results if isinstance(r, str) and r.endswith(".md")
    ]
    assert md_outputs, "No consolidated Markdown output found for Projection"
