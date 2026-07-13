ARG BASE_IMAGE=python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0
ARG RUNNER_SHA256
ARG ISOLATION_PROBE_SHA256

FROM ${BASE_IMAGE} AS runtime

COPY runner.py /opt/uaa-sealed-calculation/runner.py
COPY isolation_probe.py /opt/uaa-sealed-calculation/isolation_probe.py

# The final image has no shell, package manager, or general command directory.
# Python remains only as the fixed launcher for the reviewed AST interpreter and
# the non-production isolation probe used by the adversarial test suite.
RUN chmod 0444 /opt/uaa-sealed-calculation/runner.py \
        /opt/uaa-sealed-calculation/isolation_probe.py \
    && find /usr/local/bin -mindepth 1 ! -name python3.13 -delete \
    && rm -rf /usr/local/lib/python3.13/ensurepip \
        /usr/local/lib/python3.13/site-packages/pip* \
        /usr/local/lib/python3.13/site-packages/setuptools* \
    && rm -rf /bin /sbin /usr/bin /usr/sbin /lib/apk /etc/apk /root /home

FROM scratch

ARG BASE_IMAGE
ARG RUNNER_SHA256
ARG ISOLATION_PROBE_SHA256

COPY --from=runtime / /

LABEL com.ultimate-ai-agent.sealed-calculation="v1" \
    com.ultimate-ai-agent.sealed-calculation.base-image="${BASE_IMAGE}" \
    com.ultimate-ai-agent.sealed-calculation.runner-sha256="${RUNNER_SHA256}" \
    com.ultimate-ai-agent.sealed-calculation.probe-sha256="${ISOLATION_PROBE_SHA256}"

ENV LANG=C.UTF-8 \
    PATH=/usr/local/bin \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    PYTHONNOUSERSITE=1

USER 65532:65532
WORKDIR /tmp
ENTRYPOINT ["/usr/local/bin/python3.13", "-I", "-S", "/opt/uaa-sealed-calculation/runner.py"]
