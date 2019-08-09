# dockerma archs:amd64,arm,arm64:
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
COPY .wheel_cache/*.whl /links/
WORKDIR /skipper
RUN pip wheel . --no-cache-dir --wheel-dir=/wheels/ --find-links=/links/

FROM common as production
# Get rid of all build dependencies, install application using only pre-built binary wheels
COPY --from=build /wheels/ /wheels/
RUN pip install --no-index --no-cache-dir --find-links=/wheels/ --only-binary all /wheels/fiaas_skipper*.whl
EXPOSE 5000
CMD ["skipper"]
