export BINDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))bin

.PHONY: install clean html

ld_r2:
	wget -O $(BINDIR)/ld_r2.py "https://bitbucket.org/nvictus/ldmatrix/raw/1915baf0085777f3390a6167e76dc38982928db2/ld_r2.py"; \
	chmod 755 $(BINDIR)/ld_r2.py

plink:
	wget -O $(BINDIR)/plink.zip "https://www.cog-genomics.org/static/bin/plink150203/plink_linux_x86_64.zip"; \
	unzip $(BINDIR)/plink.zip plink prettify -d $(BINDIR); \
	rm $(BINDIR)/plink.zip

vcftools: 
	wget -O $(BINDIR)/vcftools.tar.gz "http://sourceforge.net/projects/vcftools/files/vcftools_0.1.12b.tar.gz"; \
	tar -xvf $(BINDIR)/vcftools.tar.gz -C $(BINDIR); \
	rm $(BINDIR)/vcftools.tar.gz; \
	$(MAKE) -C $(BINDIR)/vcftools_0.1.12b/cpp; \
	rm -r $(BINDIR)/vcftools_0.1.12b

install: plink vcftools ld_r2

clean:
	rm $(BINDIR)/plink; \
	rm $(BINDIR)/prettify; \
	rm $(BINDIR)/vcftools; \
	rm $(BINDIR)/ld_r2.py

html:
	ipython nbconvert --to html notebooks/*.ipynb
	mv *.html notebooks/html
