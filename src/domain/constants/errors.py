from typing import Final

# === Error Codes (Common) ===
ERR_CODE_NOT_IMPLEMENTED: Final = "NOT_IMPLEMENTED"
ERR_CODE_INTERNAL: Final = "INTERNAL_SERVER_ERROR"
ERR_CODE_VALIDATION: Final = "VALIDATION_ERROR"
ERR_CODE_UNAUTHORIZED: Final = "UNAUTHORIZED"
ERR_CODE_FORBIDDEN: Final = "FORBIDDEN"
ERR_CODE_NOT_FOUND: Final = "NOT_FOUND"
ERR_CODE_CONFLICT: Final = "CONFLICT"
ERR_CODE_RATE_LIMIT: Final = "RATE_LIMIT_EXCEEDED"


# === Error Messages (Common) ===
MSG_NOT_IMPLEMENTED: Final = "This feature is not yet available."
MSG_INTERNAL_ERROR: Final = "An unexpected server error occurred."
MSG_VALIDATION_ERROR: Final = "The provided fields are invalid or incomplete."
MSG_UNAUTHORIZED: Final = "Invalid credentials or session expired."
MSG_FORBIDDEN: Final = "You do not have sufficient permissions to perform this action."
MSG_NOT_FOUND: Final = "The requested resource does not exist."
MSG_CONFLICT: Final = "The resource already exists or there is a data conflict."
MSG_RATE_LIMIT: Final = "Too many requests. Please try again later."
MSG_IMAGE_ERROR: Final = "Unprocessable image. Please check file, size, and extension"


# --- Infrastructure & Technical Error Codes ---
ERR_CODE_DATABASE: Final = "DATABASE_ERROR"
ERR_CODE_PERSISTENCE: Final = "PERSISTENCE_ERROR"
ERR_CODE_LLM_CONNECTION: Final = "LLM_CONNECTION_LOST"
ERR_CODE_FILE_SYSTEM: Final = "FILE_DONT_EXIT"

# --- Infrastructure & Technical Messages ---
MSG_DATABASE_ERROR: Final = "Error accessing data records."
MSG_PERSISTENCE_ERROR: Final = "Database transaction failed during persistence."
MSG_LLM_CONNECTION: Final = "The AI service is currently unreachable."
MSG_FILE_SYSTEM: Final = "An error occurred while accessing the file system."
MSG_SECURITY_PATH_TRAVERSAL: Final = "File path unreachable"
# === Common Responses (Swagger / OpenAPI) ===
COMMON_RESPONSES: Final = {
    400: {"description": ERR_CODE_NOT_IMPLEMENTED},
    401: {"description": MSG_UNAUTHORIZED},
    403: {"description": MSG_FORBIDDEN},
    404: {"description": MSG_NOT_FOUND},
    409: {"description": MSG_CONFLICT},
    422: {"description": MSG_VALIDATION_ERROR},
    429: {"description": MSG_RATE_LIMIT},
    500: {"description": MSG_INTERNAL_ERROR},
}
