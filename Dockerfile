FROM osgeo/gdal:alpine-normal-3.2.0

RUN apk add --no-cache --upgrade bash

RUN mkdir /src

WORKDIR /src

COPY script.py .

CMD python script.py
