FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保 Python 输出不缓冲
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 确保启动脚本有执行权限
RUN chmod +x start.sh

# Railway 会注入 PORT 环境变量，启动脚本读取它
CMD ["./start.sh"]
