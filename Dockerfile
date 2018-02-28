FROM gliderlabs/alpine:3.6
MAINTAINER fiaas@googlegroups.com
RUN apk-install python py-pip ca-certificates
COPY . /skipper
WORKDIR /skipper
RUN pip install -e .
CMD ["skipper"]
