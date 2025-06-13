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

# The Next.js app is in a subdirectory, so we need to build it from there.
# The --cwd flag is not available in all npm versions, so we will change directory.
# Set memory limit for Node.js to prevent OOM errors
ENV NODE_OPTIONS="--max-old-space-size=384"
RUN npm run build

# 3. Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy production files
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/frontend/package.json ./frontend/package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/frontend/.next ./frontend/.next
COPY --from=builder /app/frontend/public ./frontend/public
COPY --from=builder /app/frontend/next.config.js ./frontend/next.config.js

USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# The working directory is /app/frontend for the workspace setup
WORKDIR /app/frontend
# Start the Next.js server using the script from package.json
CMD ["npm", "start"]
