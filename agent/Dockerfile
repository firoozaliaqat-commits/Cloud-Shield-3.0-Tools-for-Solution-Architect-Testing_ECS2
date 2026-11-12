FROM python:3.12-alpine
ENV PYTHONUNBUFFERED=1
COPY agent/agent.py /app/agent.py
USER 65534:65534
CMD ["python","/app/agent.py"]
