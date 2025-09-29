# frontend/Dockerfile
FROM node:20-alpine AS build

WORKDIR /usr/src/app

# Copy package files & install with npm
COPY package.json package-lock.json ./
RUN npm ci

# Copy source & build
COPY . .
RUN npm run build

# Serve build with nginx
FROM nginx:stable-alpine
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
