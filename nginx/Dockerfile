# =============================================================================
# BlingAuto API - Nginx Dockerfile
# Custom Nginx image with SSL and configuration
# =============================================================================

FROM nginx:1.25-alpine

# Install openssl for self-signed certificates
RUN apk add --no-cache openssl

# Create directories
RUN mkdir -p /etc/nginx/ssl /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy static files (optional)
COPY html /usr/share/nginx/html

# Generate self-signed SSL certificate (for pre-production)
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=FR/ST=Paris/L=Paris/O=BlingAuto/OU=IT/CN=blingauto.local" \
    && chmod 600 /etc/nginx/ssl/key.pem \
    && chmod 644 /etc/nginx/ssl/cert.pem

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
