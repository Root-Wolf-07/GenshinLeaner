"""Student authentication system: Student IDs, phone/email normalization, verification, and security fields.

Revision ID: 003_student_auth_system
Revises: 002_character_tutor_system
Create Date: 2026-10-15 06:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_student_auth_system'
down_revision: Union[str, None] = '002_character_tutor_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_id', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('normalized_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('normalized_phone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('verification_channel', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('verification_code_hash', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('verification_code_expires_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('verification_attempts', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('last_verification_sent_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('reset_token_hash', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('session_version', sa.Integer(), server_default='1', nullable=False))

        batch_op.create_index('ix_users_student_id', ['student_id'], unique=True)
        batch_op.create_index('ix_users_phone', ['phone'], unique=True)
        batch_op.create_index('ix_users_normalized_email', ['normalized_email'], unique=True)
        batch_op.create_index('ix_users_normalized_phone', ['normalized_phone'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_normalized_phone')
        batch_op.drop_index('ix_users_normalized_email')
        batch_op.drop_index('ix_users_phone')
        batch_op.drop_index('ix_users_student_id')

        batch_op.drop_column('session_version')
        batch_op.drop_column('password_changed_at')
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
        batch_op.drop_column('reset_token_expires_at')
        batch_op.drop_column('reset_token_hash')
        batch_op.drop_column('last_verification_sent_at')
        batch_op.drop_column('verification_attempts')
        batch_op.drop_column('verification_code_expires_at')
        batch_op.drop_column('verification_code_hash')
        batch_op.drop_column('verification_channel')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('normalized_phone')
        batch_op.drop_column('normalized_email')
        batch_op.drop_column('phone')
        batch_op.drop_column('student_id')
