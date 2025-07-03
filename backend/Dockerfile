# Build stage
FROM python:3.12@sha256:47d28e7d429679c31c3ea60e90857c54c7967084685e2ee287935116e5a79b92 AS builder

# Install package manager
RUN pip --no-cache-dir install -U pdm

# Install requirements
RUN mkdir -p /app
COPY pyproject.toml pdm.lock* /app
WORKDIR /app

RUN pdm --no-cache install --lockfile pdm.lock --skip=post_install --check --prod --no-editable

# Run stage
FROM python:3.12-slim@sha256:e55523f127124e5edc03ba201e3dbbc85172a2ec40d8651ac752364b23dfd733 AS runner

# Create runtime user
RUN groupadd -r appuser \
    && useradd -r -g appuser -m -d /home/appuser appuser

# Copy libraries and code
COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser --from=data . /data
COPY --chown=appuser:appuser src /app/src
COPY --chown=appuser:appuser scripts /app/scripts

WORKDIR /app

# Get debian package and security updates
# Install curl for healthcheck
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src/"

RUN python -c "from haystack.components.embedders import SentenceTransformersDocumentEmbedder; SentenceTransformersDocumentEmbedder(model='all-MiniLM-L6-v2').warm_up()"

EXPOSE 9000
CMD ["/app/scripts/entrypoint.sh"]
