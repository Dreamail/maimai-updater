"""add sec_id

迁移 ID: 11a9a1a94259
父迁移: ad582aba56b2
创建时间: 2024-04-05 19:49:13.054940

"""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress

import sqlalchemy as sa
from alembic import op


revision: str = '11a9a1a94259'
down_revision: str | Sequence[str] | None = 'ad582aba56b2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str) -> None:
    with suppress(KeyError):
        globals()[f"upgrade_{name}"]()


def downgrade(name: str) -> None:
    with suppress(KeyError):
        globals()[f"downgrade_{name}"]()


def upgrade_() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('maimai_updater_user', schema=None) as batch_op:
        batch_op.drop_column('sec_id')

    # ### end Alembic commands ###


def downgrade_() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('maimai_updater_user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sec_id', sa.String(), nullable=True))

    # ### end Alembic commands ###

