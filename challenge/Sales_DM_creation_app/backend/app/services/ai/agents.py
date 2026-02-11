"""
LangGraph-based AI Agents for DM Generation Pipeline
"""
from __future__ import annotations
from typing import List, TypedDict, Callable, Optional
import asyncio
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.schemas.dm import (
    EvidenceItem,
    HookItem,
    DMDraft,
    ToneType,
    ProgressUpdate,
)
from app.core.security import ExternalServiceError


# ---- LangGraph State ----
class DMState(TypedDict):
    target_url: str
    target_role: str | None
    company_name: str | None
    your_product_name: str
    your_product_summary: str
    preferred_tones: List[ToneType] | None
    
    evidences: List[EvidenceItem]
    hooks: List[HookItem]
    drafts: List[DMDraft]
    
    # Progress tracking
    progress_callback: Optional[Callable[[ProgressUpdate], None]]


# ---- Initialize Tools & LLM ----
def _get_tavily_tool():
    """Tavily検索ツールを初期化"""
    if not settings.tavily_api_key:
        raise ExternalServiceError("Tavily API key is not configured")
    
    # 環境変数を設定（TavilySearchResultsが環境変数から読み込む場合に備えて）
    import os
    os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
    
    return TavilySearchResults(
        tavily_api_key=settings.tavily_api_key,  # パラメータ名を確認
        max_results=settings.tavily_max_results,
        search_depth=settings.tavily_search_depth,
        include_answer=True,
    )


def _get_llm():
    """LLMを初期化"""
    if not settings.openai_api_key:
        raise ExternalServiceError("OpenAI API key is not configured")
    
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        openai_api_key=settings.openai_api_key,
    )


# ---- Agent Nodes ----
def researcher_node(state: DMState) -> DMState:
    """
    Researcher Agent: Tavilyを使って企業の最新情報を収集
    """
    callback = state.get("progress_callback")
    if callback:
        callback(ProgressUpdate(
            stage="researching",
            message="企業の最新動向を調査中...",
            progress=20
        ))
    
    tavily = _get_tavily_tool()
    
    # 検索クエリを構築
    query_parts = [
        f"Website: {state['target_url']}",
        "Find the company's latest news, product updates, funding rounds, challenges, and vision from the last 3 months.",
    ]
    if state.get("company_name"):
        query_parts.append(f"Company name: {state['company_name']}")
    if state.get("target_role"):
        query_parts.append(f"Target role: {state['target_role']}")
    
    query = " ".join(query_parts)
    
    try:
        raw_results = tavily.invoke({"query": query})
    except Exception as e:
        raise ExternalServiceError(f"Tavily search failed: {str(e)}")
    
    # EvidenceItemにマッピング
    evidences: List[EvidenceItem] = []
    for i, item in enumerate(raw_results or []):
        evidences.append(
            EvidenceItem(
                source=item.get("source", "web"),
                title=item.get("title", f"Result {i+1}"),
                snippet=item.get("content", "")[:500],  # 500文字に制限
                url=item.get("url", str(state["target_url"])),
            )
        )
    
    state["evidences"] = evidences
    
    if callback:
        callback(ProgressUpdate(
            stage="researching",
            message=f"{len(evidences)}件の情報を収集しました",
            progress=40
        ))
    
    return state


def analyzer_node(state: DMState) -> DMState:
    """
    Analyzer Agent: 収集データから「刺さるポイント」を3つ特定
    """
    callback = state.get("progress_callback")
    if callback:
        callback(ProgressUpdate(
            stage="analyzing",
            message="インサイトを分析中...",
            progress=50
        ))
    
    llm = _get_llm()
    
    if not state.get("evidences"):
        raise ValueError("No evidences found. Research step must be completed first.")
    
    evidence_text = "\n\n".join(
        [
            f"[{i}] {e.title}\n{e.snippet}\nURL: {e.url}"
            for i, e in enumerate(state["evidences"])
        ]
    )
    
    system_prompt = (
        "You are a B2B SaaS sales strategist specializing in personalized outbound messaging.\n"
        "Based on the evidence below, extract exactly 3 highly relevant hooks for a personalized cold DM.\n"
        "Each hook should:\n"
        "- Focus on a specific initiative, achievement, challenge, or recent development\n"
        "- Be grounded in concrete evidence\n"
        "- Be compelling as an opening line in a cold DM\n"
        "- Relate to business outcomes or pain points\n\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "hooks": [\n'
        "    {\n"
        '      "id": 0,\n'
        '      "title": "Short hook title (max 50 chars)",\n'
        '      "reason": "Why this hook is compelling (2-3 sentences)",\n'
        '      "related_evidence_indices": [0, 2]\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )
    
    user_prompt = f"EVIDENCE:\n{evidence_text}"
    
    try:
        structured_llm = llm.with_structured_output(
            schema={
                "title": "HooksResponse",
                "type": "object",
                "properties": {
                    "hooks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "reason": {"type": "string"},
                                "related_evidence_indices": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                },
                            },
                            "required": [
                                "id",
                                "title",
                                "reason",
                                "related_evidence_indices",
                            ],
                        },
                    }
                },
                "required": ["hooks"],
            }
        )
        
        result = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        
        hooks_raw = result.get("hooks", [])
        hooks: List[HookItem] = []
        for i, h in enumerate(hooks_raw):
            hooks.append(
                HookItem(
                    id=int(h.get("id", i)),
                    title=h["title"],
                    reason=h["reason"],
                    related_evidence_indices=h.get("related_evidence_indices", []),
                )
            )
        
        state["hooks"] = hooks
        
        if callback:
            callback(ProgressUpdate(
                stage="analyzing",
                message=f"{len(hooks)}個のインサイトを抽出しました",
                progress=70
            ))
        
        return state
        
    except Exception as e:
        raise ExternalServiceError(f"Hook extraction failed: {str(e)}")


