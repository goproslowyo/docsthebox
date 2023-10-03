# Build the python code into a Chainguard python image
FROM cgr.dev/chainguard/python:latest-dev as builder
RUN pip install --no-cache-dir --upgrade requests
FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /home/nonroot/.local/lib/python3.11/site-packages /home/nonroot/.local/lib/python3.11/site-packages
COPY *.py /app/
ENTRYPOINT [ "python", "/app/box-to-docs.py" ]
LABEL org.opencontainers.image.authors='goproslowyo, ritchies'
LABEL org.opencontainers.image.description="HackTheBox Machines to Notion Database for Writeups"
LABEL org.opencontainers.image.licenses='Apache-2.0'
LABEL org.opencontainers.image.source='https://github.com/goproslowyo/docsthebox'
LABEL org.opencontainers.image.url='https://infosecstreams.com'
LABEL org.opencontainers.image.vendor='InfoSecStreams'
