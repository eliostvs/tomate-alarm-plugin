PROJECT = tomate-alarm-plugin
AUTHOR = eliostvs
PROJECT_ROOT = $(CURDIR)
TOMATE_PATH = $(PROJECT_ROOT)/tomate
DATA_PATH = $(PROJECT_ROOT)/data
PLUGIN_PATH = $(DATA_PATH)/plugins
PYTHONPATH = PYTHONPATH=$(TOMATE_PATH):$(PLUGIN_PATH)
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PROJECT)
VERBOSITY=1

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) nosetests --verbosity=$(VERBOSITY)

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-build:
	docker build -t $(DOCKER_IMAGE_NAME) .

docker-test:
	docker run --rm -v $(PROJECT_ROOT):/code $(DOCKER_IMAGE_NAME) test

docker-all: docker-clean docker-build docker-test

docker-enter:
	docker run --rm -v $(PROJECT_ROOT):/code -it --entrypoint="bash" $(DOCKER_IMAGE_NAME)