def copywriter_node(state: DMState) -> DMState:
    """
    Copywriter Agent: 指定されたトーンでDMを執筆
    """
    callback = state.get("progress_callback")
    
    llm = _get_llm()
    
    tones: List[ToneType] = (
        state["preferred_tones"]
        if state.get("preferred_tones")
        else ["polite", "casual", "problem_solver"]
    )
    
    tone_labels = {
        "polite": "礼儀正しい・丁寧なトーン",
        "casual": "カジュアル・親しみやすいトーン",
        "problem_solver": "課題解決型・ビジネス重視のトーン",
    }
    
    hooks_text = "\n\n".join(
        [
            f"[Hook {h.id}] {h.title}\n理由: {h.reason}"
            for h in state["hooks"]
        ]
    )
    
    evidence_brief = "\n\n".join(
        [
            f"[{i}] {e.title}\n{e.snippet[:200]}..."
            for i, e in enumerate(state["evidences"])
        ]
    )
    
    system_prompt = (
        "You are a top-tier B2B SaaS outbound sales copywriter in Japanese.\n"
        "Based on the hooks and evidence, craft highly personalized cold DMs.\n"
        "Output each DM in **Markdown** format with:\n"
        "- A compelling subject line as a Markdown heading (e.g., `## 件名案`)\n"
        "- Body with natural paragraphs and bullet points where appropriate\n"
        "- Natural Japanese that sounds professional, not translated\n"
        "- Reference specific evidence/hooks to show personalization\n"
        "- Include a clear call-to-action\n"
    )
    
    user_prompt = f"""
ターゲット情報:
- URL: {state['target_url']}
- 役職: {state.get('target_role') or '不明'}
- 会社名: {state.get('company_name') or '不明'}

あなたの商材情報:
- 商材名: {state['your_product_name']}
- 要約: {state['your_product_summary']}

利用可能なフック:
{hooks_text}

参考 Evidence（要約）:
{evidence_brief}

上記の情報を基に、指定されたトーンで1通のDMを作成してください。
相手の最近の動きや課題にしっかり紐づけ、パーソナライズされた内容にしてください。
"""
    
    drafts: List[DMDraft] = []
    total_tones = len(tones)
    
    for idx, tone in enumerate(tones):
        if callback:
            progress = 70 + int((idx + 1) / total_tones * 25)
            callback(ProgressUpdate(
                stage="writing",
                message=f"{tone_labels[tone]}でDMを生成中... ({idx + 1}/{total_tones})",
                progress=progress
            ))
        
        tone_prompt = (
            f"トーン: {tone_labels[tone]}（内部ラベル: {tone}）として DM を 1 通生成してください。"
        )
        
        try:
            structured_llm = llm.with_structured_output(DMDraft)
            draft: DMDraft = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
                HumanMessage(content=tone_prompt),
            ])
            draft.tone = tone  # 念のため上書き
            drafts.append(draft)
        except Exception as e:
            raise ExternalServiceError(f"DM generation failed for tone {tone}: {str(e)}")
    
    state["drafts"] = drafts
    
    if callback:
        callback(ProgressUpdate(
            stage="completed",
            message=f"{len(drafts)}通のDMを生成しました",
            progress=100
        ))
    
    return state


# ---- Graph Builder ----
def build_dm_graph():
    """LangGraphパイプラインを構築"""
    graph = StateGraph(DMState)
    
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("copywriter", copywriter_node)
    
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "analyzer")
    graph.add_edge("analyzer", "copywriter")
    graph.add_edge("copywriter", END)
    
    return graph.compile()


# ---- Service Function ----
async def generate_dm_async(
    target_url: str,
    target_role: str | None,
    company_name: str | None,
    your_product_name: str,
    your_product_summary: str,
    preferred_tones: List[ToneType] | None = None,
    progress_callback: Callable[[ProgressUpdate], None] | None = None,
) -> dict:
    """
    DM生成を非同期で実行
    """
    graph = build_dm_graph()
    
    initial_state: DMState = {
        "target_url": str(target_url),
        "target_role": target_role,
        "company_name": company_name,
        "your_product_name": your_product_name,
        "your_product_summary": your_product_summary,
        "preferred_tones": preferred_tones or ["polite", "casual", "problem_solver"],
        "evidences": [],
        "hooks": [],
        "drafts": [],
        "progress_callback": progress_callback,
    }
    
    # 非同期実行（実際にはLangGraphは同期的だが、将来の拡張のため）
    final_state = await asyncio.to_thread(graph.invoke, initial_state)
    
    return {
        "evidences": [e.model_dump() for e in final_state["evidences"]],
        "hooks": [h.model_dump() for h in final_state["hooks"]],
        "drafts": [d.model_dump() for d in final_state["drafts"]],
    }
