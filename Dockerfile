# Build the python code into a Chainguard python image
FROM cgr.dev/chainguard/python:latest-dev as builder
RUN pip install --no-cache-dir --upgrade requests
FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /home/nonroot/.local/lib/python3.11/site-packages /home/nonroot/.local/lib/python3.11/site-packages
COPY *.py /app/
ENTRYPOINT [ "python", "/app/box-to-docs.py" ]
