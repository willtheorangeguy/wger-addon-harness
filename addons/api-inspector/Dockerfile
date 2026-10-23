FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /addon
COPY main.py client.py ./
CMD ["python", "main.py"]
