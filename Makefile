# Parameters
# ==========

# Data source
# 1KG Phase 1
URL = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20110521/ALL.chr16.phase1_release_v3.20101123.snps_indels_svs.genotypes.vcf.gz"
# 1KG Phase 3
#URL = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/ALL.chr16.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"

# Region
START = 52800000
STOP  = 56000000
INPUTNAME = chr16-$(START)-$(STOP)

# Size of bins to aggregate (bp)
BINSIZE = 10000

# Floating point format: f4, f8
FMT = f4
ifeq ($(FMT),f4)
  BINPARAM = bin4
else
  BINPARAM = bin
endif
# ==========

THISDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
export BINDIR = $(THISDIR)bin/
export DATADIR = $(THISDIR)data/

.PHONY: all clean html

all: project

# === Required binaries ===
tabix:
	wget -O $(BINDIR)htslib.tar.bz2 "https://github.com/samtools/htslib/releases/download/1.2.1/htslib-1.2.1.tar.bz2"; \
	tar -xvf $(BINDIR)htslib.tar.bz2 -C $(BINDIR); \
	cd $(BINDIR)htslib-1.2.1 && $(MAKE) lib-static lib-shared tabix; \
	cp $(BINDIR)htslib-1.2.1/tabix $(BINDIR); \
	cd $(BINDIR) && rm -r $(BINDIR)htslib-1.2.1 && rm $(BINDIR)htslib.tar.bz2

plink-1.07:
	wget -O $(BINDIR)plink.zip "http://pngu.mgh.harvard.edu/~purcell/plink/dist/plink-1.07-x86_64.zip"; \
	unzip $(BINDIR)plink.zip plink-1.07-x86_64/plink -d $(BINDIR); \
	mv $(BINDIR)plink-1.07-x86_64/plink $(BINDIR)plink; \
	rmdir $(BINDIR)plink-1.07-x86_64; \
	rm $(BINDIR)plink.zip

plink-1.9:
	wget -O $(BINDIR)plink.zip "https://www.cog-genomics.org/static/bin/plink150206/plink_linux_x86_64.zip"; \
	unzip $(BINDIR)plink.zip plink prettify -d $(BINDIR); \
	mv $(BINDIR)plink $(BINDIR)plink2; \
	rm $(BINDIR)plink.zip

vcftools: 
	wget -O $(BINDIR)vcftools.tar.gz "http://sourceforge.net/projects/vcftools/files/vcftools_0.1.12b.tar.gz"; \
	tar -xvf $(BINDIR)vcftools.tar.gz -C $(BINDIR); \
	rm $(BINDIR)vcftools.tar.gz; \
	$(MAKE) -C $(BINDIR)vcftools_0.1.12b/cpp; \
	rm -r $(BINDIR)vcftools_0.1.12b

install-tools: plink-1.9 plink-1.07 vcftools tabix

clean-tools:
	rm $(BINDIR)plink; \
	rm $(BINDIR)plink2; \
	rm $(BINDIR)prettify; \
	rm $(BINDIR)vcftools


# === Analysis pipeline ===
project: init fetch-variants convert-to-map-ped bin-variants ld-matrix reduce-ld-matrix

init:
	mkdir -p $(DATADIR)01-variants $(DATADIR)02-ld-r2 $(DATADIR)03-ld-aggregate

clean:
	-$(RM) $(DATADIR)02-ld-r2/* $(DATADIR)03-ld-aggregate/*

fetch-variants:
	cd $(DATADIR)01-variants; \
	$(BINDIR)tabix -h $(URL) 16:$(START)-$(STOP) | gzip -c > $(DATADIR)01-variants/$(INPUTNAME).vcf.gz

# Converting directly with vcftools did not work. Using "tped" as intermediate.
convert-to-map-ped: $(DATADIR)01-variants/$(INPUTNAME).vcf.gz
	$(BINDIR)vcftools --gzvcf $(DATADIR)01-variants/$(INPUTNAME).vcf.gz --chr 16 --from-bp $(START) --to-bp $(STOP) --plink-tped --out $(DATADIR)02-ld-r2/$(INPUTNAME); \
	$(BINDIR)plink --tfile $(DATADIR)02-ld-r2/$(INPUTNAME) --recode --out $(DATADIR)02-ld-r2/$(INPUTNAME)

bin-variants: $(DATADIR)02-ld-r2/$(INPUTNAME).map
	python varcount.py $(DATADIR)02-ld-r2/$(INPUTNAME).map $(START) $(STOP) $(BINSIZE) --out $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index

# BUG in plink-1.9!
ld-matrix: $(DATADIR)02-ld-r2/$(INPUTNAME).tped
	$(BINDIR)plink2 --file $(DATADIR)02-ld-r2/$(INPUTNAME) --r2 square $(BINPARAM) --out $(DATADIR)02-ld-r2/$(INPUTNAME)

reduce-ld-matrix: $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index
	python reduceld.py $(DATADIR)02-ld-r2/$(INPUTNAME).ld.bin $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index $(BINSIZE) $(FMT) --out $(DATADIR)03-ld-aggregate/$(INPUTNAME)




# === Other attempts... ===
# plink-1.09
ld-matrix-plink1:
	$(BINDIR)plink --file $(DATADIR)02-ld-r2/$(INPUTNAME) --r2 --matrix --out $(DATADIR)02-ld-r2/$(INPUTNAME)

reduce-ld-matrix-gz: $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index
	python reduceld.py $(DATADIR)02-ld-r2/$(INPUTNAME).ld.gz $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index $(BINSIZE) $(FMT) --gz --out $(DATADIR)03-ld-aggregate/$(INPUTNAME)

reduce-ld-matrix-txt: $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index
	python reduceld.py $(DATADIR)02-ld-r2/$(INPUTNAME).ld $(DATADIR)02-ld-r2/$(INPUTNAME).binned.index $(BINSIZE) $(FMT) --txt --out $(DATADIR)03-ld-aggregate/$(INPUTNAME)




# === Publish ===
html:
	ipython nbconvert --to html notebooks/*.ipynb; \
	mv *.html notebooks/html
