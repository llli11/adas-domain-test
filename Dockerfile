FROM node:20 AS builder

WORKDIR /opt/vue-fastapi-admin/web
COPY ./web .
RUN npm i --registry=https://registry.npmmirror.com && npm run build

FROM python:3.11-slim-bullseye

WORKDIR /opt/vue-fastapi-admin

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    sed -i "s@http://.*.debian.org@http://mirrors.ustc.edu.cn@g" /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc python3-dev nginx curl procps net-tools vim \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .
COPY ./deploy/entrypoint.sh .

RUN mkdir -p /opt/vue-fastapi-admin/web/dist && \
    chown -R www-data:www-data /opt/vue-fastapi-admin/web

COPY --from=builder --chown=www-data:www-data /opt/vue-fastapi-admin/web/dist ./web/dist

COPY ./deploy/web.conf /etc/nginx/sites-available/web.conf
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/web.conf /etc/nginx/sites-enabled/

RUN chmod 755 /opt/vue-fastapi-admin /opt/vue-fastapi-admin/web /opt/vue-fastapi-admin/web/dist && \
    find /opt/vue-fastapi-admin/web/dist -type d -exec chmod 755 {} \; && \
    find /opt/vue-fastapi-admin/web/dist -type f -exec chmod 644 {} \; && \
    chown -R www-data:www-data /var/log/nginx

ENV LANG=zh_CN.UTF-8
EXPOSE 80

ENTRYPOINT ["sh", "entrypoint.sh"]