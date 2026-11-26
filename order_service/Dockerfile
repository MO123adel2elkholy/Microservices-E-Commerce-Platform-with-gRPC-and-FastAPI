FROM python:3.12-slim

WORKDIR /app

# Install system build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared proto definitions, compiler script, and service code
COPY proto/ ./proto/
COPY scripts/ ./scripts/
COPY product_service/ ./product_service/
COPY user_service/ ./user_service/
COPY order_service/ ./order_service/

# Compile protobuf stubs
RUN python scripts/generate_proto.py

# Expose HTTP port (8002)
EXPOSE 8002

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "order_service.main"]
