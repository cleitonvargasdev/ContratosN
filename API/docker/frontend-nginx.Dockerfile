FROM node:20-alpine AS build

WORKDIR /frontend

COPY FRONTEND/package*.json ./

RUN npm ci

COPY FRONTEND/ ./

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginx:1.27-alpine

COPY API/docker/nginx-site.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80
