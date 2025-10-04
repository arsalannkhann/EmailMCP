FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.mcp.main:app", "--host", "0.0.0.0", "--port", "8080"]