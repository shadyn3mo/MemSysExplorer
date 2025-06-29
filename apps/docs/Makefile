SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

apidoc:
	@echo "Generating API documentation using sphinx-apidoc..."
	#sphinx-apidoc -o source/package ../../apps --force --no-toc

.PHONY: help Makefile apidoc

%: Makefile
	@$(MAKE) apidoc
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

