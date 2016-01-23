FROM eliostvs/tomate

ENV PROJECT /code/

COPY ./ $PROJECT

RUN apt-get update -qq && apt-get -yqq install gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base

WORKDIR $PROJECT

ENTRYPOINT ["make"]

CMD ["test"]