from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


# Request Schemas
class EvidenceItem(BaseModel):
    source: str
    title: str
    snippet: str
    url: str


class HookItem(BaseModel):
    id: int
    title: str
    reason: str
    related_evidence_indices: List[int]


ToneType = Literal["polite", "casual", "problem_solver"]


class DMDraft(BaseModel):
    tone: ToneType
    title: str
    body_markdown: str


class GenerateDMRequest(BaseModel):
    target_url: HttpUrl = Field(..., description="ターゲット企業のURL")
    target_role: Optional[str] = Field(None, description="ターゲットの役職")
    company_name: Optional[str] = Field(None, description="会社名")
    your_product_name: str = Field(..., min_length=1, description="あなたの商材名")
    your_product_summary: str = Field(..., min_length=10, description="商材の要約（10文字以上）")
    preferred_tones: Optional[List[ToneType]] = Field(
        default=["polite", "casual", "problem_solver"],
        description="生成するトーンのリスト"
    )


# Response Schemas
class GenerateDMResponse(BaseModel):
    generation_id: Optional[int] = None
    evidences: List[EvidenceItem]
    hooks: List[HookItem]
    drafts: List[DMDraft]
    created_at: datetime


class ProgressUpdate(BaseModel):
    """進捗更新用スキーマ（SSE用）"""
    stage: Literal["researching", "analyzing", "writing", "completed"]
    message: str
    progress: int = Field(ge=0, le=100)


class SaveDraftRequest(BaseModel):
    generation_id: Optional[int] = None
    tone: ToneType
    title: str
    body_markdown: str
    edited_body: Optional[str] = None


class SaveDraftResponse(BaseModel):
    draft_id: int
    message: str
