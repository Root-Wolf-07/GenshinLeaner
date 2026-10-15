"""Character tutor system migration: sessions, messages, audio assets, XP, and achievements.

Revision ID: 002_character_tutor_system
Revises: 001_initial_schema
Create Date: 2026-10-14 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_character_tutor_system'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. tutor_sessions
    op.create_table(
        'tutor_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('interaction_mode', sa.String(length=50), nullable=False, server_default='multimodal'),
        sa.Column('student_level', sa.String(length=50), nullable=False, server_default='undergraduate'),
        sa.Column('difficulty', sa.String(length=50), nullable=False, server_default='intermediate'),
        sa.Column('language', sa.String(length=20), nullable=False, server_default='en'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('selected_document_ids', sa.JSON(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.Column('session_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tutor_sessions_user_id', 'tutor_sessions', ['user_id'])
    op.create_index('ix_tutor_sessions_tutor_id', 'tutor_sessions', ['tutor_id'])
    op.create_index('ix_tutor_sessions_subject', 'tutor_sessions', ['subject'])
    op.create_index('idx_tutor_session_user_status', 'tutor_sessions', ['user_id', 'status'])
    op.create_index('idx_tutor_session_user_tutor', 'tutor_sessions', ['user_id', 'tutor_id'])

    # 2. tutor_session_messages
    op.create_table(
        'tutor_session_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=False, server_default='ask_question'),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('animation_state', sa.JSON(), nullable=False),
        sa.Column('audio_id', sa.String(length=36), nullable=True),
        sa.Column('message_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tutor_session_messages_session_id', 'tutor_session_messages', ['session_id'])
    op.create_index('idx_tutor_message_session_created', 'tutor_session_messages', ['session_id', 'created_at'])

    # 3. audio_assets
    op.create_table(
        'audio_assets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('tutor_id', sa.String(length=50), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='tts_output'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ready'),
        sa.Column('file_format', sa.String(length=20), nullable=False, server_default='mp3'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('timing_data', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audio_assets_user_id', 'audio_assets', ['user_id'])
    op.create_index('ix_audio_assets_session_id', 'audio_assets', ['session_id'])
    op.create_index('idx_audio_user_session', 'audio_assets', ['user_id', 'session_id'])
    op.create_index('idx_audio_status_expires', 'audio_assets', ['status', 'expires_at'])

    # 4. xp_transactions
    op.create_table(
        'xp_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('idempotency_key', sa.String(length=120), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_xp_transactions_user_id', 'xp_transactions', ['user_id'])
    op.create_index('ix_xp_transactions_idempotency_key', 'xp_transactions', ['idempotency_key'], unique=True)
    op.create_index('idx_xp_user_category', 'xp_transactions', ['user_id', 'category'])

    # 5. user_achievements
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('achievement_key', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='mastery'),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('achievement_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'])
    op.create_index('ix_user_achievements_achievement_key', 'user_achievements', ['achievement_key'])
    op.create_index('idx_user_achievement_unique', 'user_achievements', ['user_id', 'achievement_key'], unique=True)


def downgrade() -> None:
    op.drop_table('user_achievements')
    op.drop_table('xp_transactions')
    op.drop_table('audio_assets')
    op.drop_table('tutor_session_messages')
    op.drop_table('tutor_sessions')
