FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

ARG COMMIT_SHA=unknown
RUN pip install --no-cache-dir "xpublish-tiles @ git+https://github.com/OpenScienceComputing/xpublish-tiles.git@${COMMIT_SHA}" "xpublish-edr @ git+https://github.com/xpublish-community/xpublish-edr.git" "uvicorn[standard]"

COPY serve.py .

EXPOSE 8080

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]
