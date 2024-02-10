# Makefile for converting tex to pdf

INPUTS = $(wildcard *Plan.tex) PlanMaster.tex InstallingBasicChecker.tex
OUTPUTS = $(patsubst %.tex,%.pdf,$(INPUTS))

# Bring all PDFs up to date
.PHONY: all
all: $(OUTPUTS)

.PHONY: clean
clean:
	-rm -f *.aux
	-rm -f *.log
	-rm -f *.toc
	-rm -f *.bbl
	-rm -f *.blg
	-rm -f *.out

%.pdf : %.tex includeHeader.tex
	pdflatex $<  

	