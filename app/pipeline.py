"""流水线编排器：串联各步骤。

Step 1: 剧本理解（含自动风格分析，无用户手动选择）
Step 2: 分镜导演（动作增强 + 切分 + 分镜，合并一次调用）

合并理由见 storyboard_agent.py 顶部注释。
对外按步骤概念暴露进度回调。
"""
from __future__ import annotations

from typing import Callable, Optional

from app.agents.narration_visual_agent import NarrationVisualAgent
from app.agents.script_understanding_agent import ScriptUnderstandingAgent
from app.agents.storyboard_agent import StoryboardDirectorAgent
from app.schemas.models import (
    ScriptUnderstanding,
    StoryboardResult,
)


ProgressCallback = Callable[[str, str], None]


class Pipeline:
    def __init__(self, mode: str = "normal"):
        self.mode = mode
        if mode == "narration":
            self.narration_agent = NarrationVisualAgent()
            self.understanding_agent = None
            self.storyboard_agent = None
        else:
            self.narration_agent = None
            self.understanding_agent = ScriptUnderstandingAgent()
            self.storyboard_agent = StoryboardDirectorAgent(mode=mode)

    def run(
        self,
        script: str,
        on_progress: Optional[ProgressCallback] = None,
    ) -> StoryboardResult:
        def emit(step: str, msg: str):
            if on_progress:
                on_progress(step, msg)

        if self.mode == "narration":
            emit("step1", "正在识别旁白与可视觉化信息…")
            emit("step2", "正在将旁白转化为空间/光线/动作/声音/道具…")
            emit("step3", "正在按五层法改写每个场景…")
            emit("step4", "正在还原对白并做一致性检查…")
            rewritten_scenes = self.narration_agent.run(script)
            emit("step4", f"旁白视觉化改写完成，共 {len(rewritten_scenes)} 个场景。")
            return StoryboardResult(
                mode=self.mode,
                title="",
                understanding=ScriptUnderstanding(),
                scenes=[],
                rewritten_scenes=rewritten_scenes,
            )

        # Step 1：剧本理解 + 自动风格分析
        emit("step1", "正在理解剧本结构、分析风格基调…")
        understanding: ScriptUnderstanding = self.understanding_agent.run(script)
        emit(
            "step1",
            f"剧本理解完成：{understanding.title}，风格={understanding.genre}，共 {len(understanding.scenes)} 场戏。",
        )

        # Step 2：动作与情绪增强（并入分镜 Agent）
        emit("step2", "正在增强人物动作与情绪表现…")

        # Step 3：镜头切分（并入分镜 Agent）
        emit("step3", "正在按动作/情绪/信息变化切分镜头…")

        # Step 4：分镜设计
        emit("step4", "正在设计分镜与镜头语言…")
        scenes = self.storyboard_agent.run(understanding)
        total = sum(len(s.shots) for s in scenes)
        emit("step4", f"分镜生成完成，共 {len(scenes)} 场、{total} 个镜头。")

        return StoryboardResult(
            mode=self.mode,
            title=understanding.title,
            understanding=understanding,
            scenes=scenes,
        )
