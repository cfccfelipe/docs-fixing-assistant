# Phase 4: Final Cleanup (Dead Code Removal)

## Objective
Sanitize the codebase by surgically removing legacy service layers and unused components once the new orchestrator is fully functional.

## Subtasks
- [ ] Decommission and delete `src/domain/services/fixing_service.py`.
- [ ] Decommission and delete `src/domain/services/reordering_service.py`.
- [ ] Decommission and delete `src/domain/services/strategic_service.py`.
- [ ] Remove old endpoints in `src/api/routes/` that relied on these services (e.g., `fixing.py`, `reordering.py`, `strategic.py`, `pipeline.py`).
- [ ] Consolidate any duplicate models or DTOs in `src/domain/models`.
- [ ] Clean up `src/api/dependencies.py` to remove legacy service instantiations.
- [ ] Run the full integration suite to ensure the new orchestrator-led flow is stable, complete, and the application starts correctly without the legacy code.