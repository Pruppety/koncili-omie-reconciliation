FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY scripts/ scripts/
COPY pyproject.toml .

RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app/src

ENTRYPOINT ["reconciler"]
