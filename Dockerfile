FROM gliderlabs/alpine:3.6
MAINTAINER fiaas@googlegroups.com
RUN apk-install python py-pip ca-certificates
COPY . /skipper
WORKDIR /skipper
EXPOSE 5000
RUN pip install .
CMD ["skipper"]
