from __future__ import division, print_function
import argparse

import numpy as np
import pandas


def aggregate(n_bins, iterator, counts, binsize, dtype, out, thresh, percentile):
    print()
    print("Aggregating the pairwise r2 data at {} kb...".format(binsize//1000))
    R2mean = np.zeros((n_bins, n_bins), dtype=dtype)
    R2medi = np.zeros((n_bins, n_bins), dtype=dtype)
    R2freq = np.zeros((n_bins, n_bins), dtype=dtype)
    R2perc = np.zeros((n_bins, n_bins), dtype=dtype)
    for (i, j), x in iterator:
        y = x[-np.isnan(x)]
        R2mean[i, j] = np.mean(y)
        R2medi[i, j] = np.median(y)
        R2freq[i, j] = np.sum(y >= thresh)/counts[i]/counts[j]
        R2perc[i, j] = np.percentile(y, q=percentile)


    print()
    print("Writing result matrices...")
    outbase = out+'.ld.{}'.format(binsize)
    np.savetxt(outbase+'.mean.txt.gz', R2mean)
    np.savetxt(outbase+'.median.txt.gz', R2medi)
    np.savetxt(outbase+'.freq{:.3g}.txt.gz'.format(thresh), R2freq)
    np.savetxt(outbase+'.perc{:.3g}.txt.gz'.format(percentile), R2perc)    


def enumerate_bins_debug(edge_pairs):
    for i, (i1, i2) in enumerate(edge_pairs):
        if (i2 - i1) > 0:
            print(i, i1, i2)

def enumerate_bins_text(reader, edge_pairs):
    for i, (i1, i2) in enumerate(edge_pairs):
        if (i2 - i1) > 0:
            chunk = reader.read(i2-i1)
            for j, (j1, j2) in enumerate(edge_pairs):
                if (j2 - j1) > 0:
                    yield (i, j), chunk.iloc[:, j1:j2].values


def enumerate_bins_mmap(mmap, edge_pairs):
    for i, (i1, i2) in enumerate(edge_pairs):
        for j, (j1, j2) in enumerate(edge_pairs):
            yield (i, j), mmap[i1:i2, j1:j2]


def main(**kwargs):
    df = pandas.read_csv(kwargs.pop('indexfile'), delimiter='\t', header=0)
    starts, stops, counts = df['start'].values, df['stop'].values, df['count'].values
    n_bins = len(df)
    n_variants = stops[-1]

    
    format = kwargs.pop('fmt')
    kwargs['dtype'] = np.float64 if format == 'bin' else np.float32

    if format == 'plink1': 
        reader = pandas.read_csv(kwargs.pop('ldfile'), delimiter=' ', header=None, iterator=True)
        iterator = enumerate_bins_text(reader, zip(starts, stops))
    elif format == 'gz':
        reader = pandas.read_csv(kwargs.pop('ldfile'), delimiter='\t',  header=None, iterator=True, compression='gzip')
        iterator = enumerate_bins_text(reader, zip(starts, stops)) 
    else:
        mmap = np.memmap(kwargs.pop('ldfile'), dtype=kwargs['dtype'])
        mmap.resize(n_variants, n_variants)
        iterator = enumerate_bins_mmap(mmap, zip(starts, stops))

    aggregate(n_bins, iterator, counts, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ldfile", type=str)
    parser.add_argument("indexfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--fmt", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)

    parser.add_argument("--thresh", type=int, default=0.1)
    parser.add_argument("--percentile", type=float, default=90)
    args = parser.parse_args()
    main(**vars(args))
