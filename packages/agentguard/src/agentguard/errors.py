"""AgentGuard domain exceptions."""


class AgentGuardError(Exception):
    """Base exception for AgentGuard."""


class ScenarioLoadError(AgentGuardError):
    """Failed to load or validate a scenario."""


class EvaluatorNotFoundError(AgentGuardError):
    """Referenced evaluator is not registered."""


class CassetteNotFoundError(AgentGuardError):
    """No cassette recording exists for replay."""


class CassetteMatchError(AgentGuardError):
    """Could not match a request to a recorded interaction."""


class ToolValidationError(AgentGuardError):
    """Tool arguments failed JSON schema validation."""


class ToolPolicyViolation(AgentGuardError):
    """Tool call violated sandbox safety policy."""


class RunNotFoundError(AgentGuardError):
    """Run artifact not found in storage."""
