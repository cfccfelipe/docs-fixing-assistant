# domain/orchestrator/constants/messages.py

# A meaningful fallback when the agent hits the iteration limit
MSG_CIRCUIT_BREAKER_USER_FEEDBACK = (
    "I've attempted to address your request: '{user_prompt}' through {max_iters} passes, "
    "but I couldn't reach a fully verified conclusion. I have preserved the partial "
    "progress in the workspace for your review."
)

MSG_MAX_ITERATIONS_LOG = (
    "Circuit Breaker tripped at [{node_name}]: Max iterations reached."
)

# Orchestrator messages
MSG_MAX_ITERATIONS = "Workflow halted: Maximum attempts reached without convergence."
MSG_WORKFLOW_FINALIZED = "Workflow finalized: Goal achieved and XML validated."
MSG_CHUNK_REQUIRED = "🚀 Mode: Chunking Required. Dispatching XML Chunker."
MSG_STANDARD_ROUTING = "Standard Routing: {agents}"
MSG_FALLBACK_ROUTING = "Fallback: Mandatory core agents triggered."
