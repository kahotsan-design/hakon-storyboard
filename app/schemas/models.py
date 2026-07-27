"""数据结构定义：贯穿流水线的类型契约。

严格遵循资产分离原则：
- 只描述情绪 / 动作 / 镜头语言
- 不包含人物外貌、年龄、服装、脸部特征
- 不包含场景资产、光线、色彩、时间环境
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 剧本理解
# ──────────────────────────────────────────────

class DialogueLine(BaseModel):
    """一句台词 —— 带说话人，避免归属错乱。"""
    speaker: str = Field(..., description="说话人名称（剧本中的称呼）")
    line: str = Field(..., description="台词原文，逐字保留")


class CharacterState(BaseModel):
    """人物当前状态 —— 只关注情绪/目的/动作，不含外貌。"""
    name: str = Field(..., description="人物名称（剧本中的称呼）")
    emotion: str = Field("", description="当前情绪状态")
    intention: str = Field("", description="行为目的")
    current_action: str = Field("", description="当前动作表现")


class SceneBreakdown(BaseModel):
    """单场次理解结果。"""
    scene_id: str = Field(..., description="场次编号，如 S1")
    scene_heading: str = Field(..., description="场景标头，如「内景 · 办公室 · 日」")
    location_tag: str = Field("", description="场景标签（仅场所类别，不做美术设计）")
    characters: list[CharacterState] = Field(default_factory=list, description="本场出场人物状态")
    conflict: str = Field("", description="本场冲突节点")
    emotional_arc: str = Field("", description="本场情绪走向")
    summary: str = Field("", description="本场剧情摘要")
    dialogues: list[DialogueLine] = Field(default_factory=list, description="本场所有台词，带说话人，逐字保留")


class ScriptUnderstanding(BaseModel):
    """剧本结构理解。"""
    title: str = Field("", description="剧本标题（AI 提取或用户给定）")
    logline: str = Field("", description="一句话故事")
    genre: str = Field("", description="AI 自动分析的剧本风格类型，如都市现实/悬疑/爽剧等")
    tone: str = Field("", description="AI 自动分析的整体基调与改编方向")
    scenes: list[SceneBreakdown] = Field(default_factory=list)
    relationships: str = Field("", description="人物关系概述")


# ──────────────────────────────────────────────
# 分镜
# ──────────────────────────────────────────────

class Shot(BaseModel):
    """单个分镜。"""
    shot_id: str = Field("", description="镜头编号，如 S1-SH01")
    shot_type: str = Field("", description="镜头类型：建立镜头/动作镜头/情绪特写/反应镜头/对话镜头")
    camera_angle: str = Field("", description="景别：远景/中远景/中景/中近景/特写/大特写")
    camera_movement: str = Field("", description="运镜：固定/推进/拉远/跟随/手持/横摇/俯仰等")
    main_subject: str = Field("", description="当前镜头主要关注对象（人物名称）")
    action: str = Field("", description="人物正在执行的动作（增强后，自然语言描述）")
    facial_expression: str = Field("", description="面部和微表情")
    emotion: str = Field("", description="当前情绪")
    speaker: str = Field("", description="本镜台词的说话人（无台词则空）")
    dialogue: str = Field("", description="本镜对应对白原文，逐字保留")
    reaction: str = Field("", description="同镜内背景人物即时反应（无则留空）")
    # 专业模式字段（普通模式留空）
    lens: str = Field("", description="镜头焦段，如 85mm / 35mm / 24mm（专业模式）")
    aperture: str = Field("", description="光圈与景深，如 f/1.8 shallow depth of field（专业模式）")
    lighting: str = Field("", description="布光方案，如 soft side light from window, warm 3200K（专业模式）")
    color_grade: str = Field("", description="调色风格，如 teal and orange color grade（专业模式）")
    atmosphere: str = Field("", description="大气效果，如 volumetric fog, rain streaks（专业模式）")
    style_ref: str = Field("", description="风格参考，最多3个，如 Blade Runner 2049 aesthetic, shot on ARRI Alexa（专业模式）")
    duration: str = Field("", description="建议时长，如 5s（专业模式）")
    full_prompt: str = Field("", description="专业模式：按五层公式组装的完整英文AI视频prompt（喂给AI工具）")
    full_prompt_zh: str = Field("", description="专业模式：英文prompt的中文对照说明（给制作人员理解）")


class SceneStoryboard(BaseModel):
    """单场次的分镜集合。"""
    scene_id: str
    scene_heading: str
    shots: list[Shot] = Field(default_factory=list)


# ──────────────────────────────────────────────
# 旁白视觉化改写（第三种模式）
# ──────────────────────────────────────────────

class RewrittenDialogue(BaseModel):
    """改写后保留的对话。"""
    speaker: str = Field(..., description="说话人")
    line: str = Field(..., description="台词原文，逐字保留")


class RewrittenScene(BaseModel):
    """旁白视觉化改写后的单场。"""
    scene_id: str = Field(..., description="原场次编号，如 1-1")
    scene_heading: str = Field(..., description="原场景标头，如「办公室门口 日 冬」")
    body: str = Field("", description="改写后的完整剧本正文（自然叙述文本，含场景标头、视觉描写段落、对白，不含任何旁白）")
    note: str = Field("", description="改写说明：旁白信息如何被视觉化传递")


class StoryboardResult(BaseModel):
    """完整分镜结果。"""
    mode: str = Field("normal", description="模式：normal=普通模式, pro=专业模式, narration=旁白视觉化模式")
    title: str
    understanding: ScriptUnderstanding = Field(default_factory=ScriptUnderstanding)
    scenes: list[SceneStoryboard] = Field(default_factory=list)
    rewritten_scenes: list[RewrittenScene] = Field(default_factory=list, description="旁白视觉化模式：改写后的场景列表")

    def total_shots(self) -> int:
        return sum(len(s.shots) for s in self.scenes)
