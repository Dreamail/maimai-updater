"""empty message

迁移 ID: 5b05bdfe535e
父迁移: 11a9a1a94259
创建时间: 2024-06-12 22:27:09.047594

"""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress

import sqlalchemy as sa
from alembic import op


revision: str = '5b05bdfe535e'
down_revision: str | Sequence[str] | None = '11a9a1a94259'
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
        batch_op.add_column(sa.Column('magic_id', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade_() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('maimai_updater_user', schema=None) as batch_op:
        batch_op.drop_column('magic_id')

    # ### end Alembic commands ###

