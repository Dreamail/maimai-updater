"""add stat

迁移 ID: 2dcb2f7d88f6
父迁移: 5b05bdfe535e
创建时间: 2024-08-02 16:00:34.179669

"""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress

import sqlalchemy as sa
from alembic import op


revision: str = '2dcb2f7d88f6'
down_revision: str | Sequence[str] | None = '5b05bdfe535e'
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
        batch_op.add_column(sa.Column('update_times', sa.INTEGER(), nullable=True))

    # ### end Alembic commands ###


def downgrade_() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('maimai_updater_user', schema=None) as batch_op:
        batch_op.drop_column('update_times')

    # ### end Alembic commands ###

