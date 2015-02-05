export BINDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))bin

.PHONY: install clean html

plink:
	wget -O $(BINDIR)/plink.zip https://www.cog-genomics.org/static/bin/plink150203/plink_linux_x86_64.zip; \
	unzip $(BINDIR)/plink.zip plink prettify -d $(BINDIR); \
	rm $(BINDIR)/plink.zip

vcftools: 
	wget -O $(BINDIR)/vcftools.tar.gz 'http://sourceforge.net/projects/vcftools/files/vcftools_0.1.12b.tar.gz'; \
	tar -xvf $(BINDIR)/vcftools.tar.gz -C $(BINDIR); \
	$(MAKE) -C $(BINDIR)/vcftools_0.1.12b/cpp; \
	rm $(BINDIR)/vcftools.tar.gz
	#mv $(BINDIR)/vcftools_0.1.12b/bin/* $(BINDIR); \
	#rm -r $(BINDIR)/vcftools_0.1.12b

install: plink vcftools

clean:
	rm -r $(BINDIR)/*

html:
	ipython nbconvert --to html *.ipynb
	mv *.html html
