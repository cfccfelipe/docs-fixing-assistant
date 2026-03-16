import logging

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, embedder):
        """
        Initialize the EvaluationService.

        Parameters
        ----------
        embedder : object
            An embedding provider that exposes a method `.embed(text: str) -> List[float]`.
            This can be your LLM provider if it supports embeddings, or a wrapper around
            HuggingFace/OpenAI embedding models.
        """
        self.embedder = embedder

    def similarity_score(self, text_a: str, text_b: str) -> float:
        """
        Compute cosine similarity between two text inputs.
        """
        vec_a = self.embedder.embed(text_a)
        vec_b = self.embedder.embed(text_b)

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        return dot / (norm_a * norm_b)

    def evaluate_candidates(self, candidates: list[str], golden: str) -> dict:
        """
        Evaluate multiple candidate outputs against a golden reference and
        return metrics for each candidate plus the best one.

        Returns
        -------
        dict
            {
              "best_output": str,
              "best_score": float,
              "metrics": [
                  {"candidate": str, "score": float}
              ]
            }
        """
        best_output = ""
        best_score = -1.0
        metrics = []

        for i, candidate in enumerate(candidates):
            score = self.similarity_score(candidate, golden)
            metrics.append({"candidate": candidate, "score": score})
            logger.info(f"Candidate {i + 1}: similarity={score:.3f}")
            if score > best_score:
                best_score = score
                best_output = candidate

        return {
            "best_output": best_output,
            "best_score": best_score,
            "metrics": metrics,
        }
