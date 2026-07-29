"""FastAPI 后端：页面渲染 + 生成接口（SSE 流式进度）。"""
from __future__ import annotations

import asyncio
import json
import logging
import traceback
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import config
from app.pipeline import Pipeline
from app.schemas.models import StoryboardResult
from app.services.export import build_storyboard_doc, build_video_prompts_text, build_video_prompts_doc, build_narration_text

logger = logging.getLogger("ai-storyboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent  # 项目根目录
app = FastAPI(title="HAKON 智能剧本处理系统")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ──────────────────────────────────────────────
# 全局异常处理 —— 防止未捕获异常导致服务崩溃
# ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未捕获异常: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误：{str(exc)[:200]}"},
    )


# ──────────────────────────────────────────────
# 页面
# ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    warnings = config.validate()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"warnings": warnings},
    )


# ──────────────────────────────────────────────
# 请求模型
# ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    script: str = Field(..., min_length=10, description="原始剧本")
    mode: str = Field("normal", description="模式：normal=普通模式, pro=专业模式, narration=旁白视觉化模式")


# ──────────────────────────────────────────────
# 生成接口（SSE 流式）
# ──────────────────────────────────────────────

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    pipe = Pipeline(mode=req.mode)

    queue: asyncio.Queue = asyncio.Queue()

    def emit_sync(event: str, data: dict):
        try:
            queue.put_nowait((event, data))
        except Exception:
            pass

    def run_pipeline():
        try:
            def on_progress(step: str, msg: str):
                emit_sync("progress", {"step": step, "message": msg})

            emit_sync("start", {"message": "开始处理剧本"})
            result = pipe.run(req.script, on_progress=on_progress)
            emit_sync("result", result.model_dump())
            if req.mode == "narration":
                emit_sync("complete", {"total_scenes": len(result.rewritten_scenes)})
            else:
                emit_sync("complete", {"total_shots": result.total_shots()})
        except Exception as e:
            logger.error(f"生成失败: {e}\n{traceback.format_exc()}")
            emit_sync("error", {"message": str(e)[:500]})
        except BaseException as e:
            # 捕获 BaseException（如 SystemExit、KeyboardInterrupt）防止线程静默退出
            logger.error(f"生成被中断: {e}\n{traceback.format_exc()}")
            emit_sync("error", {"message": f"生成被中断：{str(e)[:200]}"})

    async def sse_stream():
        task = asyncio.create_task(asyncio.to_thread(run_pipeline))
        try:
            while True:
                try:
                    # 15秒心跳超时：如果15秒内没有新事件，发送心跳保持连接
                    event, data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    if event in ("complete", "error"):
                        break
                except asyncio.TimeoutError:
                    # 发送心跳注释，防止代理/浏览器超时断开
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ──────────────────────────────────────────────
# 健康检查 & 示例
# ──────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Render 健康检查端点。返回 200 说明服务存活。"""
    return {
        "status": "ok",
        "model": config.DEEPSEEK_MODEL,
        "api_configured": bool(config.DEEPSEEK_API_KEY),
        "warnings": config.validate(),
    }


@app.on_event("startup")
async def startup_event():
    """服务启动时记录日志。"""
    logger.info("=" * 50)
    logger.info("HAKON 智能剧本处理系统启动")
    logger.info(f"模型: {config.DEEPSEEK_MODEL}")
    logger.info(f"API 已配置: {bool(config.DEEPSEEK_API_KEY)}")
    logger.info("=" * 50)


@app.get("/api/sample")
async def sample_script():
    sample = (
        "《最后一班地铁》\n\n"
        "第一场 内景 · 地铁车厢 · 夜\n"
        "车厢空荡，只有林然和苏晚两人相对而坐。苏晚低头看手机，林然几次想开口又停下。\n"
        "林然：我……明天不在这个城市了。\n"
        "苏晚手指一顿，没抬头。\n"
        "苏晚：噢。去哪？\n"
        "林然：很远。可能不回来了。\n"
        "苏晚终于抬头，眼眶微红，但强撑着笑。\n"
        "苏晚：那祝你顺利。\n\n"
        "第二场 内景 · 地铁站台 · 夜\n"
        "列车停稳，门开。林然起身，犹豫片刻，把围巾解下递给苏晚。\n"
        "林然：外边冷。\n"
        "苏晚接过，捂紧。林然转身走向车门，又回头。\n"
        "林然：如果……算了。\n"
        "他下车。苏晚透过车窗看着他，列车门关上。苏晚终于落泪。\n"
    )
    return {"script": sample}


# ──────────────────────────────────────────────
# 导出接口
# ──────────────────────────────────────────────

class ExportRequest(BaseModel):
    data: dict


@app.post("/api/export/word")
async def export_word(req: ExportRequest):
    try:
        result = StoryboardResult.model_validate(req.data)
        doc_bytes = build_storyboard_doc(result)
        title = result.title or "storyboard"
        filename = quote(f"{title}_分镜报告.docx")
        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Word导出失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)[:200]}")


@app.post("/api/export/video-prompts")
async def export_video_prompts(req: ExportRequest):
    try:
        result = StoryboardResult.model_validate(req.data)
        text = build_video_prompts_text(result)
        title = result.title or "storyboard"
        filename = quote(f"{title}_视频Prompt.txt")
        return Response(
            content=text.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频Prompt导出失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)[:200]}")


@app.post("/api/export/prompt-word")
async def export_prompt_word(req: ExportRequest):
    """导出视频生成 Prompt 的 Word 文档。"""
    try:
        result = StoryboardResult.model_validate(req.data)
        doc_bytes = build_video_prompts_doc(result)
        title = result.title or "storyboard"
        filename = quote(f"{title}_视频Prompt.docx")
        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt Word导出失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)[:200]}")


@app.post("/api/export/narration")
async def export_narration(req: ExportRequest):
    """旁白视觉化模式：导出改写后的纯视觉化剧本文本。"""
    try:
        result = StoryboardResult.model_validate(req.data)
        if result.mode != "narration":
            raise HTTPException(status_code=400, detail="仅旁白视觉化模式支持此导出")
        text = build_narration_text(result)
        filename = quote(f"{result.title or 'storyboard'}_旁白视觉化剧本.txt")
        return Response(
            content=text.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"旁白导出失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)[:200]}")
