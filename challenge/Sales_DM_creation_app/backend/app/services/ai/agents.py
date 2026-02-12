"""
LangGraph-based AI Agents for DM Generation Pipeline

改善版: 
- 言語・地域対応（日本企業なら日本語、海外企業なら英語）
- 商材情報を検索クエリに組み込み
- 複数観点での検索
- 検索結果のスコアリング
- 不適切コンテンツのフィルタリング
"""
from __future__ import annotations
from typing import List, TypedDict, Callable, Optional, Tuple
import asyncio
import re
from urllib.parse import urlparse
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


# ---- 不適切コンテンツフィルタリング ----
BLOCKED_DOMAINS = [
    "pornhub", "xvideos", "xhamster", "redtube", "youporn",
    "xnxx", "tube8", "spankbang", "beeg", "porn",
    "adult", "xxx", "sex", "hentai", "erotic",
]

BLOCKED_KEYWORDS = [
    "porn", "xxx", "adult video", "erotic", "hentai",
    "アダルト", "ポルノ", "エロ", "風俗", "デリヘル",
    "出会い系", "セフレ", "不倫",
]


def _is_inappropriate_content(text: str, url: str) -> bool:
    """不適切なコンテンツかどうかをチェック"""
    text_lower = text.lower()
    url_lower = url.lower()
    
    # ドメインチェック
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return True
    
    # キーワードチェック
    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in text_lower or keyword in text:
            return True
    
    return False


# ---- 言語・地域判定 ----
JAPANESE_TLDS = [".jp", ".co.jp", ".or.jp", ".ne.jp", ".ac.jp", ".go.jp"]
JAPANESE_DOMAINS = ["rakuten", "yahoo.co.jp", "nikkei", "recruit", "cyberagent", "mercari", "line"]

def _detect_region(url: str, company_name: str | None) -> Tuple[str, str]:
    """
    URLと会社名から地域と言語を判定
    
    Returns:
        (region, language): ("japan", "ja") or ("global", "en")
    """
    url_lower = url.lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # 日本のTLDチェック
    for tld in JAPANESE_TLDS:
        if domain.endswith(tld):
            return ("japan", "ja")
    
    # 日本の有名企業ドメインチェック
    for jp_domain in JAPANESE_DOMAINS:
        if jp_domain in domain:
            return ("japan", "ja")
    
    # 会社名に日本語が含まれているかチェック
    if company_name:
        # 日本語文字（ひらがな、カタカナ、漢字）が含まれているか
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', company_name):
            return ("japan", "ja")
    
    # デフォルトはグローバル（英語）
    return ("global", "en")


# ---- 商材からキーワード抽出 ----
def _extract_product_keywords(product_name: str, product_summary: str) -> List[str]:
    """商材情報からキーワードを抽出"""
    # 簡易的なキーワード抽出（将来的にはNLPを使用）
    keywords = []
    
    # 商材名を追加
    keywords.append(product_name)
    
    # よくあるB2B SaaSカテゴリとキーワードマッピング
    category_keywords = {
        # 日本語キーワード
        "チャットボット": ["カスタマーサポート", "顧客対応", "自動応答", "問い合わせ対応"],
        "CRM": ["顧客管理", "営業支援", "セールス", "商談管理"],
        "MA": ["マーケティング", "リード獲得", "メール配信", "ナーチャリング"],
        "HR": ["人事", "採用", "労務管理", "勤怠管理", "人材"],
        "会計": ["経理", "請求書", "経費精算", "財務"],
        "セキュリティ": ["情報漏洩", "サイバー攻撃", "認証", "アクセス管理"],
        "AI": ["業務効率化", "自動化", "DX", "デジタル変革"],
        "クラウド": ["インフラ", "サーバー", "データ管理"],
        # 英語キーワード
        "chatbot": ["customer support", "customer service", "automation"],
        "crm": ["sales", "customer relationship", "pipeline"],
        "marketing": ["lead generation", "email", "campaign"],
        "security": ["cybersecurity", "data protection", "compliance"],
    }
    
    # 商材名と要約から関連カテゴリを検出
    combined_text = f"{product_name} {product_summary}".lower()
    for category, related_keywords in category_keywords.items():
        if category.lower() in combined_text:
            keywords.extend(related_keywords)
    
    # 重複を削除
    return list(set(keywords))


