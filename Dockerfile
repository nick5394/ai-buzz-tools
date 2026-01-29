# Use official Python runtime
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first (this layer is cached unless requirements.txt changes)
COPY requirements.txt .

# Install Python dependencies (this layer is cached)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY api/ api/
COPY data/ data/
COPY widgets/ widgets/

# Expose port
EXPOSE 8000

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
