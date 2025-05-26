FROM alpine:latest as gitrepo
RUN apk add --no-cache git
ARG REPO=""
ARG GH_TOKEN=""
WORKDIR /
RUN git clone https://${GH_TOKEN}@${REPO} repo

FROM peaceiris/hugo:v0.145.0
COPY --from=gitrepo /repo /src
RUN apt update && \ 
    apt install -y gosu && \
    rm -rf /var/lib/apt/lists/* && \
    apt clean
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /src
ENTRYPOINT ["/entrypoint.sh"]
