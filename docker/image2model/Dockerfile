FROM alpine:3.23

LABEL maintainer="cmahnke@gmail.com"
LABEL "com.github.actions.name"="Open source Exhibition tools"
LABEL "com.github.actions.description"="A collection of open source tools for creating exhibitions"
LABEL org.opencontainers.image.source https://github.com/cmahnke/oss-exhibition-tools

ENV BUILD_DEPS="git gcc py3-pip" \
    RUN_DEPS="bash busybox blender-headless blender-shared py3-blender py3-pillow" \
    BUILD_CONTEXT=/mnt/build-context \
    PIP_ROOT_USER_ACTION=ignore

RUN --mount=target=/mnt/build-context \
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
    apk --update upgrade && \
    apk add --no-cache $RUN_DEPS $BUILD_DEPS && \
    mkdir /opt/scripts && \
    cp $BUILD_CONTEXT/docker/image2model/scripts/generate-models.py /opt/scripts/ && \
    pip install --break-system-packages -r /mnt/build-context/docker/image2model/scripts/requirements.txt && \
    blender-headless --python /opt/scripts/generate-models.py -- -s && \
    cp $BUILD_CONTEXT/docker/image2model/scripts/image2model /usr/local/bin/ && \
    chmod +x /usr/local/bin/image2model && \
# Cleanup
    cd / && \
    apk del $BUILD_DEPS libjpeg && \
    rm -rf $BUILD_DIR /var/cache/apk/* /root/.cache

ENTRYPOINT ["/usr/local/bin/image2model"]
