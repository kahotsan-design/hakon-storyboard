"""Word 文档导出服务：生成完整分镜文档。

结构：封面（标题+风格参数+统计）→ 剧本理解 → 各场戏镜头表格。
"""
from __future__ import annotations

import io
from datetime import datetime

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.schemas.models import StoryboardResult


# 冰雪色板（与前端一致）
ICE_BLUE = "5B9BD5"      # 主蓝
ICE_DEEP = "2E5C8A"      # 深蓝标题
ICE_LIGHT = "DEEBF7"     # 浅蓝底
ICE_WHITE = "FFFFFF"
ICE_GREY = "595959"
ICE_BG = "F2F7FC"


def _set_cell_bg(cell, color_hex: str):
    """设置单元格背景色。"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {
        qn("w:val"): "clear",
        qn("w:color"): "auto",
        qn("w:fill"): color_hex,
    })
    tc_pr.append(shd)


def _set_cell_text(cell, text: str, *, bold=False, color=None, size=10, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(text or "")
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _set_run_east_asia(run, font_name: str = "微软雅黑"):
    """安全设置 run 的东亚字体。"""
    run.font.name = font_name
    rPr = run.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)


def build_storyboard_doc(result: StoryboardResult) -> bytes:
    if result.mode == "narration":
        return build_narration_doc(result)

    doc = Document()

    # 全局字体
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    # 页边距
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    # ─── 封面 ───
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.space_before = Pt(60)
    run = title_p.add_run("HAKON 智能剧本处理系统")
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub_p.add_run("分 镜 导 演 报 告")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
    run.font.name = "微软雅黑"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    # 分隔线
    doc.add_paragraph()

    # 标题信息块
    title_block = doc.add_table(rows=1, cols=1)
    title_block.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = title_block.cell(0, 0)
    _set_cell_bg(cell, ICE_LIGHT)
    _set_cell_text(
        cell,
        result.title,
        bold=True,
        color=ICE_DEEP,
        size=18,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    # 表格宽度
    for c in title_block.columns:
        c.width = Cm(16)

    # AI 分析的风格基调
    doc.add_paragraph()
    u = result.understanding
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"风格类型：{u.genre}    基调：{u.tone}")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string(ICE_GREY)

    # 统计
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        f"共 {len(result.understanding.scenes)} 场戏  ·  "
        f"{result.total_shots()} 个镜头  ·  "
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(ICE_GREY)

    doc.add_page_break()

    # ─── 剧本理解 ───
    h = doc.add_paragraph()
    run = h.add_run("一、剧本理解")
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

    u = result.understanding
    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run("故事梗概")
    run.font.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
    p = doc.add_paragraph(u.logline)
    p.runs[0].font.size = Pt(11)
    p.runs[0].font.italic = True

    p = doc.add_paragraph()
    run = p.add_run("人物关系")
    run.font.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
    doc.add_paragraph(u.relationships)

    # ─── 各场戏分镜 ───
    doc.add_page_break()
    h = doc.add_paragraph()
    run = h.add_run("二、分镜详情")
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

    for idx, scene in enumerate(result.scenes, 1):
        # 场景标题
        doc.add_paragraph()
        p = doc.add_paragraph()
        run = p.add_run(f"第 {idx} 场  {scene.scene_heading}")
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

        # 场景理解摘要
        sc_understanding = next(
            (s for s in u.scenes if s.scene_id == scene.scene_id), None
        )
        if sc_understanding:
            p = doc.add_paragraph()
            run = p.add_run(f"冲突节点：{sc_understanding.conflict}")
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor.from_string(ICE_GREY)
            p = doc.add_paragraph()
            run = p.add_run(f"情绪走向：{sc_understanding.emotional_arc}")
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor.from_string(ICE_GREY)

        # 镜头表格 —— 每个镜头一个小表
        for shot in scene.shots:
            doc.add_paragraph()
            # 镜头编号标题
            p = doc.add_paragraph()
            run = p.add_run(f"  ▸ {shot.shot_id}  {shot.shot_type}")
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor.from_string(ICE_BLUE)

            # 字段表
            fields = [
                ("景别", shot.camera_angle),
                ("运镜", shot.camera_movement),
                ("主体", shot.main_subject),
                ("描述", shot.description),
            ]
            if shot.dialogue:
                spk = shot.speaker + "：" if shot.speaker else ""
                fields.append(("对白", spk + shot.dialogue))
            if shot.reaction:
                fields.append(("反应", shot.reaction))
            # 专业模式扩展字段
            if result.mode == "pro":
                pro_extra = [
                    ("焦段", shot.lens),
                    ("光圈", shot.aperture),
                    ("布光", shot.lighting),
                    ("调色", shot.color_grade),
                    ("氛围", shot.atmosphere),
                    ("风格参考", shot.style_ref),
                    ("时长", shot.duration),
                ]
                for label, value in pro_extra:
                    if value:
                        fields.append((label, value))

            tbl = doc.add_table(rows=len(fields), cols=2)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = "Table Grid"
            for i, (label, value) in enumerate(fields):
                label_cell = tbl.cell(i, 0)
                value_cell = tbl.cell(i, 1)
                _set_cell_bg(label_cell, ICE_LIGHT)
                _set_cell_text(label_cell, label, bold=True, color=ICE_DEEP, size=10)
                _set_cell_text(value_cell, value, size=10)
                label_cell.width = Cm(2.5)
                value_cell.width = Cm(13.5)

            # 专业模式：Full Prompt 中英对照块
            if result.mode == "pro" and shot.full_prompt and shot.full_prompt.strip():
                p = doc.add_paragraph()
                run = p.add_run("  ▸ Full Prompt（五层公式 · 英文）")
                run.font.size = Pt(10)
                run.font.bold = True
                run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
                p = doc.add_paragraph()
                run = p.add_run(shot.full_prompt.strip())
                run.font.size = Pt(9)
                run.font.italic = True
                run.font.color.rgb = RGBColor.from_string(ICE_GREY)
                run.font.name = "Consolas"
                _set_run_east_asia(run, "微软雅黑")
                # 中文对照
                if shot.full_prompt_zh and shot.full_prompt_zh.strip():
                    p = doc.add_paragraph()
                    run = p.add_run("  ▸ 中文对照")
                    run.font.size = Pt(10)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
                    p = doc.add_paragraph()
                    run = p.add_run(shot.full_prompt_zh.strip())
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor.from_string(ICE_GREY)
                    _set_run_east_asia(run, "微软雅黑")



        # 场景间分页
        if idx < len(result.scenes):
            doc.add_page_break()

    # 保存到内存
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ──────────────────────────────────────────────
# 视频 Prompt 格式转换
# ──────────────────────────────────────────────

def build_video_prompts_text(result) -> str:
    """把分镜转换为 AI 视频生成工具直接可用的纯文本 prompt 格式。

    格式参考用户提供的 DeepSeek 分镜模板：
    【镜X】
    景别。运镜。画面动作描述。
    人物台词：XXX
    无背景音乐，无字幕。
    """
    lines = []
    global_idx = 0
    for scene in result.scenes:
        lines.append(f"# {scene.scene_id} {scene.scene_heading}")
        lines.append("")
        for shot in scene.shots:
            global_idx += 1
            # 镜号用全局连续编号
            lines.append(f"【镜{global_idx}】")
            # 景别 + 运镜 + 画面描述
            parts = []
            if shot.camera_angle:
                parts.append(shot.camera_angle)
            if shot.camera_movement:
                parts.append(shot.camera_movement)
            # 画面描述：用 description
            first_line_parts = []
            if parts:
                first_line_parts.append("。".join(parts))
            desc_with_subject = []
            if shot.main_subject:
                desc_with_subject.append(shot.main_subject)
            if hasattr(shot, 'description') and shot.description:
                desc_with_subject.append(shot.description)
            if desc_with_subject:
                first_line_parts.append("，".join(desc_with_subject))
            first_line = "。".join(first_line_parts) if first_line_parts else ""
            lines.append(first_line + "。" if first_line and not first_line.endswith("。") else first_line)
            # 专业模式：如果有 full_prompt，输出英文prompt + 中文对照
            if hasattr(shot, 'full_prompt') and shot.full_prompt and shot.full_prompt.strip():
                lines.append(f"[英文Prompt] {shot.full_prompt.strip()}")
                if hasattr(shot, 'full_prompt_zh') and shot.full_prompt_zh and shot.full_prompt_zh.strip():
                    lines.append(f"[中文对照] {shot.full_prompt_zh.strip()}")
            # 台词（两种模式都保留）
            if shot.dialogue and shot.dialogue.strip():
                dlg = shot.dialogue.strip()
                spk = shot.speaker if shot.speaker else (shot.main_subject if shot.main_subject else "人物")
                lines.append(f"{spk}台词：{dlg}")
            # 结尾
            lines.append("无背景音乐，无字幕。")
            lines.append("")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


# ──────────────────────────────────────────────
# 旁白视觉化模式导出
# ──────────────────────────────────────────────

def build_narration_text(result: StoryboardResult) -> str:
    """将旁白视觉化改写结果导出为纯文本剧本正文。"""
    lines = []
    lines.append("旁白视觉化改写剧本")
    lines.append("=" * 40)
    lines.append("")
    for scene in result.rewritten_scenes:
        if scene.body:
            lines.append(scene.body.strip())
        else:
            lines.append(f"{scene.scene_id} {scene.scene_heading}")
        if scene.note:
            lines.append("")
            lines.append(f"[改写说明] {scene.note}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_narration_doc(result: StoryboardResult) -> bytes:
    """旁白视觉化模式：生成 Word 文档。"""
    doc = Document()

    # 全局字体
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    # 封面
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.space_before = Pt(60)
    run = title_p.add_run("HAKON 智能剧本处理系统")
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub_p.add_run("旁白视觉化改写剧本")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
    _set_run_east_asia(run)

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"共 {len(result.rewritten_scenes)} 个场景 · 已删除旁白并转化为纯视觉描写")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string(ICE_GREY)

    doc.add_page_break()

    # 各场景
    for scene in result.rewritten_scenes:
        h = doc.add_paragraph()
        run = h.add_run(f"{scene.scene_id} {scene.scene_heading}")
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(ICE_DEEP)

        # 直接输出 body 正文，按换行分段
        if scene.body:
            for para in scene.body.split("\n"):
                para = para.strip()
                if not para:
                    continue
                p = doc.add_paragraph()
                p.paragraph_format.first_line_indent = Cm(0.5)
                run = p.add_run(para)
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor.from_string(ICE_GREY)
                _set_run_east_asia(run)

        if scene.note:
            p = doc.add_paragraph()
            run = p.add_run(f"改写说明：{scene.note}")
            run.font.size = Pt(10)
            run.font.italic = True
            run.font.color.rgb = RGBColor.from_string(ICE_BLUE)
            _set_run_east_asia(run)

        doc.add_paragraph()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
