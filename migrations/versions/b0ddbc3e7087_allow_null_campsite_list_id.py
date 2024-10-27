"""allow null campsite_list_id

Revision ID: b0ddbc3e7087
Revises: 
Create Date: 2024-10-27 13:02:05.902991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0ddbc3e7087'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # SQLAlchemy Enum type for ListVisibilityType
    list_visibility_type = sa.Enum('LIST_VISIBILITY_NONE', 'LIST_VISIBILITY_PRIVATE', 
                                 'LIST_VISIBILITY_PROTECTED', 'LIST_VISIBILITY_PUBLIC',
                                 name='listvisibilitytype')
    
    # Change the nullable constraint
    op.alter_column('campsites', 'campsite_list_id',
                    existing_type=sa.Integer(),
                    nullable=True)

def downgrade():
    op.alter_column('campsites', 'campsite_list_id',
                    existing_type=sa.Integer(),
                    nullable=False)