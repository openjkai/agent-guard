"""Mock tool sandbox for safe agent testing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import jsonschema
from jsonschema import ValidationError

from agentguard.errors import ToolPolicyViolation, ToolValidationError
from agentguard.tracing.context import RunContext


class FailureMode(str, Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    ERROR = "error"
    SLOW = "slow"
    MALFORMED = "malformed"


@dataclass
class ToolPolicy:
    max_amount: float | None = None
    allowed_fields: set[str] | None = None

    def validate(self, arguments: dict[str, Any]) -> str | None:
        if self.allowed_fields is not None:
            unknown = set(arguments) - self.allowed_fields
            if unknown:
                return f"Disallowed fields: {sorted(unknown)}"
        if self.max_amount is not None and "amount" in arguments:
            amount = arguments["amount"]
            if isinstance(amount, (int, float)) and amount > self.max_amount:
                return f"Amount {amount} exceeds limit {self.max_amount}"
        return None


@dataclass
class MockTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], dict[str, Any]], Any]
    failure_mode: FailureMode = FailureMode.NONE
    slow_delay_ms: float = 500.0
    policy: ToolPolicy | None = None

    def validate_args(self, arguments: dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=arguments, schema=self.input_schema)
        except ValidationError as exc:
            raise ToolValidationError(str(exc.message)) from exc

    def invoke(self, arguments: dict[str, Any], context: dict[str, Any]) -> Any:
        self.validate_args(arguments)
        if self.policy:
            violation = self.policy.validate(arguments)
            if violation:
                raise ToolPolicyViolation(violation)

        if self.failure_mode == FailureMode.TIMEOUT:
            raise TimeoutError(f"Tool {self.name} timed out")
        if self.failure_mode == FailureMode.ERROR:
            raise RuntimeError(f"Tool {self.name} failed")
        if self.failure_mode == FailureMode.SLOW:
            time.sleep(self.slow_delay_ms / 1000.0)
        if self.failure_mode == FailureMode.MALFORMED:
            return {"status": "ok", "unexpected": object()}

        return self.handler(arguments, context)


@dataclass
class ToolAttempt:
    tool_name: str
    arguments: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    policy_violation: str | None = None


@dataclass
class ToolBox:
    """Registry of mock tools available to an agent."""

    tools: dict[str, MockTool] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    attempts: list[ToolAttempt] = field(default_factory=list)
    record_only: set[str] = field(default_factory=set)

    def register(self, tool: MockTool) -> None:
        self.tools[tool.name] = tool

    def set_failure_mode(self, tool_name: str, mode: FailureMode) -> None:
        if tool_name in self.tools:
            self.tools[tool_name].failure_mode = mode

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")

        tool = self.tools[name]
        attempt = ToolAttempt(tool_name=name, arguments=arguments)
        self.attempts.append(attempt)

        if name in self.record_only:
            attempt.result = {"recorded": True, "executed": False}
            return attempt.result

        try:
            result = tool.invoke(arguments, self.context)
            attempt.result = result
            return result
        except ToolPolicyViolation as exc:
            attempt.policy_violation = str(exc)
            raise
        except Exception as exc:
            attempt.error = str(exc)
            raise

    def execute_with_trace(
        self, trace: RunContext, name: str, arguments: dict[str, Any]
    ) -> Any:
        try:
            result = self.call(name, arguments)
            trace.record_tool(tool_name=name, arguments=arguments, result=result)
            return result
        except ToolPolicyViolation as exc:
            trace.record_tool(
                tool_name=name,
                arguments=arguments,
                result=None,
                error=str(exc),
                policy_violation=str(exc),
            )
            raise
        except Exception as exc:
            trace.record_tool(
                tool_name=name,
                arguments=arguments,
                result=None,
                error=str(exc),
            )
            raise

    def schema_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]
