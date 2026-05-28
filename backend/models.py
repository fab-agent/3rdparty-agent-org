from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Organization(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    slug: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Personnel(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    organization_id: str = Field(foreign_key="organization.id")
    name: str
    slug: str
    role: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)