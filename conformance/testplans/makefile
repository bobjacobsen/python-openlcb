# Makefile for converting tex to pdf

INPUTS = $(wildcard *.tex)
OUTPUTS = $(patsubst %.tex,%.pdf,$(INPUTS))

# Bring all PDFs up to date
.PHONY: all
all: $(OUTPUTS)

# Force Latex to run again to ger cross-references right
.PHONY: rerun
rerun: cleanpdf all

.PHONY: clean
clean:
	-rm -f *.aux
	-rm -f *.log
	-rm -f *.toc
	-rm -f *.bbl
	-rm -f *.blg
	-rm -f *.out

cleanpdf:
	-rm -f *.pdf
	
%.pdf : %.tex
	pdflatex $<  

	