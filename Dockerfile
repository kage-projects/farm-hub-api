FROM python:3.9-slim-buster

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip && pip install -e .

COPY . .

EXPOSE 3000

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--reload", "--reload-dir", "/app"]


