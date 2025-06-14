FROM node:20-alpine AS base

# 1. Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files from root and frontend
COPY package.json package-lock.json* ./
COPY frontend/package.json ./frontend/
# Install all dependencies
RUN npm ci

# 2. Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
# Copy all project files, including the frontend directory
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

# Set memory limit for Node.js to prevent OOM errors
ENV NODE_OPTIONS="--max-old-space-size=512"

# Build Next.js directly in the frontend directory
WORKDIR /app/frontend
RUN npm run build

# Return to app root for consistency
WORKDIR /app

# 3. Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# For standalone mode, copy the standalone output
COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=builder /app/frontend/public ./frontend/public

USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Start the standalone Next.js server
WORKDIR /app/frontend
CMD ["node", "server.js"]
