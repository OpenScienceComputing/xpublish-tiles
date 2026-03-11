FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "xpublish-tiles @ git+https://github.com/OpenScienceComputing/xpublish-tiles.git" "uvicorn[standard]"

COPY serve.py .

EXPOSE 8080

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]
