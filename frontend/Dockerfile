# ─── StockPulse Frontend ─────────────────────────────────
# Step 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Cache npm install
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit --no-fund

# Copy source and build
COPY . .
RUN npm run build

# Step 2: Serve with nginx
FROM nginx:1.25-alpine

COPY --from=builder /app/build /usr/share/nginx/html

# Custom nginx config for SPA routing (redirect all to index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
