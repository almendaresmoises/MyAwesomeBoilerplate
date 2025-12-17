from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, declared_attr

class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True, nullable=False)  # Row-level tenant isolation

Base = declarative_base(cls=Base)
