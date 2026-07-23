"""Initial schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agent_module_path", sa.String(length=1024), nullable=False),
        sa.Column("scenarios_path", sa.String(length=1024), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "suite_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("pass_rate", sa.Float(), nullable=True),
        sa.Column("release_decision", sa.String(length=64), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("gate_report_json", sa.JSON(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("progress_completed", sa.Integer(), nullable=False),
        sa.Column("progress_total", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suite_runs_project_id", "suite_runs", ["project_id"])
    op.create_table(
        "run_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("suite_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("agent_output", sa.Text(), nullable=True),
        sa.Column("trace_json", sa.JSON(), nullable=False),
        sa.Column("evaluations_json", sa.JSON(), nullable=False),
        sa.Column("cassette_json", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["suite_id"], ["suite_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_run_records_suite_id", "run_records", ["suite_id"])


def downgrade() -> None:
    op.drop_index("ix_run_records_suite_id", table_name="run_records")
    op.drop_table("run_records")
    op.drop_index("ix_suite_runs_project_id", table_name="suite_runs")
    op.drop_table("suite_runs")
    op.drop_table("projects")
