"""Customer model for customer management."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimeStampMixin


class CustomerType(str, enum.Enum):
    """Customer type enumeration."""

    INDIVIDUAL = "individual"
    BUSINESS = "business"


class Customer(Base, TimeStampMixin):
    """Customer model for storing customer profiles and credit settings."""

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_full_name", "full_name"),
        Index("ix_customers_company_name", "company_name"),
        Index("ix_customers_phone", "phone"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_city", "city"),
        Index("ix_customers_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    customer_type = Column(
        SQLEnum(CustomerType), nullable=False, default=CustomerType.INDIVIDUAL
    )
    credit_limit = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Customer {self.customer_code}: {self.full_name}>"
