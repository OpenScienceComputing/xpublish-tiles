FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "xpublish-tiles==0.4.2" "uvicorn[standard]"

COPY serve.py .

EXPOSE 8080

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]
