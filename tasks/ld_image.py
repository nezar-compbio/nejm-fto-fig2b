from __future__ import division, print_function
import argparse
import datetime

import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def main(matrixfile, binsize, fmt, out):
    mat = np.loadtxt(matrixfile)
    plt.matshow(np.log(mat), cmap=plt.cm.Reds)
    plt.savefig(out+'.{}.{}.{}.png'.format(binsize, fmt, datetime.date.today()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("matrixfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--fmt", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    main(**vars(args))
