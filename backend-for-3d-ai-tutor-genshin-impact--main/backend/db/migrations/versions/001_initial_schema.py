"""Initial schema migration for AI Study Companion.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-13 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('student_level', sa.String(length=50), nullable=False, server_default='undergraduate'),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # 2. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('safe_storage_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('slide_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('doc_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_owner_id', 'documents', ['owner_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # 3. document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('slide_number', sa.Integer(), nullable=True),
        sa.Column('start_timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('end_timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_owner_id', 'document_chunks', ['owner_id'])
    op.create_index('idx_doc_owner_chunk', 'document_chunks', ['document_id', 'owner_id', 'chunk_index'])

    # 4. conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('selected_document_ids', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_owner_id', 'conversations', ['owner_id'])

    # 5. messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('message_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_conversation_created', 'messages', ['conversation_id', 'created_at'])

    # 6. study_materials
    op.create_table(
        'study_materials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('material_type', sa.String(length=50), nullable=False),
        sa.Column('student_level', sa.String(length=50), nullable=False, server_default='undergraduate'),
        sa.Column('difficulty', sa.String(length=50), nullable=False, server_default='intermediate'),
        sa.Column('content_format', sa.String(length=50), nullable=False, server_default='structured_json'),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('raw_markdown', sa.Text(), nullable=False),
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('document_ids', sa.JSON(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ready'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_study_materials_owner_id', 'study_materials', ['owner_id'])
    op.create_index('ix_study_materials_topic', 'study_materials', ['topic'])
    op.create_index('ix_study_materials_material_type', 'study_materials', ['material_type'])
    op.create_index('idx_material_owner_topic', 'study_materials', ['owner_id', 'topic'])

    # 7. quizzes
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False, server_default='intermediate'),
        sa.Column('student_level', sa.String(length=50), nullable=False, server_default='undergraduate'),
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('document_ids', sa.JSON(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quizzes_owner_id', 'quizzes', ['owner_id'])
    op.create_index('ix_quizzes_topic', 'quizzes', ['topic'])
    op.create_index('idx_quiz_owner_topic', 'quizzes', ['owner_id', 'topic'])

    # 8. quiz_attempts
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('quiz_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('submitted_answers', sa.JSON(), nullable=False),
        sa.Column('graded_results', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('earned_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])
    op.create_index('idx_attempt_user_quiz', 'quiz_attempts', ['user_id', 'quiz_id'])
    op.create_index('idx_attempt_user_completed', 'quiz_attempts', ['user_id', 'completed_at'])

    # 9. topic_mastery
    op.create_table(
        'topic_mastery',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('total_questions_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('incorrect_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mastery_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('difficulty_level', sa.String(length=50), nullable=False, server_default='intermediate'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_topic_mastery_user_id', 'topic_mastery', ['user_id'])
    op.create_index('ix_topic_mastery_topic', 'topic_mastery', ['topic'])
    op.create_index('idx_mastery_user_topic', 'topic_mastery', ['user_id', 'topic'], unique=True)
    op.create_index('idx_mastery_user_score', 'topic_mastery', ['user_id', 'mastery_score'])

    # 10. background_jobs
    op.create_table(
        'background_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_background_jobs_owner_id', 'background_jobs', ['owner_id'])
    op.create_index('ix_background_jobs_status', 'background_jobs', ['status'])
    op.create_index('idx_job_owner_status', 'background_jobs', ['owner_id', 'status'])


def downgrade() -> None:
    op.drop_table('background_jobs')
    op.drop_table('topic_mastery')
    op.drop_table('quiz_attempts')
    op.drop_table('quizzes')
    op.drop_table('study_materials')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
