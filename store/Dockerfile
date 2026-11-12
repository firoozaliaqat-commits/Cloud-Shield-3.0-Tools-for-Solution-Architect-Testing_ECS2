FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.2 prometheus-client==0.21.1
COPY store/ /app/
USER 65534:65534
CMD ["uvicorn","main:APP","--host","0.0.0.0","--port","8081"]
