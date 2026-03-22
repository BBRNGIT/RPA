# RPA Sandbox - Isolated Python Execution Environment
# Minimal Python image with NO network access

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/BBRNGIT/RPA"
LABEL org.opencontainers.image.description="RPA Sandbox - Isolated Python Executor"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SANDBOX_MODE=1

# Create non-root user
RUN useradd --create-home --shell /bin/false --uid 1000 sandbox

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Set working directory
WORKDIR /sandbox

# Create temp directory
RUN mkdir -p /tmp/sandbox && \
    chown -R sandbox:sandbox /sandbox /tmp/sandbox

# Copy sandbox execution script
COPY rpa/execution/code_sandbox.py /sandbox/
COPY rpa/core/ /sandbox/core/
COPY rpa/ /sandbox/rpa/

# Switch to non-root user
USER sandbox

# Default timeout
ENV SANDBOX_TIMEOUT=10

# Entry point for code execution
ENTRYPOINT ["python", "-c"]
CMD ["print('Sandbox ready')"]
