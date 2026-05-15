FROM python:3.12-bookworm

WORKDIR /app

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/shared ./packages/shared
RUN pip install ./packages/shared

COPY packages/agent_core ./packages/agent_core
RUN pip install ./packages/agent_core

COPY apps/api ./api
ENV PYTHONPATH=/app

RUN useradd -m assistant
USER assistant
WORKDIR /home/assistant/workspaces

EXPOSE 54345

CMD ["uvicorn", "api.controller.main:app", "--host", "0.0.0.0", "--port", "54345"]
