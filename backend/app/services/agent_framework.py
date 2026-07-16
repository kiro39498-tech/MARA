"""Backward-compatibility shim for agent_framework service module.

The MaterialPlanningOrchestrator has moved to:
    app.agents.orchestrator.MaterialPlanningOrchestrator

This shim re-exports it under the original module path so that existing
imports in planning_api.py and any other callers continue to work
without modification.

    Old import (still works):
        from app.services.agent_framework import MaterialPlanningOrchestrator

    New canonical import:
        from app.agents.orchestrator import MaterialPlanningOrchestrator
"""

from app.agents.orchestrator import MaterialPlanningOrchestrator  # noqa: F401

__all__ = ["MaterialPlanningOrchestrator"]
