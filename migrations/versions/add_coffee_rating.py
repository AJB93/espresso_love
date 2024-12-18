"""add coffee rating

Revision ID: add_coffee_rating
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_coffee_rating'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add rating column to coffee table
    op.add_column('coffee', sa.Column('rating', sa.Integer, nullable=True))


def downgrade():
    # Remove rating column from coffee table
    op.drop_column('coffee', 'rating') 