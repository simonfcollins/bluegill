FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/agent_core ./packages/agent_core
RUN pip install ./packages/agent_core

COPY apps/api ./apps/api

RUN useradd -m agentuser
USER agentuser

EXPOSE 54345

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "54345"]