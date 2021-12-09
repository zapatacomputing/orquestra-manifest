default: target

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


.PHONY: target
init:
	@echo Initializing repos
	orqm init

update:
	@echo Update all repos
	orqm update

list:
	@echo Listing all repos
	orqm list

check:
	@echo Check all repos for valid versions
	orqm check

# SubRepos should all have a docs/ folder which we use implicitly
# For project that support auto-doc (like Python), Sphinx should run autodocs on it
docs:
	# Spawn master build on docs
	@echo building docs
	orqm docs

build:
	@echo Build the entire project
	@echo Not sure how to do it yet
	@echo Each project should provide its own "make build" command independently.
	@echo * Try not to build the same project twice: IE: do we build a dependency tree?


