FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini .

RUN python -m pip install --upgrade pip \
    && pip install .

EXPOSE 8000

CMD ["uvicorn", "work_order_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
