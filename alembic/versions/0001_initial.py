"""Initial schema matching current SQLAlchemy models.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

attendancetype = postgresql.ENUM(
    "present", "absent", "half_day", "wfh", "leave",
    name="attendancetype",
    create_type=False,
)
role = postgresql.ENUM(
    "employee", "manager", "admin",
    name="role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    attendancetype.create(bind, checkfirst=True)
    role.create(bind, checkfirst=True)

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_teams_id", "teams", ["id"])

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("role", role, nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_employees_id", "employees", ["id"])
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("status", attendancetype, nullable=True),
        sa.Column("check_in", sa.DateTime(), nullable=True),
        sa.Column("check_out", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_id", "attendance", ["id"])

    op.create_table(
        "team_trends",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_employees", sa.Integer(), nullable=False),
        sa.Column("present_count", sa.Integer(), nullable=False),
        sa.Column("absent_count", sa.Integer(), nullable=False),
        sa.Column("wfh_count", sa.Integer(), nullable=False),
        sa.Column("half_day_count", sa.Integer(), nullable=False),
        sa.Column("leave_count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_team_trends_id", "team_trends", ["id"])

    op.create_table(
        "ai_insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_ai_insights_id", "ai_insights", ["id"])


def downgrade() -> None:
    op.drop_index("ix_ai_insights_id", table_name="ai_insights")
    op.drop_table("ai_insights")
    op.drop_index("ix_team_trends_id", table_name="team_trends")
    op.drop_table("team_trends")
    op.drop_index("ix_attendance_id", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_index("ix_employees_id", table_name="employees")
    op.drop_table("employees")
    op.drop_index("ix_teams_id", table_name="teams")
    op.drop_table("teams")

    bind = op.get_bind()
    attendancetype.drop(bind, checkfirst=True)
    role.drop(bind, checkfirst=True)
