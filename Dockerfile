FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs git \
    && npm install -g @github/copilot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Codex CLI install path may evolve; keep overridable at runtime.
ARG CODEX_INSTALL_CMD="pip install --no-cache-dir codex-cli"
RUN sh -lc "$CODEX_INSTALL_CMD" || true

COPY pyproject.toml README.md /workspace/
COPY src /workspace/src
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["codex_manager_yolo"]
