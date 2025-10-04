# build React app
FROM node:20 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# stage outputs dist/ for nginx
FROM alpine:3 as export
WORKDIR /out
COPY --from=build /app/dist ./
