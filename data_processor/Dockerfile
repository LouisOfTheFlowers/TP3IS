# Data Processor Service Dockerfile
# Protocol: XML-RPC
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY data_processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY data_processor/ .

# Copy crawler scripts
COPY crawler/ ./crawler/

# Expose XML-RPC port and HTTP port
EXPOSE 8000
EXPOSE 8001

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV XMLRPC_PORT=8000
ENV HTTP_PORT=8001
ENV XMLRPC_HOST=0.0.0.0
ENV XML_SERVICE_URL=http://xml-service:5000/graphql

# Create a startup script to run both servers
RUN echo '#!/bin/bash\npython xmlrpc_server.py &\npython http_server.py' > /app/start.sh && chmod +x /app/start.sh

# Run both XML-RPC and HTTP servers
CMD ["/bin/bash", "/app/start.sh"]

