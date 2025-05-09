FROM registry.access.redhat.com/ubi8/skopeo@sha256:f3ca0d5a15c2e3807076cee65713acb032cabf86a0222de0c23ef78a7c7df154

# See: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/

COPY ./retag.py ./retag.py.lock ./entrypoint.sh /work/

ENTRYPOINT [ "/work/entrypoint.sh" ]
