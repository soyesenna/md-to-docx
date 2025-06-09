FROM python:3.11-slim

# Install pandoc and required system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser templates/ templates/
COPY --chown=appuser:appuser gunicorn_config.py .

# Create temp directory for file uploads
RUN mkdir -p /tmp/uploads && chown appuser:appuser /tmp/uploads

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5005

# Run the application with gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]