FROM node:22-alpine AS build
WORKDIR /tenant
COPY TENANT/package.json TENANT/package-lock.json ./
RUN npm ci
COPY TENANT/index.html TENANT/vite.config.js ./
COPY TENANT/src ./src
ENV VITE_API_BASE_URL=/api/platform
RUN npm run build

FROM nginx:1.27-alpine
COPY API/docker/tenant-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /tenant/dist /usr/share/nginx/html
EXPOSE 80
