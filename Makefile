PACKAGE = tomate-alarm-plugin
AUTHOR = eliostvs
PACKAGE_ROOT = $(CURDIR)
TOMATE_PATH = $(PACKAGE_ROOT)/tomate
DATA_PATH = $(PACKAGE_ROOT)/data
PLUGIN_PATH = $(DATA_PATH)/plugins
PYTHONPATH = PYTHONPATH=$(TOMATE_PATH):$(PLUGIN_PATH)
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
DOCKER_IMAGE_NAME= $(AUTHOR)/tomate
PROJECT = home:eliostvs:tomate
DEBUG = TOMATE_DEBUG=true
OBS_API_URL = https://api.opensuse.org:443/trigger/runservice?project=$(PROJECT)&package=$(PACKAGE)
WORK_DIR=/code

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	TEST_PREFIX = xvfb-run -a
else
	TEST_PREFIX =
endif

submodule:
	git submodule init
	git submodule update --recursive --remote

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) $(DEBUG) $(TEST_PREFIX) py.test test_plugin.py --cov=$(PLUGIN_PATH)

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-pull:
	docker pull $(DOCKER_IMAGE_NAME)

docker-test:
	docker run --rm -v $(PACKAGE_ROOT):$(WORK_DIR) --workdir $(WORK_DIR)  $(DOCKER_IMAGE_NAME)

docker-all: docker-clean docker-pull docker-test docker-enter

docker-enter:
	docker run --rm -v $(PACKAGE_ROOT):$(WORK_DIR) --workdir $(WORKDIR) -it --entrypoint="bash" $(DOCKER_IMAGE_NAME)

trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)
