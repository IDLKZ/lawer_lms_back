"""create_case_results_table

Revision ID: 9ec97301ac31
Revises: 99c4db8e5577
Create Date: 2025-11-30 12:10:05.685197

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ec97301ac31'
down_revision = '99c4db8e5577'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'case_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['test_id'], ['case_tests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('test_id', 'student_id', name='uq_test_student')
    )
    op.create_index(op.f('ix_case_results_test_id'), 'case_results', ['test_id'], unique=False)
    op.create_index(op.f('ix_case_results_student_id'), 'case_results', ['student_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_case_results_student_id'), table_name='case_results')
    op.drop_index(op.f('ix_case_results_test_id'), table_name='case_results')
    op.drop_table('case_results')
