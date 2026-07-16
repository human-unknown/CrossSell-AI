"""
SQLAlchemy 数据模型
==================
- Task: 任务主记录（状态、进度、步骤）
- TaskInput: 关联的输入参数
- TaskResult: 关联的生成结果
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(Base):
    """异步任务记录 — 核心模型"""

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    status = Column(
        String(20),
        default="pending",
        index=True,
        comment="pending | processing | completed | failed",
    )
    progress = Column(Float, default=0.0, comment="0.0 ~ 1.0")
    current_step = Column(String(50), nullable=True, comment="当前执行步骤标识")
    steps = Column(
        JSON,
        default=list,
        comment="步骤列表: [{name, status, error}]",
    )
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # 关联
    input_data = relationship("TaskInput", back_populates="task", uselist=False, cascade="all, delete-orphan")
    result_data = relationship("TaskResult", back_populates="task", uselist=False, cascade="all, delete-orphan")


class TaskInput(Base):
    """任务输入参数"""

    __tablename__ = "task_inputs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), unique=True)

    product_name = Column(String(200), nullable=False)
    product_selling_points = Column(JSON, default=list)
    product_description = Column(Text, nullable=True)
    target_markets = Column(JSON, default=list)
    target_platforms = Column(JSON, default=list)
    content_types = Column(JSON, default=list)
    product_image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="input_data")


class TaskResult(Base):
    """任务生成结果"""

    __tablename__ = "task_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), unique=True)

    videos = Column(JSON, default=list, comment="视频列表")
    copies = Column(JSON, default=list, comment="文案列表")
    strategy = Column(JSON, nullable=True, comment="投流策略")

    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="result_data")
