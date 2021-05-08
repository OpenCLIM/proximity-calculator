FROM osgeo/gdal:alpine-ultrasmall-3.2.0

RUN apk add --no-cache --upgrade bash

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python

RUN mkdir /src

WORKDIR /src

COPY script.py .

CMD python script.py
