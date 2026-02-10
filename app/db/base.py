from sqlalchemy.ext.declarative import declarative_base, as_declarative
from sqlalchemy import MetaData
from typing import Any

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
