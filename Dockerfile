# Build the python code into a Chainguard python image
FROM cgr.dev/chainguard/python:latest-dev AS builder
WORKDIR /app
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade requests

FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY box-to-docs.py models.py utils.py /app/
ENTRYPOINT [ "python", "/app/box-to-docs.py" ]
LABEL org.opencontainers.image.authors='goproslowyo, ritchies'
LABEL org.opencontainers.image.description="HackTheBox Machines to Notion Database for Writeups"
LABEL org.opencontainers.image.licenses='Apache-2.0'
LABEL org.opencontainers.image.source='https://github.com/goproslowyo/docsthebox'
LABEL org.opencontainers.image.url='https://infosecstreams.com'
LABEL org.opencontainers.image.vendor='InfoSecStreams'
