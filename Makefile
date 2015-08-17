# === Parameters ===

# Data source
# -----------
# 1KG Phase 1
URL = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20110521/ALL.chr16.phase1_release_v3.20101123.snps_indels_svs.genotypes.vcf.gz"

# 1KG Phase 3
#URL = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/ALL.chr16.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
# -----------

# Region
START = 52800000
STOP  = 56000000
INPUTNAME = chr16.$(START)-$(STOP)

# Size of bins to aggregate (bp)
#BINSIZE = 40000
#HICFILE = "Jin2013-IMR90.chr16_40kb_FTO.ICEobserved.npy"
BINSIZE = 5000
HICFILE = "Rao2014-IMR90.MAPQG0.chr16_5kb_FTO.ICEobserved.npy"


# Floating point format or gz: bin, bin4, gz
FMT = bin4
# ==========

THISDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
BINDIR = $(THISDIR)bin/
TASKDIR = $(THISDIR)tasks/
DATADIR = $(THISDIR)data/
DATADIR1 = $(THISDIR)data/01-variants/
DATADIR2 = $(THISDIR)data/02-ld-r2/
DATADIR3 = $(THISDIR)data/03-ld-aggregate/
DATADIR4 = $(THISDIR)data/04-hic/
PUBDIR = $(THISDIR)output/


all: install-tools init fetch-vcf project

project: ld-r2 ld-aggregate figure

ld-r2: convert-to-map-ped ld-matrix-plink2

ld-aggregate: index ld-aggregate-binary



# === Required binaries ===
install-tools:
	$(MAKE) -C $(BINDIR)

clean-tools:
	$(MAKE) -C $(BINDIR) clean



# === Analysis pipeline ===
init:
	mkdir -p $(DATADIR1) $(DATADIR2) $(DATADIR3) $(PUBDIR)

clean:
	-$(RM) $(DATADIR1) $(DATADIR2) $(DATADIR3)

clean-output:
	-$(RM) $(DATADIR2)* $(DATADIR3)*

fetch-vcf:
	cd $(DATADIR1); \
	$(BINDIR)tabix -h $(URL) 16:$(START)-$(STOP) | gzip -c > $(DATADIR1)$(INPUTNAME).vcf.gz

# Converting directly with vcftools did not work. Using "tped" as intermediate.
convert-to-map-ped: $(DATADIR1)$(INPUTNAME).vcf.gz
	$(BINDIR)vcftools --gzvcf $(DATADIR1)$(INPUTNAME).vcf.gz --chr 16 --from-bp $(START) --to-bp $(STOP) --plink-tped --out $(DATADIR2)$(INPUTNAME); \
	$(BINDIR)plink --noweb --tfile $(DATADIR2)$(INPUTNAME) --recode --out $(DATADIR2)$(INPUTNAME)

# BUG in plink-1.9 FIXED: https://github.com/nezar-compbio/plink2-bug
ld-matrix-plink2: $(DATADIR2)$(INPUTNAME).map $(DATADIR2)$(INPUTNAME).ped
	$(BINDIR)plink2 --file $(DATADIR2)$(INPUTNAME) --r2 square $(FMT) --out $(DATADIR2)$(INPUTNAME)

index: $(DATADIR2)$(INPUTNAME).map
	python $(TASKDIR)index_mapfile.py $(DATADIR2)$(INPUTNAME).map $(START) $(STOP) $(BINSIZE) --out $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index

ld-aggregate-binary: $(DATADIR2)$(INPUTNAME).ld.bin $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index
	python $(TASKDIR)aggregate_ldr2.py $(DATADIR2)$(INPUTNAME).ld.bin $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index $(BINSIZE) --fmt $(FMT) --out $(DATADIR3)$(INPUTNAME)

ld-aggregate-gz: $(DATADIR2)$(INPUTNAME).ld.gz $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index
	python $(TASKDIR)aggregate_ldr2.py $(DATADIR2)$(INPUTNAME).ld.gz $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index $(BINSIZE) --fmt $(FMT) --out $(DATADIR3)$(INPUTNAME)




# === Publish ===
image: $(DATADIR3)$(INPUTNAME).ld.$(BINSIZE).mean.txt.gz
	python $(TASKDIR)figure_ldr2_only.py $(DATADIR3)$(INPUTNAME).ld.$(BINSIZE).mean.txt.gz $(BINSIZE) --fmt $(FMT) --out $(PUBDIR)ldmatrix

figure: $(DATADIR3)$(INPUTNAME).ld.$(BINSIZE).mean.txt.gz
	python $(TASKDIR)figure.py $(DATADIR4)$(HICFILE) $(DATADIR3)$(INPUTNAME).ld.$(BINSIZE).mean.txt.gz $(BINSIZE) --out $(PUBDIR)$(INPUTNAME).ld.$(BINSIZE).mean

notebook-html:
	ipython nbconvert --to=html --output $(PUBDIR)figure notebook/figure.ipynb

# run-notebook:
# 	mkdir -p publish/img; \
# 	ipython nbconvert --to=notebook --ExecutePreprocessor.enabled=True notebook/figure.ipynb




# === Stable PLINK version (SLOW!) ===
# plink-1.07
ld-matrix-plink1: $(DATADIR2)$(INPUTNAME).map $(DATADIR2)$(INPUTNAME).ped
	$(BINDIR)plink --file $(DATADIR2)$(INPUTNAME) --r2 --matrix --out $(DATADIR2)$(INPUTNAME)

ld-aggregate-plink1: $(DATADIR2)$(INPUTNAME).ld $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index
	python $(TASKDIR)aggregate_ldr2.py $(DATADIR2)$(INPUTNAME).ld $(DATADIR2)$(INPUTNAME).$(BINSIZE).binned.index $(BINSIZE) --fmt plink1 --out $(DATADIR3)$(INPUTNAME)