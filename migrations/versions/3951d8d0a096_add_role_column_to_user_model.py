"""Add role column to User model

Revision ID: 3951d8d0a096
Revises: b0ddbc3e7087
Create Date: 2024-10-27 14:35:19.833323

"""
from alembic import op
import sqlalchemy as sa
from website.models.models import UserRole 


# revision identifiers, used by Alembic.
revision = '3951d8d0a096'
down_revision = 'b0ddbc3e7087'
branch_labels = None
depends_on = None


def upgrade():
    # Create the enum type in the database
    user_role_enum = sa.Enum(UserRole, name='userrole')
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the column
    op.add_column('users',
        sa.Column('role', sa.Enum(UserRole), nullable=True)
    )

def downgrade():
    # Remove the column
    op.drop_column('users', 'role')
    
    # Remove the enum type
    user_role_enum = sa.Enum(UserRole, name='userrole')
    user_role_enum.drop(op.get_bind())