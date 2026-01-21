from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("brand", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "download_tokens",
        sa.Column("token", sa.String(), primary_key=True),
        sa.Column("artifact_id", sa.String(), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table("download_tokens")
    op.drop_table("artifacts")
