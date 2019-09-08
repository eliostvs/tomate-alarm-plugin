#.SILENT:

DATAPATH     = XDG_DATA_DIRS=$(CURDIR)/data:/home/$(USER)/.local/share:/usr/local/share:/usr/share
DEBUG 		 = TOMATE_DEBUG=true
DOCKER_IMAGE = eliostvs/tomate
OBS_API_URL  = https://api.opensuse.org:443/trigger/runservice
PLUGINPATH   = $(CURDIR)/data/plugins
PYTHONPATH   = PYTHONPATH=$(CURDIR)/tomate:$(PLUGINPATH)
VERSION 	 = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`
WORKDIR 	 = /code

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	ARGS = xvfb-run -a
else
	ARGS =
endif

submodule:
	git submodule init;
	git submodule update;

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" -o -iname ".coverage" -o -iname ".cache" \) -print0 | xargs -0 rm -rf

test: clean
	$(DATAPATH) $(PYTHONPATH) $(DEBUG) $(ARGS) py.test test_plugin.py --cov=$(PLUGINPATH)

docker-clean:
	docker rmi $(DOCKER_IMAGE) 2> /dev/null || echo $(DOCKER_IMAGE) not found!

docker-pull:
	docker pull $(DOCKER_IMAGE)

docker-test:
	docker run --rm -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR)  $(DOCKER_IMAGE)

docker-all: docker-clean docker-pull docker-test docker-enter

docker-enter:
	docker run --rm -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR) -it --entrypoint="bash" $(DOCKER_IMAGE)

trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)

release-%:
	git flow init -d
	@grep -q '\[Unreleased\]' README.md || (echo 'Create the [Unreleased] section in the changelog first!' && exit)
	bumpversion --verbose --commit $*
	git flow release start $(VERSION)
	GIT_MERGE_AUTOEDIT=no git flow release finish -m "Merge branch release/$(VERSION)" -T $(VERSION) $(VERSION) -p
