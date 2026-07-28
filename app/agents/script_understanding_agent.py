"""Step 2 Agent：剧本结构理解。

理解故事结构、场景关系、人物关系、情绪变化、冲突节点。
自动分析剧本风格类型和基调，不需要用户手动选择。
严格不生成人物外貌/年龄/服装/脸部特征。
每句台词必须带说话人，逐字保留原文。
"""
from __future__ import annotations

from app.schemas.models import ScriptUnderstanding, SceneBreakdown, CharacterState, DialogueLine
from app.services.llm import chat_json


SYSTEM_PROMPT = """你是一名专业影视剧本分析专家与改编导演。

你的任务：
1. 理解剧本的结构、场景、人物关系、情绪变化、冲突节点。
2. 自动分析剧本的风格类型（如都市现实/悬疑/爽剧/爱情/喜剧/惊悚/动作/文艺等），以及整体基调和改编方向。
3. 提取每一句台词，标注说话人，逐字保留原文。

【严格规则 —— 必须遵守】
1. 只分析人物的：情绪状态、行为目的、当前动作表现。
2. 禁止生成任何人物外貌信息：不写年龄、不写服装、不写脸部特征、不写身高体型。
3. 禁止生成场景资产信息：不写光线、不写色彩、不写时间环境、不写美术布景。
   场景标头只记录「内/外景 · 场所 · 时段」这种最简结构信息。
4. 人物名称用剧本中的称呼即可，不要编造。
5. 【最重要】dialogues 数组里每一句台词都必须带 speaker（说话人）和 line（台词原文）。
   - speaker 写说话人的名字，必须是剧本里出现过的称呼。
   - line 必须逐字保留原文，不改写、不合并、不省略、不概括。
   - 例如剧本写"林然：我……明天不在这个城市了。"，
     dialogues 里就是 {"speaker":"林然","line":"我……明天不在这个城市了。"}。
   - 一句台词一个元素，不可把多句合并成一个。
   - 【中英双版本台词规则】很多剧本中，同一角色有中文名和英文名（如「苏珊娜」=「Seraphina」），
     剧本会让这个角色用中文名说一遍中文台词，再用英文名说一遍英文台词。
     这是同一句话的中英对照，必须合并为一个 dialogue 元素：
     speaker 写「中文名（英文名）」，如「苏珊娜（Seraphina）」；
     line 写「中文原文／英文原文」，如「你好，我是苏珊娜。／Hello, I'm Seraphina.」。
     绝不可只保留中文或只保留英文，两个版本缺一不可。
   - 识别方法：如果两个相邻台词的说话人名不同（一个中文名一个英文名），
     但台词内容是互译关系，则它们是同一句话的中英对照，必须合并。
   - 【旁白/VO识别规则】很多剧本（尤其是"解说慢"风格）会大量使用旁白，
     剧本中标注为"旁白""VO""（旁白）""（VO）"的台词，都是角色的内心独白或画外解说。
     识别方法：
     a) 台词前标注了"旁白""VO""（旁白）""（VO）"等字样
     b) 角色在陈述故事、回忆、感慨，而非与在场人物对话
     c) 角色虽然在场，但嘴型不需要与台词同步（画外音）
     处理方式：
     - speaker 写「角色名（旁白）」，如「苏珊娜（旁白）」
     - line 仍逐字保留原文
     - 这些台词是旁白/画外音，不是角色当场说出口的对话
     - "解说慢"风格剧本可能旁白比例极高，甚至超过50%，必须全部识别并保留

6. 【action_beats 动作节拍 —— 与台词同等重要】
   每场戏的 action_beats 数组必须包含剧本中该场出现的【每一个动作描写、场景变化、人物移动】，按时间顺序逐条列出。
   - 一条 action_beat 对应剧本中的一个动作/事件，不可省略、不可合并、不可概括。
   - 包括但不限于：人物进出场景、人物移动、人物做某个动作、场景变化、物品传递、表情/姿态变化描写。
   - 剧本原文中的旁白描写也必须提取为 action_beat（如"万斯庄园的大门缓缓打开，我被领进客厅"就是一条 action_beat）。
   - 台词之外的所有叙事文本，都必须提取为 action_beat。
   - 开场动作（人物如何进入场景、场景如何建立）必须作为前几条 action_beat。
   - 这是为了确保分镜阶段不会丢失任何动作和情节。
   - 示例：剧本写"林然推门走进办公室，把文件摔在桌上"，
     action_beats 就是 ["林然推门走进办公室", "林然把文件摔在桌上"]。

7. 风格类型 genre 和基调 tone 由你根据剧本内容自动判断，不要问用户。

【输出格式】
返回 JSON，结构如下：
{
  "title": "剧本标题",
  "logline": "一句话故事概述",
  "genre": "自动分析的剧本风格类型",
  "tone": "整体基调与改编方向，一段话描述，包括情绪强度、动作风格、镜头节奏建议",
  "relationships": "人物关系概述（一段文字）",
  "scenes": [
    {
      "scene_id": "S1",
      "scene_heading": "内景 · 办公室 · 日",
      "location_tag": "办公场所",
      "characters": [
        {
          "name": "人物名",
          "emotion": "当前情绪",
          "intention": "行为目的",
          "current_action": "当前动作表现"
        }
      ],
      "conflict": "本场冲突节点",
      "emotional_arc": "本场情绪走向",
      "summary": "本场剧情摘要",
      "action_beats": [
        "动作节拍1：剧本中的动作描写原文",
        "动作节拍2：..."
      ],
      "dialogues": [
        {"speaker": "人物名", "line": "台词原文"}
      ]
    }
  ]
}

只返回 JSON，不要任何额外说明。"""


class ScriptUnderstandingAgent:
    def __init__(self):
        pass

    def run(self, script: str) -> ScriptUnderstanding:
        user_prompt = (
            f"【待分析剧本】\n{script}\n\n"
            f"请按指定 JSON 格式输出剧本理解结果。"
            f"务必：自动判断风格类型和基调；每句台词带说话人逐字保留。"
        )
        data = chat_json(SYSTEM_PROMPT, user_prompt, temperature=0.3)

        scenes = []
        for s in data.get("scenes", []):
            chars = [
                CharacterState(
                    name=c.get("name", ""),
                    emotion=c.get("emotion", ""),
                    intention=c.get("intention", ""),
                    current_action=c.get("current_action", ""),
                )
                for c in s.get("characters", [])
            ]
            dlgs = [
                DialogueLine(
                    speaker=d.get("speaker", ""),
                    line=d.get("line", ""),
                )
                for d in s.get("dialogues", [])
            ]
            action_beats_list = s.get("action_beats", [])
            scenes.append(
                SceneBreakdown(
                    scene_id=s.get("scene_id", f"S{len(scenes)+1}"),
                    scene_heading=s.get("scene_heading", ""),
                    location_tag=s.get("location_tag", ""),
                    characters=chars,
                    conflict=s.get("conflict", ""),
                    emotional_arc=s.get("emotional_arc", ""),
                    summary=s.get("summary", ""),
                    action_beats=action_beats_list,
                    dialogues=dlgs,
                )
            )

        return ScriptUnderstanding(
            title=data.get("title", "未命名剧本"),
            logline=data.get("logline", ""),
            genre=data.get("genre", ""),
            tone=data.get("tone", ""),
            relationships=data.get("relationships", ""),
            scenes=scenes,
        )
