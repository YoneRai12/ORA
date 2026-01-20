import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    String, DateTime, Enum, ForeignKey, Integer, Float,
    UniqueConstraint, Index, Text
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

def utcnow():
    return datetime.utcnow()

class ConversationScope(str, enum.Enum):
    personal = "personal"
    workspace = "workspace"

class AuthorRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    tool = "tool"
    system = "system"

class RunStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    error = "error"
    canceled = "canceled"

class RunRoute(str, enum.Enum):
    local_vlm = "local_vlm"
    cloud_codex = "cloud_codex"
    cloud_vision = "cloud_vision"
    local_text = "local_text"
    cloud_text = "cloud_text"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), default="Unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    identities: Mapped[list["UserIdentity"]] = relationship(back_populates="user")
    participants: Mapped[list["ConversationParticipant"]] = relationship(back_populates="user")

class UserIdentity(Base):
    __tablename__ = "user_identities"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), primary_key=True)  # discord/google/apple
    provider_id: Mapped[str] = mapped_column(String(128), index=True)
    auth_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="identities")

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_identity_provider_pid"),
    )

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scope: Mapped[ConversationScope] = mapped_column(Enum(ConversationScope), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New Conversation")
    next_seq: Mapped[int] = mapped_column(Integer, default=1)  # 連番競合回避
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    participants: Mapped[list["ConversationParticipant"]] = relationship(back_populates="conversation")
    bindings: Mapped[list["ConversationBinding"]] = relationship(back_populates="conversation")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")
    runs: Mapped[list["Run"]] = relationship(back_populates="conversation")

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner/admin/member/readonly
    client_role: Mapped[str] = mapped_column(String(30), default="discord_user")
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participants")

class ConversationBinding(Base):
    __tablename__ = "conversation_bindings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)   # discord/web
    external_id: Mapped[str] = mapped_column(String(200), index=True) # "guild:channel:thread" or "room_id"

    conversation: Mapped["Conversation"] = relationship(back_populates="bindings")

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_binding_provider_external"),
    )

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True, index=True)  # nullable
    author: Mapped[AuthorRole] = mapped_column(Enum(AuthorRole), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    seq: Mapped[int] = mapped_column(Integer, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    run: Mapped["Run"] = relationship(back_populates="messages", foreign_keys=[run_id])

    __table_args__ = (
        Index("ix_messages_conv_seq", "conversation_id", "seq"),
        UniqueConstraint("conversation_id", "author", "idempotency_key", name="uq_msg_idempotency"),
    )

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    user_message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), index=True)
    assistant_message_id: Mapped[str | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), index=True, default=RunStatus.queued)
    route: Mapped[RunRoute | None] = mapped_column(Enum(RunRoute), nullable=True)
    route_reasons: Mapped[list] = mapped_column(JSON, default=list)
    policy_version: Mapped[str] = mapped_column(String(40), default="v1")
    parent_run_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="runs")
    messages: Mapped[list["Message"]] = relationship(back_populates="run", foreign_keys=[Message.run_id])
    tool_invocations: Mapped[list["ToolInvocation"]] = relationship(back_populates="run", cascade="all, delete-orphan")

class ToolInvocation(Base):
    __tablename__ = "tool_invocations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(60), index=True)
    input: Mapped[dict] = mapped_column(JSON, default=dict)
    output_summary: Mapped[str] = mapped_column(Text, default="")
    artifact_ref: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    run: Mapped["Run"] = relationship(back_populates="tool_invocations")
