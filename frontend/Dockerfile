# Stage 1: Build Stage
FROM node:22-alpine@sha256:41e4389f3d988d2ed55392df4db1420ad048ae53324a8e2b7c6d19508288107e AS build

# Install requirements
RUN mkdir -p /app
COPY package.json package-lock.json /app
WORKDIR /app
RUN npm install

# Copy application and build
COPY . /app
RUN npm run build

# Stage 2: Production Stage
FROM nginxinc/nginx-unprivileged:mainline-alpine@sha256:65e3e85dbaed8ba248841d9d58a899b6197106c23cb0ff1a132b7bfe0547e4c0 AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
