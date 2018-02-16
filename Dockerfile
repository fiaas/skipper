FROM python:alpine
MAINTAINER fiaas@googlegroups.com
COPY . /skipper
WORKDIR /skipper
RUN pip install -e .
CMD ["skipper"]
