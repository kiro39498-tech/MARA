"""User, Role, and Permission models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Table,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


# Association tables for many-to-many relationships
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base, TimeStampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Relationships
    roles = relationship(
        "Role", secondary=user_roles, back_populates="users", lazy="selectin"
    )
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "Notification",
        lazy="select",
        cascade="all, delete-orphan",
    )

    @property
    def permissions(self):
        """Flatten unique permissions across assigned roles."""
        unique_permissions = {}
        for role in self.roles or []:
            for permission in role.permissions or []:
                unique_permissions[permission.id] = permission
        return list(unique_permissions.values())

    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base, TimeStampMixin):
    """Role model for role-based access control."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    users = relationship(
        "User", secondary=user_roles, back_populates="roles", lazy="select"
    )
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base, TimeStampMixin):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    resource = Column(
        String(50), nullable=False
    )  # e.g., 'products', 'sales', 'users'
    action = Column(
        String(50), nullable=False
    )  # e.g., 'create', 'read', 'update', 'delete'

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="select",
    )

    def __repr__(self):
        return f"<Permission {self.name}>"


class PasswordResetToken(Base):
    """Hashed reset tokens used by forgot-password flow."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    requested_ip = Column(String(45), nullable=True)
    requested_user_agent = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user = relationship(
        "User", back_populates="password_reset_tokens", lazy="select"
    )

    def __repr__(self):
        return (
            f"<PasswordResetToken user_id={self.user_id} "
            f"expires_at={self.expires_at}>"
        )
