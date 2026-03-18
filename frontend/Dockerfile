FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
COPY public ./public
COPY .next ./.next
COPY pages ./pages
COPY components ./components
COPY styles ./styles
RUN npm ci --production --silent || npm install --silent
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/pages ./pages
COPY --from=builder /app/components ./components
COPY --from=builder /app/styles ./styles
EXPOSE 3000
CMD ["npm", "start"]
