FROM python:3.11

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock .python-version ./

RUN uv sync

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py"]