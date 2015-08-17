from __future__ import division, print_function
import argparse

import numpy as np
import pandas


def main(mapfile, out, start, stop, binsize):
    # map file contains variants sorted by bp position
    variants = pandas.read_csv(
        mapfile,
        header=None, 
        names=['chrom', 'id', '_', 'POS'],
        delimiter='\t')

    # group them into genomic bins of equal width
    spans = pandas.cut(
        variants['POS'], 
        np.arange(start, stop+binsize, binsize)
    )
    gby = variants.groupby(spans)
    counts = gby.size().sort_index().values
    counts[np.isnan(counts)] = 0
    counts = counts.astype(int)
    edges = np.r_[0, np.cumsum(counts)]

    # write out tsv index file of bin edges and counts
    df = pandas.DataFrame(
        {'start':edges[:-1], 
         'stop':edges[1:], 
         'count':counts},
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
