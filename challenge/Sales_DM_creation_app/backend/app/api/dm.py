"""
DM生成関連のAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
from datetime import datetime

from app.schemas.dm import (
    GenerateDMRequest,
    GenerateDMResponse,
    ProgressUpdate,
    SaveDraftRequest,
    SaveDraftResponse,
)
from app.services.ai.agents import generate_dm_async
from app.core.security import APIError, ValidationError
from app.db.base import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/dm", tags=["DM Generation"])


@router.post("/generate", response_model=GenerateDMResponse)
async def generate_dm(
    request: GenerateDMRequest,
    db: Session = Depends(get_db),
):
    """
    DMを生成するエンドポイント
    """
    try:
        result = await generate_dm_async(
            target_url=str(request.target_url),
            target_role=request.target_role,
            company_name=request.company_name,
            your_product_name=request.your_product_name,
            your_product_summary=request.your_product_summary,
            preferred_tones=request.preferred_tones,
        )
        
        return GenerateDMResponse(
            generation_id=None,  # TODO: DB保存後にIDを返す
            evidences=result["evidences"],
            hooks=result["hooks"],
            drafts=result["drafts"],
            created_at=datetime.now(),
        )
        
    except APIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/generate/stream")
async def generate_dm_stream(request: GenerateDMRequest):
    """
    Server-Sent Events (SSE)で進捗をストリーミングしながらDMを生成
    """
    async def event_generator():
        progress_queue = asyncio.Queue()
        
        def progress_callback(update: ProgressUpdate):
            """進捗更新をキューに追加"""
            try:
                # 実行中のイベントループを取得
                loop = asyncio.get_running_loop()
                # タスクとしてキューに追加
                asyncio.create_task(progress_queue.put(update))
            except RuntimeError:
                # イベントループが実行されていない場合はスキップ
                # （通常は発生しないはずだが、念のため）
                pass
        
        # バックグラウンドでDM生成を開始
        async def generate_task():
            try:
                await generate_dm_async(
                    target_url=str(request.target_url),
                    target_role=request.target_role,
                    company_name=request.company_name,
                    your_product_name=request.your_product_name,
                    your_product_summary=request.your_product_summary,
                    preferred_tones=request.preferred_tones,
                    progress_callback=progress_callback,
                )
                # 完了シグナル
                await progress_queue.put(None)
            except Exception as e:
                await progress_queue.put({
                    "error": str(e),
                    "stage": "error"
                })
        
        # 結果を保持する変数
        final_result = None
        error_occurred = None
        
        # 生成タスクを開始
        async def generate_with_result():
            nonlocal final_result, error_occurred
            try:
                result = await generate_dm_async(
                    target_url=str(request.target_url),
                    target_role=request.target_role,
                    company_name=request.company_name,
                    your_product_name=request.your_product_name,
                    your_product_summary=request.your_product_summary,
                    preferred_tones=request.preferred_tones,
                    progress_callback=progress_callback,
                )
                final_result = result
                await progress_queue.put(None)  # 完了シグナル
            except Exception as e:
                error_occurred = str(e)
                await progress_queue.put({"error": str(e), "stage": "error"})
        
        task = asyncio.create_task(generate_with_result())
        
        # 進捗をストリーミング
        while True:
            try:
                update = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                
                if update is None:
                    # 生成完了、最終結果を送信
                    if final_result:
                        yield f"data: {json.dumps({'stage': 'completed', 'result': final_result})}\n\n"
                    break
                
                if isinstance(update, dict) and "error" in update:
                    yield f"data: {json.dumps(update)}\n\n"
                    break
                
                # SSE形式で送信
                data = {
                    "stage": update.stage,
                    "message": update.message,
                    "progress": update.progress,
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            except asyncio.TimeoutError:
                # タイムアウト時もハートビートを送信
                yield f": heartbeat\n\n"
                # タスクが完了しているかチェック
                if task.done():
                    if error_occurred:
                        yield f"data: {json.dumps({'error': error_occurred, 'stage': 'error'})}\n\n"
                    elif final_result:
                        yield f"data: {json.dumps({'stage': 'completed', 'result': final_result})}\n\n"
                    break
                continue
        
        # タスクが完了するまで待機
        await task
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/drafts/save", response_model=SaveDraftResponse)
async def save_draft(
    request: SaveDraftRequest,
    db: Session = Depends(get_db),
):
    """
    DMドラフトを保存
    """
    # TODO: DB保存実装
    return SaveDraftResponse(
        draft_id=1,
        message="Draft saved successfully"
    )
