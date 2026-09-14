"""Compatibility entry point for the local-first mission service."""

from .mission_lifecycle import (
    Decision,
    MissionAnalysis,
    MissionDecision,
    MissionLifecycleService,
    MissionResult,
    MissionState,
)

MissionService = MissionLifecycleService

__all__ = [
    "Decision",
    "MissionAnalysis",
    "MissionDecision",
    "MissionLifecycleService",
    "MissionResult",
    "MissionService",
    "MissionState",
]
