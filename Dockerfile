FROM python:3.11-slim

# Install system dependencies including LibreOffice for native PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/
COPY samples/ samples/

# Install project and dependencies
RUN pip install --no-cache-dir .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/court_board/ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
