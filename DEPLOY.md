# 部署指南

本项目支持多种部署方式,推荐使用 Railway。

## 方式一:Railway 部署(推荐)

Railway 对 Python + FastAPI + SSE 长连接友好,免费额度(每月 500 小时执行时间 + 5GB 流量)足够个人使用。

### 步骤

1. **推送代码到 GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit: HAKON 智能剧本处理系统"
   git branch -M main
   git remote add origin https://github.com/你的用户名/hakon-storyboard.git
   git push -u origin main
   ```

2. **在 Railway 创建项目**

   - 访问 [railway.app](https://railway.app),用 GitHub 账号登录
   - 点击 `New Project` → `Deploy from GitHub repo`
   - 选择你的 `hakon-storyboard` 仓库
   - Railway 会自动识别 `Dockerfile` 并构建

3. **配置环境变量**

   在 Railway 项目的 `Variables` 标签页添加:
   ```
   DEEPSEEK_API_KEY=sk-你的真实key
   DEEPSEEK_MODEL=deepseek-chat
   ```

4. **生成公网域名**

   在 `Settings` → `Networking` 点击 `Generate Domain`,获得一个 `xxx.up.railway.app` 的永久域名。

5. **验证**

   访问 `https://xxx.up.railway.app/api/health`,返回 JSON 即部署成功。

## 方式二:Render 部署

1. 推送代码到 GitHub
2. 在 [render.com](https://render.com) 新建 Web Service,选择仓库
3. 构建命令:`pip install -r requirements.txt`
4. 启动命令:`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 环境变量添加 `DEEPSEEK_API_KEY`

## 方式三:Docker 自部署(VPS)

```bash
# 构建镜像
docker build -t hakon-storyboard .

# 运行容器
docker run -d \
  --name hakon-storyboard \
  -p 80:8000 \
  -e DEEPSEEK_API_KEY=sk-你的key \
  --restart unless-stopped \
  hakon-storyboard
```

配合 Nginx 反向代理 + Let's Encrypt 证书即可拥有 HTTPS 域名。

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | ✅ | - | DeepSeek API 密钥 |
| `DEEPSEEK_MODEL` | ❌ | `deepseek-chat` | 模型名,可选 `deepseek-reasoner` |
| `DEEPSEEK_BASE_URL` | ❌ | `https://api.deepseek.com/v1` | API 基础地址 |
| `PORT` | ❌ | `8000` | 服务端口(部署平台自动注入) |

## 为什么不用 Vercel?

Vercel 是 Serverless 架构,对当前项目有以下限制:

- **函数超时**:免费版 10 秒、Pro 版 60 秒,而 LLM 生成一次剧本通常需要 1-3 分钟
- **不支持 SSE 长连接**:`StreamingResponse` 会被中断,前端无法接收实时进度
- **无持久进程**:每次请求是独立冷启动,`asyncio.Queue` 等进程内状态无法跨请求保留

Railway / Render 提供**持久进程**,完美匹配 FastAPI + SSE 架构。
