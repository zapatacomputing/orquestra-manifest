default: list

# define install_repo
#     @echo Checking out $(1)
#     @git clone -q $(1) 2> /dev/null && echo cloning || { echo "$(1) already exists"; }
#     cd $(shell echo $(1) | sed -n -e 's/^.*\/\([^.]*\)\(.git\)*/\1/p') \
#        && git checkout $(2) \
#        && git status
# endef
# 
# define update_repo
#     @echo Checking out $(1)
#     @git clone -q $(1) 2> /dev/null && echo cloning || { echo "$(1) already exists"; }
#     cd $(shell echo $(1) | sed -n -e 's/^.*\/\([^.]*\)\(.git\)*/\1/p') \
#        && git checkout $(2) \
#        && git pull
# endef


# Clean out all Pythonic cruft
clean:
	@find . -regex '^.*\(__pycache__\|\.py[co]\)$$' -delete;
	@find . -type d -name __pycache__ -exec rm -r {} \+
	@find . -type d -name '*.egg-info' -exec rm -rf {} +
	@find . -type d -name .mypy_cache -exec rm -r {} \+
	@rm -rf .pytest_cache;
	@rm -rf tests/.pytest_cache;
	@rm -rf dist build
	@rm -f .coverage*
	@echo Finished cleaning out pythonic cruft...

install:
	@echo Installing package
	pip install .

init:
	@echo Initializing repos
	morq init

update:
	@echo Update all repos
	morq update

list:
	@echo Listing all repos
	@morq list

list_installed:
	@echo Listing all repos
	@morq list -i

check:
	@echo Check all repos for valid versions
	morq check

# SubRepos should all have a docs/ folder which we use implicitly
# For project that support auto-doc (like Python), Sphinx should run autodocs on it
docs:
	# Spawn master build on docs
	@echo building docs
	morq docs

build:
	@echo Build the entire project
	@echo Not sure how to do it yet
	@echo Each project should provide its own "make build" command independently.
	@echo * Try not to build the same project twice: IE: do we build a dependency tree?


test:
	pytest tests
