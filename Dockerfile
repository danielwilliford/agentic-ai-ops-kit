FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY demo_data ./demo_data
COPY tests ./tests
RUN pip install --no-cache-dir fastapi pydantic uvicorn pytest httpx
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
