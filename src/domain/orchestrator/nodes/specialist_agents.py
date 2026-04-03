import logging
import os
import re
from pathlib import Path
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.models.llm_provider_model import LLMRequest
from domain.models.message_model import MessageDefinition
from domain.models.enums import MessageRole
import uuid

logger = logging.getLogger(__name__)

def _update_plan_filename(tool_registry, old_name: str, new_name: str):
    """Updates all future tasks in PLAN.md with the new filename."""
    if not tool_registry:
        return
    try:
        content = tool_registry.execute("read_file", path="PLAN.md")
        new_content = content.replace(f" {old_name} ->", f" {new_name} ->")
        if new_content != content:
            tool_registry.execute("write_file", path="PLAN.md", content=new_content)
            logger.info(f"📝 PERSISTENCE: Updated PLAN.md for future tasks: {old_name} -> {new_name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to update PLAN.md: {e}")

class ClassifierAgent(BaseWorkerNode):
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"📂 ClassifierAgent: Analyzing {state.current_file}")
        
        try:
            content = self.tool_registry.execute("read_file", path=state.current_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not read file {state.current_file}: {e}")
            return StateUpdate(task_result=f"Error: {e}", next_agent="supervisor")
        
        prompt = (
            "Determine the technical domain for this content. Use ONE word from: [architecture, operations, research, guides, development].\n"
            f"Content: {content[:1000]}\n"
            "Respond with ONLY the word."
        )
        
        request = LLMRequest(messages=[MessageDefinition(id=uuid.uuid4(), role=MessageRole.USER, content_history=prompt)])
        response = await self._execute_inference(request)
        category = re.sub(r'[^a-z]', '', response.content.strip().lower()) or "other"
        
        # New relative path
        new_rel_path = f"fixed_files/{category}/{Path(state.current_file).name}"
        
        self.tool_registry.execute("write_file", path=new_rel_path, content=content)
        self.tool_registry.execute("delete_file", path=state.current_file)
        
        _update_plan_filename(self.tool_registry, state.current_file, new_rel_path)
        return StateUpdate(task_result=f"Classified as {category}", next_agent="supervisor")

class NamingAgent(BaseWorkerNode):
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"🏷️ NamingAgent: Renaming {state.current_file}")
        
        try:
            content = self.tool_registry.execute("read_file", path=state.current_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not read file {state.current_file}: {e}")
            return StateUpdate(task_result=f"Error: {e}", next_agent="supervisor")
        
        prompt = (
            "Propose a clean, lowercase snake_case filename (no spaces) for this content.\n"
            f"Content: {content[:1000]}\n"
            "Respond with ONLY the filename (with .md)."
        )
        
        request = LLMRequest(messages=[MessageDefinition(id=uuid.uuid4(), role=MessageRole.USER, content_history=prompt)])
        response = await self._execute_inference(request)
        
        new_name = response.content.strip()
        new_name = re.sub(r'^.*[:\n]', '', new_name)
        new_name = re.sub(r'[^a-z0-9_\-\.]', '', new_name.lower())
        if not new_name.endswith(".md"):
            new_name += ".md"
        
        new_rel_path = f"fixed_files/{new_name}"
        
        if new_rel_path != state.current_file:
            self.tool_registry.execute("write_file", path=new_rel_path, content=content)
            self.tool_registry.execute("delete_file", path=state.current_file)
            _update_plan_filename(self.tool_registry, state.current_file, new_rel_path)
            
        return StateUpdate(task_result=f"Renamed to {new_name}", next_agent="supervisor")

class AtomicityAgent(BaseWorkerNode):
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"⚛️ AtomicityAgent: XMLizing {state.current_file}")
        try:
            content = self.tool_registry.execute("read_file", path=state.current_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not read file {state.current_file}: {e}")
            return StateUpdate(task_result=f"Error: {e}", next_agent="supervisor")
            
        xml_filename = Path(state.current_file).with_suffix(".xml").name
        xml_rel_path = f"fixed_files/xml/{xml_filename}"
        
        xml_content = f"<atomic_document>\n  <source>{state.current_file}</source>\n  <content>{content}</content>\n</atomic_document>"
        self.tool_registry.execute("write_file", path=xml_rel_path, content=xml_content)
        
        return StateUpdate(task_result="XML Generated", next_agent="supervisor")

class SummarizerAgent(BaseWorkerNode):
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"📝 SummarizerAgent: Summarizing {state.current_file}")
        try:
            content = self.tool_registry.execute("read_file", path=state.current_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not read file {state.current_file}: {e}")
            return StateUpdate(task_result=f"Error: {e}", next_agent="supervisor")
        
        prompt = f"Summarize this documentation in 3 punchy bullet points:\n{content[:2000]}"
        request = LLMRequest(messages=[MessageDefinition(id=uuid.uuid4(), role=MessageRole.USER, content_history=prompt)])
        response = await self._execute_inference(request)
        
        sum_filename = Path(state.current_file).with_suffix(".txt").name
        sum_rel_path = f"fixed_files/summaries/{sum_filename}"
        
        self.tool_registry.execute("write_file", path=sum_rel_path, content=response.content.strip())
        return StateUpdate(task_result="Summary Generated", next_agent="supervisor")

class TagAgent(BaseWorkerNode):
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"🔖 TagAgent: Tagging {state.current_file}")
        try:
            content = self.tool_registry.execute("read_file", path=state.current_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not read file {state.current_file}: {e}")
            return StateUpdate(task_result=f"Error: {e}", next_agent="supervisor")
        
        prompt = f"Extract 3-5 keywords for this content as a comma-separated list:\n{content[:1000]}"
        request = LLMRequest(messages=[MessageDefinition(id=uuid.uuid4(), role=MessageRole.USER, content_history=prompt)])
        response = await self._execute_inference(request)
        tags = response.content.strip().replace("{", "").replace("}", "")
        
        tagged_content = f"---\ntags: [{tags}]\n---\n{content}"
        self.tool_registry.execute("write_file", path=state.current_file, content=tagged_content)
        
        return StateUpdate(task_result="Metadata Injected", next_agent="supervisor")
