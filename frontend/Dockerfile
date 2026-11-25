# Frontend — multi-stage production image (Debian/glibc for reliable Next SWC).
FROM node:20-bookworm-slim AS deps
WORKDIR /app
ARG TARGETARCH
COPY package.json package-lock.json ./
RUN npm ci \
    && case "$TARGETARCH" in \
         arm64) npm install --no-save @next/swc-linux-arm64-gnu@14.1.0 ;; \
         amd64) npm install --no-save @next/swc-linux-x64-gnu@14.1.0 ;; \
         *) echo "Unsupported TARGETARCH=$TARGETARCH" >&2; exit 1 ;; \
       esac

FROM node:20-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000
ARG NEXT_PUBLIC_BOOK_ID=FIXTURE_BOOK_001
ARG NEXT_PUBLIC_TENANT_ID=FIXTURE_TENANT_001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL \
    NEXT_PUBLIC_BOOK_ID=$NEXT_PUBLIC_BOOK_ID \
    NEXT_PUBLIC_TENANT_ID=$NEXT_PUBLIC_TENANT_ID \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

RUN npm run build

FROM node:20-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

RUN groupadd --system nextjs && useradd --system --gid nextjs nextjs

COPY --from=builder /app/package.json ./
COPY --from=builder /app/package-lock.json ./
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

USER nextjs
EXPOSE 3000
CMD ["npm", "run", "start"]
