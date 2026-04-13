FROM dhi.io/python:3.13-dev AS builder
 
WORKDIR /app
 
ENV PATH="/app/venv/bin:$PATH"
 
RUN python -m venv /app/venv
 
COPY requirements.txt .
 
RUN pip install --no-cache-dir -r requirements.txt
 
 
FROM dhi.io/python:3.13
 
WORKDIR /app
 
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
 
COPY --from=builder /app/venv /app/venv
COPY app/ ./app/
 
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
 
EXPOSE 3000
 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]