FROM python:3.6-alpine3.7 as common
MAINTAINER fiaas@googlegroups.com
# Install any binary package dependencies here
RUN apk --no-cache add \
    yaml

FROM common as build
# Install build tools, and build wheels of all dependencies
RUN apk --no-cache add \
    build-base \
    git \
    yaml-dev
COPY . /skipper
WORKDIR /skipper
RUN pip wheel . --wheel-dir=/wheels/

FROM common as production
# Get rid of all build dependencies, install application using only pre-built binary wheels
COPY --from=build /wheels/ /wheels/
RUN pip install --no-index --find-links=/wheels/ --only-binary all /wheels/fiaas_skipper*.whl && \
    pip install gunicorn==19.8.1 gevent==1.3.1
EXPOSE 5000
CMD ["/usr/local/bin/gunicorn", "--worker-class", "gevent" "--bind=0.0.0.0:5000", "--log-file=-", "fiaas_skipper:app"]
