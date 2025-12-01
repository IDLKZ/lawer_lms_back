"""create_case_tests_table

Revision ID: 99c4db8e5577
Revises: ca0609c7823f
Create Date: 2025-11-29 15:43:25.512613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99c4db8e5577'
down_revision = 'ca0609c7823f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'case_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_tests_id'), 'case_tests', ['id'], unique=False)
    op.create_index(op.f('ix_case_tests_case_id'), 'case_tests', ['case_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_case_tests_case_id'), table_name='case_tests')
    op.drop_index(op.f('ix_case_tests_id'), table_name='case_tests')
    op.drop_table('case_tests')
