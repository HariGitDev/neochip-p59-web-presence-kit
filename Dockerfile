# P59 Web Presence Kit — static build served by nginx.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Fail the image build if any {{TBD}} token survives when SITE_ENV=prod.
ARG SITE_ENV=test
RUN npm run build \
 && if [ "$SITE_ENV" = "prod" ]; then PROD_READY=1 npm run test; else npm run test; fi

FROM nginx:1.27-alpine
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1
