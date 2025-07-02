FROM ruby:3.3-slim

# Install build dependencies and github-linguist
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git build-essential cmake pkg-config \
        libgit2-dev libicu-dev libicu72 && \
    gem install --no-document github-linguist && \
    apt-get purge -y build-essential cmake pkg-config libgit2-dev libicu-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["github-linguist"]