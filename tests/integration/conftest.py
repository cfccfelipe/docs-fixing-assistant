# # tests/integration/conftest.py


# import pytest

# from domain.orchestrator.nodes.supervisor_node import SupervisorNode
# from infrastructure.adapters.config.ollama import OllamaConfig
# from infrastructure.adapters.llm_provider.ollama_adapter import OllamaAdapter


# @pytest.fixture(scope="session")
# def real_llm_config():
#     return OllamaConfig()


# @pytest.fixture(scope="session")
# def real_llm_adapter(real_llm_config):
#     return OllamaAdapter(config=real_llm_config)


# @pytest.fixture(scope="session")
# def real_supervisor(real_llm_adapter):
#     """SupervisorNode con el adapter real (ej. OllamaAdapter)."""
#     return SupervisorNode(llm_provider=real_llm_adapter)


# # @pytest.fixture(scope="session")
# # def real_fs():
# #     # Adaptador local de FS apuntando a la carpeta examples
# #     examples_dir = Path(__file__).parent / "examples"
# #     return LocalFileSystemAdapter(base_dir=str(examples_dir))


# # @pytest.fixture(scope="session")
# # def real_builder(real_llm_adapter, real_fs):
# #     graph = LangGraphBuilder(fs=real_fs)
# #     return graph.build_fixing_graph(real_llm_adapter)
