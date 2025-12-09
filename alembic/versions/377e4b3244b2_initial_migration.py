from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '377e4b3244b2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=True),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('registration_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('trips',
    sa.Column('trip_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('destination', sa.String(length=200), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('trip_id')
    )
    op.create_table('tasks',
    sa.Column('task_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.trip_id'], ),
        sa.PrimaryKeyConstraint('task_id')
    )


def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('trips')
    op.drop_table('users')
