from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class DMGeneration(Base):
    """DM生成履歴モデル"""
    __tablename__ = "dm_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False, index=True)
    target_role = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    product_summary = Column(Text, nullable=False)
    
    # Generated content (JSON)
    evidences = Column(JSON, nullable=True)
    hooks = Column(JSON, nullable=True)
    drafts = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DMDraft(Base):
    """保存されたDMドラフトモデル"""
    __tablename__ = "dm_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(Integer, nullable=True, index=True)
    
    tone = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body_markdown = Column(Text, nullable=False)
    edited_body = Column(Text, nullable=True)  # ユーザーが編集した内容
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
