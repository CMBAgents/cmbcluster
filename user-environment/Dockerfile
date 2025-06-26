FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scientific computing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create workspace directory
RUN mkdir -p /workspace && chmod 755 /workspace

# Create non-root user
RUN useradd --create-home --shell /bin/bash cmbuser \
    && chown -R cmbuser:cmbuser /app /workspace
USER cmbuser

# Set environment variables
ENV PYTHONPATH=/app
ENV WORKSPACE_DIR=/workspace

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
