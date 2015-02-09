"""
Data source (Rao et al, 2014):
    ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE63nnn/GSE63525/suppl/GSE63525%5FIMR90%5Fcontact%5Fmatrices%2Etar%2Egz    

"""
from __future__ import division
import argparse
import numpy as np
import os
pjoin = os.path.join

from mirnylib.numutils import completeIC


def process_chr16(binsize):
    chr16_length = 90354753
    n_bins = int(np.ceil(chr16_length/binsize))

    # IMR90/5kb_resolution_intrachromosomal/chr16/MAPQG0/chr16_5kb.RAWobserved
    # IMR90/5kb_resolution_intrachromosomal/chr16/MAPQG30/chr16_5kb.RAWobserved
    triples = np.genfromtxt(hicfile+'.RAWobserved')
    nnz = triples.shape[0]

    A = np.zeros((n_bins, n_bins))
    for x, y, val in triples:
        i, j = x//binsize, y//binsize
        A[i, j] = A[j, i] = val

    Ac, bias = completeIC(A, returnBias=True)
    np.save(out+'.RAWobserved.npy', A)
    np.save(out+'.ICEobserved.npy', Ac)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("hicfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    main(**vars(args))
    