FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

# 创建静态目录
RUN mkdir -p static/css static/uploads static/msg_uploads

EXPOSE 5000

CMD ["python", "app.py"]