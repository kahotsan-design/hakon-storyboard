# HAKON 智能剧本处理系统

将原始剧本转换为可直接驱动 AI 视频生成的镜头指令,支持三种创作模式。

## 三种模式

| 模式 | 说明 | 适用场景 |
|---|---|---|
| **普通模式(短剧)** | 标准分镜,景别+运镜+动作+对白 | 短剧、快节奏短视频 |
| **专业模式** | 五层电影级 Prompt,中英对照 | 专业影视制作,AI 视频工具(如 Runway/Pika) |
| **旁白视觉化模式** | 将旁白剧本改写为纯视觉剧本,支持闪回 | 旁白驱动的文艺片、纪录片 |

## 核心定位

系统**不生成角色和环境资产**,只负责:

```
剧情理解 → 情绪视觉化 → 动作设计 → 分镜设计 → 镜头语言生成
```

人物外貌 / 服装 / 场景资产 由外部 Asset System 负责。

## 本地开发

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env,填入你的 DeepSeek API Key
# 获取地址:https://platform.deepseek.com/
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 启动服务

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

浏览器访问 `http://localhost:8000`

## 部署

项目支持 Docker 部署,已包含 Dockerfile。

### Docker 本地运行

```bash
docker build -t hakon-storyboard .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=sk-xxx hakon-storyboard
```

### Railway 部署(推荐)

1. 推送代码到 GitHub 仓库
2. 在 [railway.app](https://railway.app) 新建项目,选择该仓库
3. 在 Railway 项目变量中设置 `DEEPSEEK_API_KEY`
4. Railway 自动构建部署,生成公网域名

详细部署文档见 `DEPLOY.md`

## 导出功能

- **Word 文档**:完整分镜报告,含封面、剧本理解、各场戏镜头表
- **TXT 文本**:AI 视频生成工具直接可用的 Prompt 文本
- 三种模式均支持顶部和底部预览区双按钮导出

## 架构

```
app/
├── main.py                      # FastAPI 后端(SSE 流式进度)
├── config.py                    # DeepSeek API 配置
├── pipeline.py                  # 流水线编排(三种模式分支)
├── agents/
│   ├── script_understanding_agent.py  # 剧本理解
│   ├── storyboard_agent.py      # 分镜导演(普通+专业模式)
│   └── narration_visual_agent.py # 旁白视觉化改写
├── schemas/
│   └── models.py                # 数据结构契约
└── services/
    ├── llm.py                   # DeepSeek LLM 客户端
    └── export.py                # Word/TXT 导出
templates/index.html             # Web 界面
static/                          # 样式、前端逻辑、Logo
```

## 技术栈

- **后端**:FastAPI + SSE(实时进度推送)
- **LLM**:DeepSeek(OpenAI 兼容协议)
- **前端**:原生 HTML/CSS/JS,响应式布局,无需构建
- **导出**:python-docx(Word 文档生成)

## 制作人员

**creator:Jiahao Zeng**
