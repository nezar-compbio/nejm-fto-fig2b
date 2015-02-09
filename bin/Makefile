BINDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

all: plink-1.9 plink-1.07 vcftools tabix

clean:
	-$(RM) plink plink2 prettify vcftools tabix

# === Required binaries ===
plink-1.07:
	wget -O $(BINDIR)plink.zip "http://pngu.mgh.harvard.edu/~purcell/plink/dist/plink-1.07-x86_64.zip"; \
	unzip $(BINDIR)plink.zip plink-1.07-x86_64/plink -d $(BINDIR) && rm $(BINDIR)plink.zip; \
	mv $(BINDIR)plink-1.07-x86_64/plink $(BINDIR)plink && rmdir $(BINDIR)plink-1.07-x86_64

plink-1.9:
	wget -O $(BINDIR)plink.zip "https://www.cog-genomics.org/static/bin/plink150206/plink_linux_x86_64.zip"; \
	unzip $(BINDIR)plink.zip plink prettify -d $(BINDIR) && rm $(BINDIR)plink.zip; \
	mv $(BINDIR)plink $(BINDIR)plink2

vcftools: 
	wget -O $(BINDIR)vcftools.tar.gz "http://sourceforge.net/projects/vcftools/files/vcftools_0.1.12b.tar.gz"; \
	tar -xvf $(BINDIR)vcftools.tar.gz -C $(BINDIR) && rm $(BINDIR)vcftools.tar.gz; \
	$(MAKE) -C $(BINDIR)vcftools_0.1.12b/cpp; \
	mv $(BINDIR)vcftools_0.1.12b/cpp/vcftools $(BINDIR)vcftools && rm -r $(BINDIR)vcftools_0.1.12b

tabix:
	wget -O $(BINDIR)htslib.tar.bz2 "https://github.com/samtools/htslib/releases/download/1.2.1/htslib-1.2.1.tar.bz2"; \
	tar -xvf $(BINDIR)htslib.tar.bz2 -C $(BINDIR); \
	cd $(BINDIR)htslib-1.2.1 && $(MAKE) lib-static lib-shared tabix; \
	cp $(BINDIR)htslib-1.2.1/tabix $(BINDIR); \
	cd $(BINDIR) && rm -r $(BINDIR)htslib-1.2.1 && rm $(BINDIR)htslib.tar.bz2
