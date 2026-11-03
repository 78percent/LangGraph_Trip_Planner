# syntax=docker/dockerfile:1
# 前端镜像：构建 Vue 产物，再用 nginx 托管并反代后端

# ---------- 构建阶段 ----------
FROM node:22-alpine AS build
WORKDIR /app

# 先装依赖，利用缓存
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码
COPY . .

# 高德浏览器 JS Key / 安全密钥 在「构建时」打进产物（Vite 只认 VITE_ 前缀）
# VITE_API_BASE_URL 留空 = 走同源 /api，由 nginx 反代到后端，无需填公网地址
ARG VITE_AMAP_WEB_KEY=""
ARG VITE_AMAP_SECURITY_CODE=""
ARG VITE_API_BASE_URL=""
ENV VITE_AMAP_WEB_KEY=$VITE_AMAP_WEB_KEY \
    VITE_AMAP_SECURITY_CODE=$VITE_AMAP_SECURITY_CODE \
    VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80