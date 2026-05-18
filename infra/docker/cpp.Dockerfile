# jeff-course C++ sandbox image.
#
# Used by the docker / docker-gpu runtime to compile and run user C++
# submissions inside a short-lived container. The runtime invokes us with:
#
#   docker run --rm ... jeff-course/cpp:1 bash -lc "g++ ... && /tmp/user"
#
# So we leave the default CMD as bash to keep the runtime invocation simple.

FROM debian:13-slim

LABEL org.opencontainers.image.title="jeff-course-cpp"
LABEL org.opencontainers.image.description="Sandboxed g++ build/run environment for jeff-course C++ exercises"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        g++ \
        cmake \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["bash"]
