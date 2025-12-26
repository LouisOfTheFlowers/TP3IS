# BI Service Node.js Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy source code
COPY . .

# Expose port
EXPOSE 5001

# Set environment variables
ENV PORT=5001
ENV NODE_ENV=production
ENV XML_SERVICE_URL=http://xml-service:5000/graphql

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Start the server
CMD ["npm", "start"]