# ---- LangGraph State ----
class DMState(TypedDict):
    target_url: str
    target_role: str | None
    company_name: str | None
    your_product_name: str
    your_product_summary: str
    preferred_tones: List[ToneType] | None
    
    # 追加: 検索用メタデータ
    region: str  # "japan" or "global"
    language: str  # "ja" or "en"
    product_keywords: List[str]
    
    evidences: List[EvidenceItem]
    hooks: List[HookItem]
    drafts: List[DMDraft]
    
    # Progress tracking
    progress_callback: Optional[Callable[[ProgressUpdate], None]]


# ---- Initialize Tools & LLM ----
def _get_tavily_tool(max_results: int = 5):
    """Tavily検索ツールを初期化"""
    if not settings.tavily_api_key:
        raise ExternalServiceError("Tavily API key is not configured")
    
    # 環境変数を設定（TavilySearchResultsが環境変数から読み込む場合に備えて）
    import os
    os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
    
    return TavilySearchResults(
        tavily_api_key=settings.tavily_api_key,
        max_results=max_results,
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


# ---- 検索結果のスコアリング ----
def _score_evidence(evidence_text: str, product_keywords: List[str], language: str) -> int:
    """検索結果と商材との関連度をスコアリング"""
    score = 0
    text_lower = evidence_text.lower()
    
    # 商材キーワードとのマッチ
    for keyword in product_keywords:
        if keyword.lower() in text_lower:
            score += 10
    
    # ビジネス関連キーワード（高スコア）
    business_keywords_ja = ["導入", "課題", "検討", "効率化", "改善", "強化", "投資", "DX", "成長"]
    business_keywords_en = ["implement", "challenge", "improve", "efficiency", "growth", "invest", "digital"]
    
    keywords = business_keywords_ja if language == "ja" else business_keywords_en
    for keyword in keywords:
        if keyword.lower() in text_lower:
            score += 5
    
    # ニュース・プレスリリース関連（中スコア）
    news_keywords = ["発表", "リリース", "調達", "提携", "launch", "announce", "funding", "partnership"]
    for keyword in news_keywords:
        if keyword.lower() in text_lower:
            score += 3
    
    return score


# ---- Agent Nodes ----
def researcher_node(state: DMState) -> DMState:
    """
    Researcher Agent: Tavilyを使って企業の最新情報を収集
    
    改善点:
    - 言語・地域に応じた検索クエリ
    - 商材に関連する情報を優先的に検索
    - 複数観点での検索（基本情報、商材関連、採用情報）
    - 検索結果のスコアリングとフィルタリング
    """
    callback = state.get("progress_callback")
    if callback:
        callback(ProgressUpdate(
            stage="researching",
            message="企業情報を多角的に調査中...",
            progress=10
        ))
    
    tavily = _get_tavily_tool(max_results=5)
    
    # 地域・言語を取得
    region = state.get("region", "japan")
    language = state.get("language", "ja")
    product_keywords = state.get("product_keywords", [])
    company_name = state.get("company_name") or ""
    target_url = state["target_url"]
    product_name = state["your_product_name"]
    
    # ---- 複数観点での検索クエリを構築 ----
    queries = []
    
    if language == "ja":
        # 日本語検索クエリ
        
        # 1. 基本情報・最新ニュース
        queries.append(
            f"{company_name} 最新ニュース プレスリリース 2024 2025"
            if company_name else f"site:{target_url} 最新ニュース"
        )
        
        # 2. 商材関連の課題・取り組み
        if product_keywords:
            keyword_str = " OR ".join(product_keywords[:3])
            queries.append(
                f"{company_name} {keyword_str} 課題 導入 検討"
                if company_name else f"site:{target_url} {keyword_str}"
            )
        
        # 3. 採用情報（どの部門を強化中か）
        queries.append(
            f"{company_name} 採用 求人 募集 強化"
            if company_name else f"site:{target_url} 採用"
        )
        
    else:
        # 英語検索クエリ
        
        # 1. 基本情報・最新ニュース
        queries.append(
            f"{company_name} latest news press release 2024 2025"
            if company_name else f"site:{target_url} latest news"
        )
        
        # 2. 商材関連の課題・取り組み
        if product_keywords:
            keyword_str = " OR ".join(product_keywords[:3])
            queries.append(
                f"{company_name} {keyword_str} challenges implementation"
                if company_name else f"site:{target_url} {keyword_str}"
            )
        
        # 3. 採用情報
        queries.append(
            f"{company_name} careers hiring jobs"
            if company_name else f"site:{target_url} careers"
        )
    
    # ---- 検索実行 ----
    all_results = []
    total_queries = len(queries)
    
    for idx, query in enumerate(queries):
        if callback:
            progress = 10 + int((idx + 1) / total_queries * 20)
            search_type = ["基本情報", "商材関連", "採用情報"][idx] if language == "ja" else ["Basic Info", "Product Related", "Hiring"][idx]
            callback(ProgressUpdate(
                stage="researching",
                message=f"{search_type}を検索中... ({idx + 1}/{total_queries})",
                progress=progress
            ))
        
        try:
            raw_results = tavily.invoke({"query": query})
            if raw_results:
                all_results.extend(raw_results)
        except Exception as e:
            # 個別の検索失敗は無視して続行
            print(f"Search query failed: {query}, error: {e}")
            continue
    
    if not all_results:
        raise ExternalServiceError("All search queries failed. Please try again.")
    
    # ---- 重複排除 ----
    seen_urls = set()
    unique_results = []
    for item in all_results:
        url = item.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(item)
    
    # ---- フィルタリング（不適切コンテンツ除外） ----
    filtered_results = []
    for item in unique_results:
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("url", "")
        
        if not _is_inappropriate_content(f"{title} {content}", url):
            filtered_results.append(item)
    
    if callback:
        callback(ProgressUpdate(
            stage="researching",
            message=f"検索結果をスコアリング中...",
            progress=35
        ))
    
    # ---- スコアリング ----
    scored_results = []
    for item in filtered_results:
        title = item.get("title", "")
        content = item.get("content", "")
        score = _score_evidence(f"{title} {content}", product_keywords, language)
        scored_results.append((score, item))
    
    # スコア順にソート（高い順）
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # 上位8件を採用
    top_results = [item for score, item in scored_results[:8]]
    
    # ---- EvidenceItemにマッピング ----
    evidences: List[EvidenceItem] = []
    for i, item in enumerate(top_results):
        evidences.append(
            EvidenceItem(
                source=item.get("source", "web"),
                title=item.get("title", f"Result {i+1}"),
                snippet=item.get("content", "")[:500],
                url=item.get("url", str(target_url)),
            )
        )
    
    state["evidences"] = evidences
    
    if callback:
        callback(ProgressUpdate(
            stage="researching",
            message=f"{len(evidences)}件の関連情報を収集しました",
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
    
    改善点:
    - URLと会社名から言語・地域を自動判定
    - 商材情報からキーワードを自動抽出
    """
    graph = build_dm_graph()
    
    # 言語・地域を判定
    region, language = _detect_region(str(target_url), company_name)
    
    # 商材からキーワードを抽出
    product_keywords = _extract_product_keywords(your_product_name, your_product_summary)
    
    # 進捗コールバックで判定結果を通知
    if progress_callback:
        region_label = "日本企業" if region == "japan" else "グローバル企業"
        progress_callback(ProgressUpdate(
            stage="researching",
            message=f"{region_label}として検索を開始します...",
            progress=5
        ))
    
    initial_state: DMState = {
        "target_url": str(target_url),
        "target_role": target_role,
        "company_name": company_name,
        "your_product_name": your_product_name,
        "your_product_summary": your_product_summary,
        "preferred_tones": preferred_tones or ["polite", "casual", "problem_solver"],
        # 追加: 検索用メタデータ
        "region": region,
        "language": language,
        "product_keywords": product_keywords,
        # 結果格納用
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
