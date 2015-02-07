#!/usr/bin/env python
from __future__ import division, print_function
import subprocess
import argparse
# import os
# pjoin = os.path.join
# this_dir = os.path.dirname(os.path.realpath(__file__))

import numpy as np
import pandas


def enumerate_bins_gz(reader, edge_pairs):
    # yield submatrix corresponding to each bin pair
    for i, (i1, i2) in enumerate(edge_pairs):
        chunk = reader.read(i2-i1)
        for j, (j1, j2) in enumerate(edge_pairs):
            yield (i,j), chunk.iloc[:, j1:j2].values


def from_gz(ldfile, countsfile, binsize, out, fmt='f8', thresh=0.1, percentile=90):
    df = pandas.read_csv(countsfile, sep='\t')
    n_bins = len(df)
    kb_binsize= binsize/1000
    starts, stops, counts = df['start'].values, df['stop'].values, df['count'].values
    total_snps = stops[-1]

    # load the binary ld matrix
    reader = pandas.read_csv(ldfile, sep='\t', compression='gzip', header=None, iterator=True)
    iter_bins = enumerate_bins_gz(reader, zip(starts, stops))

    print()
    print("Aggregating the pairwise r2 data...")
    R2mean = np.zeros((n_bins, n_bins), dtype=fmt)
    R2medi = np.zeros((n_bins, n_bins), dtype=fmt)
    R2freq = np.zeros((n_bins, n_bins), dtype=fmt)
    R2perc = np.zeros((n_bins, n_bins), dtype=fmt)
    for (i, j), x in iter_bins:
        y = x[np.isfinite(x)]
        print(i,j, x.shape, y.shape)
        R2mean[i,j] = np.mean(y)
        R2medi[i,j] = np.median(y)
        R2freq[i,j] = np.sum(y >= thresh)/counts[i]/counts[j]
        R2perc[i,j] = np.percentile(y, q=percentile)


    print()
    print("Writing result matrices [*.txt.gz]...")
    outbase = out+'-ldmatrix-{0:.3g}kb'.format(kb_binsize)
    np.savetxt(outbase+'-mean.txt.gz', R2mean)
    np.savetxt(outbase+'-median.txt.gz', R2medi)
    np.savetxt(outbase+'-freq-t{:.3g}.txt.gz'.format(thresh), R2freq)
    np.savetxt(outbase+'-perc-q{:.3g}.txt.gz'.format(percentile), R2perc)



def enumerate_bins(mmap, edge_pairs):
    # yield submatrix corresponding to each bin pair
    for i, (i1, i2) in enumerate(edge_pairs):
        for j, (j1, j2) in enumerate(edge_pairs):
            yield (i,j), mmap[i1:i2, j1:j2]

def from_binary(ldfile, countsfile, binsize, out, fmt='f8', thresh=0.1, percentile=90):
    df = pandas.read_csv(countsfile, sep='\t')
    n_bins = len(df)
    kb_binsize= binsize/1000
    starts, stops, counts = df['start'].values, df['stop'].values, df['count'].values
    total_snps = stops[-1]

    # load the binary ld matrix
    mmap = np.memmap(ldfile, dtype=fmt)
    mmap.resize(total_snps, total_snps)
    iter_bins = enumerate_bins(mmap, zip(starts, stops))

    print()
    print("Aggregating and reducing the pairwise r2 data...")
    R2mean = np.zeros((n_bins, n_bins), dtype=fmt)
    R2medi = np.zeros((n_bins, n_bins), dtype=fmt)
    R2freq = np.zeros((n_bins, n_bins), dtype=fmt)
    R2perc = np.zeros((n_bins, n_bins), dtype=fmt)
    for (i, j), x in iter_bins:
        y = x[np.isfinite(x)]
        R2mean[i,j] = np.mean(y)
        R2medi[i,j] = np.median(y)
        R2freq[i,j] = np.sum(y >= thresh)/counts[i]/counts[j]
        R2perc[i,j] = np.percentile(y, q=percentile)


    print()
    print("Writing result matrices [*.txt.gz]...")
    outbase = out+'-ldmatrix-{0:.3g}kb'.format(kb_binsize)
    np.savetxt(outbase+'-mean.txt.gz', R2mean)
    np.savetxt(outbase+'-median.txt.gz', R2medi)
    np.savetxt(outbase+'-freq-t{:.3g}.txt.gz'.format(thresh), R2freq)
    np.savetxt(outbase+'-perc-q{:.3g}.txt.gz'.format(percentile), R2perc)



def main(**kwargs):
    if kwargs.pop('gz', False):
        from_gz(**kwargs)
    else:
        from_binary(**kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ldfile", type=str)
    parser.add_argument("countsfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("fmt", type=str)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--gz", action='store_true')
    parser.add_argument("--thresh", type=int, default=0.1)
    parser.add_argument("--percentile", type=float, default=90)
    args = parser.parse_args()
    main(**vars(args))
