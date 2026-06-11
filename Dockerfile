FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv --no-cache-dir

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY . .

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

CMD ["sh", "start.sh"]
