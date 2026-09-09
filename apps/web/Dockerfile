FROM node:22.16-alpine AS build

WORKDIR /app
COPY package.json ./
# Exact direct versions are pinned. A committed npm lockfile is the remaining M1 gate.
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
