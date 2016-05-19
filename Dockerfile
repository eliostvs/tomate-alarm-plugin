FROM eliostvs/tomate

RUN apt-get update -qq && apt-get -yqq install gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base

WORKDIR /code/

ENTRYPOINT ["make"]

CMD ["test"]
