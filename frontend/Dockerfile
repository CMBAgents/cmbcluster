FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash streamlit \
    && chown -R streamlit:streamlit /app
USER streamlit

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

# Set environment variables for dark theme
ENV STREAMLIT_THEME_BASE=dark
ENV STREAMLIT_THEME_PRIMARY_COLOR=#4A9EFF
ENV STREAMLIT_THEME_BACKGROUND_COLOR=#0E1117
ENV STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR=#262730
ENV STREAMLIT_THEME_TEXT_COLOR=#FAFAFA

CMD ["streamlit", "run", "Main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--theme.base=dark", \
     "--theme.primaryColor=#4A9EFF", \
     "--theme.backgroundColor=#0E1117", \
     "--theme.secondaryBackgroundColor=#262730", \
     "--theme.textColor=#FAFAFA", \
     "--browser.gatherUsageStats=false"]
