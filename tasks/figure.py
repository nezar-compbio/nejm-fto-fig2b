from __future__ import division, print_function
import argparse
import datetime
import os
pjoin = os.path.join

import matplotlib as mpl
mpl.use('agg')
import seaborn as sns
sns.set_style('white') 
sns.set_context('paper') #poster, talk

from matplotlib.ticker import MaxNLocator, FuncFormatter
import matplotlib.pyplot as plt
import numpy as np

#PROJECT_DIR = pjoin(os.getcwd(), os.path.pardir)
BP_START    = 52800000
BP_STOP     = 56000000
BP_CHROMLEN = 90354753

names = [
    'rs1421085',
    'IRX5',
    'IRX3',
    'FTO',
    'RPGRIP1L',
    'RBL2',
    'CHD9',
    'IRX6',
    'CRNDE',
]

locations = [ #bp coordinate
    (53800954, 53800954), # SNP rs1421085
    (54964200, 54965302),
    (54319016, 54319016),
    (53737375, 53738194),
    (53737375, 53738194),
    (53467832, 53468474),
    (53088445, 53089051),
    (55357172, 55357772),
    (54973696, 54974296),
]


# some utils...
def reveal_triu(A):
    B = np.array(A)
    B[np.tril_indices_from(B)] = np.nan
    return B


def reveal_tril(A):
    B = np.array(A)
    B[np.triu_indices_from(B)] = np.nan
    return B


def chx(start, **kw):
    kw.setdefault('light', 1.0)
    kw.setdefault('dark', 0.0)
    kw.setdefault('as_cmap', True)
    return sns.cubehelix_palette(start=start, **kw)


class Binner(object):
    def __init__(self, bp_start, bp_end, bp_step):
        import math
        self.start, self.stop, self.step = bp_start, bp_end, bp_step
        self.n_bins = int(math.floor((bp_end - bp_start)/bp_step))
    
    def get(self, bp_coord):
        i = (bp_coord - self.start)//self.step
        return max(0, min(i, self.n_bins-1))


# Dumb workaround until I figure out why reduceld.py chokes on empty bins. (5kb)
# Need to manually remove the following bins from the index file and readd them here:
#   605 and 607
def add_missing_bins(L):
    tmp1 = np.concatenate([L[:, :605], np.nan*np.ones((L.shape[0],1)), L[:, 605:]], axis=1)
    tmp2 = np.concatenate([tmp1[:, :607], np.nan*np.ones((tmp1.shape[0],1)), tmp1[:, 607:]], axis=1)
    tmp3 = np.concatenate([tmp2[:605, :], np.nan*np.ones((1,tmp2.shape[1])), tmp2[605:,:]], axis=0)
    tmp4 = np.concatenate([tmp3[:607, :], np.nan*np.ones((1,tmp3.shape[1])), tmp2[607:,:]], axis=0)
    return tmp4.copy()


def main(hicfile, ldaggfile, binsize, out):
    BINSIZE = binsize
    START = BP_START//BINSIZE
    STOP  = BP_STOP//BINSIZE 
    binner = Binner(0, BP_CHROMLEN, BINSIZE)

    name_point = { #bin coordinate
        name: (binner.get(loc[0]), binner.get(loc[1])) \
            for (name, loc) in zip(names, locations)
    }

    # Get Hi-C data
    chr16 = np.load(hicfile)
    colsum = chr16.sum(axis=0).max()
    A = chr16[START:STOP, START:STOP]
    N = len(A)

    # Get LD data
    L = np.loadtxt(ldaggfile)
    if BINSIZE == 5000:
        L = add_missing_bins(L)

    # 1 main axis + 2 colorbar axes
    f, (ax, cax1, cax2) = plt.subplots(3,1, figsize=(20,50))

    # plot HiC/LD
    imA = ax.matshow(
        reveal_triu(np.log(A)), 
        cmap=chx(0.6), 
        interpolation='none'
    )
    imL = ax.matshow(
        reveal_tril(np.log10(L)), 
        cmap=plt.cm.Blues, 
        interpolation='none'
    )
    ax.set_xlim([0, N])
    ax.set_ylim([N, 0])
    bbox = ax.get_position()

    # genomic coordinate ticks
    tick_locator = MaxNLocator(4)
    tick_formatter = FuncFormatter( lambda x, pos: '{:7.0f}'.format(START*BINSIZE + x*BINSIZE) )
    ax.xaxis.set_major_locator(tick_locator)
    ax.xaxis.set_major_formatter(tick_formatter)
    ax.yaxis.set_major_locator(tick_locator)
    ax.yaxis.set_major_formatter(tick_formatter)

    #Hi-C colorbar (units = contact probability)
    cax1.set_position([
        bbox.x0+bbox.width-0.07, 
        bbox.y0, 
        0.015, 
        bbox.height,
    ])
    cbar = f.colorbar(imA, cax=cax1)
    cmin, cmax = cbar.get_clim()
    cticks = np.linspace(cmin, cmax, 5)
    cbar.set_ticks(cticks)
    cbar.set_ticklabels(['{:0.2f}'.format(np.exp(t)/colsum * 100) for t in cticks])

    # LD colorbar (units = log10 r^2-value)
    cax2.set_position([
        bbox.x0+bbox.width,
        bbox.y0,
        0.015,
        bbox.height,
    ])
    cbar = f.colorbar(imL, cax=cax2)
    cmin, cmax = cbar.get_clim()
    cticks = np.linspace(cmin, cmax, 5)
    cbar.set_ticks(cticks)
    cbar.set_ticklabels(['{:0.1f}'.format(t) for t in cticks])

    # identify loci
    for name, point in name_point.items():
        a, b = point
        kw = {}
        if name == 'rs1421085':
            kw['marker'] = 'o'
            kw['markerfacecolor'] = 'r'
            kw['markeredgecolor'] = 'r'
            kw['markeredgewidth'] = 1
        else:
            kw['marker'] = 'o'
            kw['markerfacecolor'] = 'none'
            kw['markeredgecolor'] = 'r'
            kw['markeredgewidth'] = 1
        ax.plot(a-START, b-START, **kw)

    
    p = name_point['CHD9'][0]-START; d = 160
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+2, 'CHD9')

    p = name_point['RBL2'][0]-START; d = 160
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+2, 'RBL2')

    p = name_point['FTO'][0]-START; d = 320
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+4, 'FTO\nRFGRIP1L')

    p = name_point['rs1421085'][0]-START; d = 160
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+2, 'rs1421085')

    p = name_point['IRX3'][0]-START; d = 160
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+2, 'IRX3')

    p = name_point['IRX5'][0]-START; d = 160
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+4, 'IRX5\nCRNDE')

    p = name_point['IRX6'][0]-START; d = 80
    ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
    ax.text(p, p+d+2, 'IRX6');

    plt.savefig(
        out+'.{}.pdf'.format(datetime.date.today()),
        bbox_inches='tight', 
        pad_inches=0
    )



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("hicfile", type=str)
    parser.add_argument("ldaggfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--out", type=str, required=True)

    args = parser.parse_args()
    main(**vars(args))
