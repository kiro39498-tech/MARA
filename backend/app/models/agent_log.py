"""Agent Log model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class AgentLog(Base):
    """
    Stores logs of AI Agent executions, planning suggestions, and prompt metrics.
    """

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    input_data = Column(Text, nullable=True)  # JSON or text payload
    output_data = Column(Text, nullable=True)  # JSON or text response
    tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AgentLog agent={self.agent_name} action={self.action} created_at={self.created_at}>"
