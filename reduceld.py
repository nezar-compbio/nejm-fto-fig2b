#!/usr/bin/env python
from __future__ import division, print_function
import argparse

import numpy as np
import pandas


def aggregate(n_bins, iterator, counts, binsize, out, fmt, thresh=0.1, percentile=90):
    kb_binsize = binsize//1000

    print()
    print("Aggregating the pairwise r2 data...")
    R2mean = np.zeros((n_bins, n_bins), dtype=fmt)
    R2medi = np.zeros((n_bins, n_bins), dtype=fmt)
    R2freq = np.zeros((n_bins, n_bins), dtype=fmt)
    R2perc = np.zeros((n_bins, n_bins), dtype=fmt)
    for (i, j), x in iterator:
        print(i,j)
        y = x[np.isfinite(x)]
        R2mean[i,j] = np.mean(y)
        R2medi[i,j] = np.median(y)
        R2freq[i,j] = np.sum(y >= thresh)/counts[i]/counts[j]
        R2perc[i,j] = np.percentile(y, q=percentile)


    print()
    print("Writing result matrices [*.txt.gz]...")
    outbase = out+'.ld.{0:.3g}kb'.format(kb_binsize)
    np.savetxt(outbase+'.mean.txt.gz', R2mean)
    np.savetxt(outbase+'.median.txt.gz', R2medi)
    np.savetxt(outbase+'.freq{:.3g}.txt.gz'.format(thresh), R2freq)
    np.savetxt(outbase+'.perc{:.3g}.txt.gz'.format(percentile), R2perc)    


# yield submatrix corresponding to each bin pair
def enumerate_bins_gz(reader, edge_pairs):
    for i, (i1, i2) in enumerate(edge_pairs):
        chunk = reader.read(i2-i1)
        for j, (j1, j2) in enumerate(edge_pairs):
            yield (i,j), chunk.iloc[:, j1:j2].values


def enumerate_bins_mmap(mmap, edge_pairs):
    for i, (i1, i2) in enumerate(edge_pairs):
        for j, (j1, j2) in enumerate(edge_pairs):
            yield (i,j), mmap[i1:i2, j1:j2]


def main(**kwargs):
    df = pandas.read_csv(kwargs.pop('indexfile'), sep='\t')
    starts, stops, counts = df['start'].values, df['stop'].values, df['count'].values
    n_bins = len(df)

    # create a bin-wise chunk iterator over the LD matrix
    if kwargs.pop('gz', False):
        reader = pandas.read_csv(kwargs.pop('ldfile'), sep='\t', compression='gzip', header=None, iterator=True)
        iterator = enumerate_bins_gz(reader, zip(starts, stops))
    elif kwargs.pop('txt', False):
        reader = pandas.read_csv(kwargs.pop('ldfile'), sep='\t', header=None, iterator=True)
        iterator = enumerate_bins_gz(reader, zip(starts, stops))
    else:
        total_snps = stops[-1]
        mmap = np.memmap(kwargs.pop('ldfile'), dtype=kwargs['fmt'])
        mmap.resize(total_snps, total_snps)
        iterator = enumerate_bins_mmap(mmap, zip(starts, stops))

    # aggregate chunks
    aggregate(n_bins, iterator, counts, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ldfile", type=str)
    parser.add_argument("indexfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("fmt", type=str)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--txt", action='store_true')
    parser.add_argument("--gz", action='store_true')
    parser.add_argument("--thresh", type=int, default=0.1)
    parser.add_argument("--percentile", type=float, default=90)
    args = parser.parse_args()
    main(**vars(args))
