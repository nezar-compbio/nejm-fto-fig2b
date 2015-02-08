#!/usr/bin/env python
from __future__ import division, print_function
import argparse

import numpy as np
import pandas


def main(mapfile, out, start, stop, binsize):
    # read in map file of snp locations
    snps = pandas.read_csv(
        mapfile,
        header=None, 
        names=['chrom', 'id', '_', 'POS'],
        delimiter='\t')

    # the rows are snps sorted by bp position
    # group them into genomic bins of equal width
    interval_map = pandas.cut(
        snps['POS'], 
        range(start, stop+binsize, binsize)
    )
    gby = snps.groupby(interval_map)
    snpcounts = [len(gby.get_group(interval)) for interval in sorted(gby.groups.keys())]
    edges = np.r_[0, np.cumsum(snpcounts)]

    # write out tsv file of bins
    df = pandas.DataFrame(
        {'start':edges[:-1], 'stop':edges[1:], 'count':snpcounts},
        columns=['start','stop','count'])
    df.to_csv(out, sep='\t', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mapfile", type=str)
    parser.add_argument("start", type=int)
    parser.add_argument("stop", type=int)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    main(**vars(args))
