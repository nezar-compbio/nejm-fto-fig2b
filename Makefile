# Params
URL = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20110521/ALL.chr16.phase1_release_v3.20101123.snps_indels_svs.genotypes.vcf.gz"
START = 52800000
STOP = 56000000
BINSIZE = 10000
INPUTNAME = ALL-chr16-section
#INPUTNAME = 16.52800000-56000000.ALL.chr16.phase1_release_v3.20101123.snps_indels_svs.genotypes
#INPUTNAME = 16.52800000-56000000.ALL.chr16.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes
FMT = f4

THISDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
export BINDIR = $(THISDIR)bin/
export DATADIR = $(THISDIR)data/


.PHONY: all clean html


# === Required binaries ===
tabix:
	wget -O $(BINDIR)htslib.tar.bz2 "https://github.com/samtools/htslib/releases/download/1.2.1/htslib-1.2.1.tar.bz2"; \
	tar -xvf $(BINDIR)htslib.tar.bz2 -C $(BINDIR); \
	cd $(BINDIR)htslib-1.2.1 && $(MAKE) lib-static lib-shared tabix; \
	cp $(BINDIR)htslib-1.2.1/tabix $(BINDIR); \
	cd $(BINDIR) && rm -r $(BINDIR)htslib-1.2.1 && rm $(BINDIR)htslib-1.2.1.tar.bz2

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


# === Publish ===
html:
	ipython nbconvert --to html notebooks/*.ipynb; \
	mv *.html notebooks/html


# === Analysis pipeline ===
all: convert-to-plink bin-and-count-snps ld-matrix

clean:
	-$(RM) $(DATADIR)02-ld-r2/* $(DATADIR)03-ld-aggregate/*

fetch-variants:
	cd $(DATADIR)01-variants; \
	$(BINDIR)tabix -h $(URL) 16:$(START)-$(STOP) | gzip -c > $(DATADIR)01-variants/$(INPUTNAME).vcf.gz

convert-to-plink: $(DATADIR)01-variants/$(INPUTNAME).vcf.gz
	$(BINDIR)vcftools --gzvcf $(DATADIR)01-variants/$(INPUTNAME).vcf.gz --chr 16 --from-bp $(START) --to-bp $(STOP) --plink-tped --out $(DATADIR)02-ld-r2/$(INPUTNAME); \
	$(BINDIR)plink --tfile $(DATADIR)02-ld-r2/$(INPUTNAME) --recode --out $(DATADIR)02-ld-r2/$(INPUTNAME)

bin-and-count-snps: $(DATADIR)02-ld-r2/$(INPUTNAME).map
	python varcount.py $(DATADIR)02-ld-r2/$(INPUTNAME).map $(START) $(STOP) $(BINSIZE) --out $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt

ld-matrix: $(DATADIR)02-ld-r2/$(INPUTNAME).tped
	$(BINDIR)plink2 --file $(DATADIR)02-ld-r2/$(INPUTNAME) --r2 square bin4 --out $(DATADIR)02-ld-r2/$(INPUTNAME)

reduce-ld-matrix: $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt
	python reduceld.py $(DATADIR)02-ld-r2/$(INPUTNAME).ld.bin $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt $(BINSIZE) $(FMT) --out $(DATADIR)03-ld-aggregate/$(INPUTNAME)



# Other attempts
# ld-matrix-plink1:
# 	$(BINDIR)plink --file $(DATADIR)02-ld-r2/$(INPUTNAME) --r2 --matrix --out $(DATADIR)02-ld-r2/$(INPUTNAME)
# 	#plink --file mydata --r2 --ld-window-kb 500000

# ld-matrix-gz: $(DATADIR)02-ld-r2/$(INPUTNAME).tped
# 	$(BINDIR)plink2 --tfile $(DATADIR)02-ld-r2/$(INPUTNAME) --r2 square gz --out $(DATADIR)02-ld-r2/$(INPUTNAME)

# reduce-ld-matrix-gz: $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt
# 	python reduceld.py $(DATADIR)02-ld-r2/$(INPUTNAME).ld.gz $(DATADIR)02-ld-r2/$(INPUTNAME).binned.txt $(BINSIZE) --gz --out $(DATADIR)03-ld-aggregate/$(INPUTNAME)
