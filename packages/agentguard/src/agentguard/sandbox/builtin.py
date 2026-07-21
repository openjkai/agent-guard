"""Built-in enterprise mock tools."""

from __future__ import annotations

from typing import Any

from agentguard.sandbox.tool import FailureMode, MockTool, ToolBox, ToolPolicy


def _refund_handler(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    return {
        "refund_id": f"RF-{args.get('order_id', 'unknown')}",
        "amount": args.get("amount"),
        "status": "processed",
        "customer_id": args.get("customer_id", context.get("customer_id")),
    }


def _crm_handler(args: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": args.get("record_id"),
        "updated": True,
        "fields": args.get("fields", {}),
    }


def _approve_handler(args: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return {"request_id": args.get("request_id"), "approved": True}


def _email_handler(args: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return {"message_id": "msg-001", "to": args.get("to"), "sent": True}


def _schedule_handler(args: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return {"appointment_id": "appt-001", "slot": args.get("slot"), "confirmed": True}


def _account_handler(args: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_id": args.get("account_id"),
        "changes": args.get("changes", {}),
        "updated": True,
    }


def _query_handler(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    table = args.get("table", "customers")
    db = context.get("database", {})
    rows = db.get(table, [])
    return {"table": table, "rows": rows, "count": len(rows)}


def build_default_toolbox(context: dict[str, Any] | None = None) -> ToolBox:
    toolbox = ToolBox(context=context or {})
    tools = [
        MockTool(
            name="issue_refund",
            description="Issue a customer refund",
            input_schema={
                "type": "object",
                "required": ["customer_id", "order_id", "amount"],
                "properties": {
                    "customer_id": {"type": "string"},
                    "order_id": {"type": "string"},
                    "amount": {"type": "number", "minimum": 0},
                    "reason": {"type": "string"},
                },
            },
            handler=_refund_handler,
            policy=ToolPolicy(max_amount=500.0),
        ),
        MockTool(
            name="update_crm_record",
            description="Update a CRM record",
            input_schema={
                "type": "object",
                "required": ["record_id", "fields"],
                "properties": {
                    "record_id": {"type": "string"},
                    "fields": {"type": "object"},
                },
            },
            handler=_crm_handler,
        ),
        MockTool(
            name="approve_request",
            description="Approve a pending request",
            input_schema={
                "type": "object",
                "required": ["request_id"],
                "properties": {
                    "request_id": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
            handler=_approve_handler,
        ),
        MockTool(
            name="send_email",
            description="Send an email to a customer",
            input_schema={
                "type": "object",
                "required": ["to", "subject", "body"],
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            handler=_email_handler,
        ),
        MockTool(
            name="schedule_appointment",
            description="Schedule a customer appointment",
            input_schema={
                "type": "object",
                "required": ["customer_id", "slot"],
                "properties": {
                    "customer_id": {"type": "string"},
                    "slot": {"type": "string"},
                },
            },
            handler=_schedule_handler,
        ),
        MockTool(
            name="modify_account",
            description="Modify a customer account",
            input_schema={
                "type": "object",
                "required": ["account_id", "changes"],
                "properties": {
                    "account_id": {"type": "string"},
                    "changes": {"type": "object"},
                },
            },
            handler=_account_handler,
        ),
        MockTool(
            name="query_database",
            description="Query a mock database table",
            input_schema={
                "type": "object",
                "required": ["table"],
                "properties": {
                    "table": {"type": "string"},
                    "filters": {"type": "object"},
                },
            },
            handler=_query_handler,
        ),
    ]
    for tool in tools:
        toolbox.register(tool)
    return toolbox


__all__ = ["FailureMode", "MockTool", "ToolBox", "ToolPolicy", "build_default_toolbox"]
