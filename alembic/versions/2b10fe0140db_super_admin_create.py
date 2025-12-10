"""super admin create

Revision ID: 2b10fe0140db
Revises: 111fb47427ec
Create Date: 2025-12-10 11:33:27.517386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2b10fe0140db'
down_revision: Union[str, None] = '111fb47427ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add with server_default to handle existing rows
    op.add_column('admins', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # Remove the server_default after column is created
    op.alter_column('admins', 'is_super_admin', server_default=None)


def downgrade() -> None:
    op.drop_column('admins', 'is_super_admin')
