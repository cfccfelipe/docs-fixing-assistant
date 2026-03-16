import json
import logging
import re
from pathlib import Path

from domain.constants import golden_answers, system_prompts, users_prompts
from domain.services.evaluation_service import EvaluationService
from infrastructure.adapters.config.ollama import OllamaConfig
from infrastructure.adapters.llm_provider.ollama_adapter import OllamaAdapter
from infrastructure.adapters.llm_provider.ollama_embedder_adapter import (
    OllamaEmbedderAdapter,
)
from infrastructure.adapters.storage.atomic_storage import AtomicSourceStorageTool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_single_variant(
    llm_adapter, base_system_prompt: str, base_user_prompt: str, iteration: int
):
    """Genera UNA variante de system y user prompt en formato texto con etiquetas claras."""
    messages = [
        {"role": "system", "content": "You are a prompt engineering assistant."},
        {
            "role": "user",
            "content": (
                f"Iteration {iteration}: Generate exactly 1 alternative system prompt and 1 alternative user prompt "
                f"that could improve the following:\n\nSystem prompt:\n{base_system_prompt}\n\n"
                f"User prompt:\n{base_user_prompt}\n\n"
                f"Output ONLY in this format:\n\n"
                f"SYSTEM_PROMPT:\n<your system prompt here>\n\n"
                f"USER_PROMPT:\n<your user prompt here>\n\n"
                f"Do not include explanations, markdown, or any other text."
            ),
        },
    ]
    response = llm_adapter.generate(messages=messages)
    return response.get("content", "")


def extract_prompts_from_raw(text: str, base_system: str, base_user: str):
    """Extrae los prompts alternativos desde el texto crudo devuelto por el modelo."""
    system_prompt = base_system
    user_prompt = base_user

    sys_match = re.search(
        r"SYSTEM_PROMPT:\s*(.*?)(?:USER_PROMPT:|$)", text, re.S | re.I
    )
    if sys_match:
        system_prompt = sys_match.group(1).strip()

    user_match = re.search(r"USER_PROMPT:\s*(.*)", text, re.S | re.I)
    if user_match:
        user_prompt = user_match.group(1).strip()

    return {"system": system_prompt, "user": user_prompt}


def main():
    # 1. Adapter para generación de texto con temperatura alta para diversidad
    llm_config = OllamaConfig(model_name="llama3.1:latest", temperature=0.9)
    llm_adapter = OllamaAdapter(config=llm_config)

    # 2. Adapter para embeddings con nomic-embed-text
    embed_config = OllamaConfig(model_name="nomic-embed-text:latest")
    embed_adapter = OllamaEmbedderAdapter(config=embed_config)

    evaluator = EvaluationService(embedder=embed_adapter)

    # 3. Leer archivo Markdown
    base_dir = Path(__file__).parent
    file_path = base_dir / "requirements" / "0. Initial requirements.md"
    raw_content = file_path.read_text(encoding="utf-8")

    # 4. Limpiar y persistir con AtomicSourceStorageTool
    storage_tool = AtomicSourceStorageTool()
    xml_path = storage_tool.execute(
        raw_content=raw_content,
        file_name="initial_requirements",
        storage_path="./cleaned_sources",
    )
    cleaned_content = Path(xml_path).read_text(encoding="utf-8")

    # 5. Base prompts (usando contenido limpio)
    base_system_prompt = system_prompts.SYSTEM_PROMPT_ATOMICITY
    base_user_prompt = users_prompts.USER_PROMPT_ATOMICITY.format(
        content=cleaned_content
    )

    # 6. Iterar 5 veces generando variantes y resultados
    candidates = []
    detailed_results = []
    for i in range(1, 6):
        logger.info(f"Generando variante {i}...")
        variant_raw = generate_single_variant(
            llm_adapter, base_system_prompt, base_user_prompt, i
        )

        # Guardar la respuesta cruda para depuración
        raw_path = Path(__file__).parent / f"variant_raw_{i}.txt"
        raw_path.write_text(variant_raw, encoding="utf-8")

        # Extraer prompts desde el texto crudo
        variant = extract_prompts_from_raw(
            variant_raw, base_system_prompt, base_user_prompt
        )

        messages = [
            {"role": "system", "content": variant["system"]},
            {"role": "user", "content": variant["user"]},
        ]
        response = llm_adapter.generate(messages=messages)
        candidate_output = response.get("content", "")
        candidates.append(candidate_output)

        iteration_result = {
            "iteration": i,
            "system_prompt": variant["system"],
            "user_prompt": variant["user"],
            "candidate_output": candidate_output,
            "raw_variant": variant_raw,
        }
        detailed_results.append(iteration_result)

        iter_path = Path(__file__).parent / f"evaluation_result_{i}.json"
        with open(iter_path, "w", encoding="utf-8") as f:
            json.dump(iteration_result, f, indent=2, ensure_ascii=False)
        logger.info(f"Iteración {i} guardada en {iter_path}")

    # 7. Evaluar contra golden answer usando los candidatos generados
    results = evaluator.evaluate_candidates(candidates, golden_answers.ATOMICITY_GOLDEN)

    print("=== Evaluation Results ===")
    print("Best score:", results["best_score"])
    print("Best output:\n", results["best_output"])
    print("\nAll metrics:")
    for idx, m in enumerate(results["metrics"], start=1):
        print(f"Candidate {idx} | Score={m['score']:.3f}")
        print(m["candidate"][:200], "...\n")

    # 8. Guardar resultados globales
    output_path = Path(__file__).parent / "evaluation_results.json"
    full_output = {
        "summary": results,
        "iterations": detailed_results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    logger.info(f"Resultados completos guardados en {output_path}")


if __name__ == "__main__":
    main()
