FROM gliderlabs/alpine:3.6
MAINTAINER fiaas@googlegroups.com
RUN apk-install python3=3.6.1-r3 ca-certificates=20161130-r2 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
COPY . /skipper
WORKDIR /skipper
EXPOSE 5000
RUN pip3 install .
CMD ["skipper"]
