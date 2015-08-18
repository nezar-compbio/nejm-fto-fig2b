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

blues = sns.cubehelix_palette(0.4, gamma=0.5, rot=-0.3, dark=0.1, light=0.9, as_cmap=True)

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
    #chr16 = np.load(hicfile)
    #colsum = chr16.sum(axis=0).max()
    #A = chr16[START:STOP, START:STOP]
    A = np.load(hicfile)
    colsum = 1  #2387.157
    N = len(A)

    # Get LD data
    L = np.loadtxt(ldaggfile)
    # L = np.log10(L)

    # 1 main axis + 2 colorbar axes
    f, (ax, cax1, cax2) = plt.subplots(3,1, figsize=(20, 50))

    # plot HiC/LD
    imA = ax.matshow(
        reveal_triu(np.log(A)), 
        cmap=blues, 
        interpolation='none'
    )
    imL = ax.matshow(
        reveal_tril(L), 
        cmap=plt.cm.Reds, 
        interpolation='none'
    )
    ax.set_xlim([0, N])
    ax.set_ylim([N, 0])
    bbox = ax.get_position()

    # genomic coordinate ticks
    tick_locator = MaxNLocator(4)
    tick_formatter = FuncFormatter( lambda x, pos: '{:,}'.format(int(START*BINSIZE + x*BINSIZE)))
    ax.xaxis.set_major_locator(tick_locator)
    ax.xaxis.set_major_formatter(tick_formatter)
    ax.yaxis.set_major_locator(tick_locator)
    ax.yaxis.set_major_formatter(tick_formatter)

    #Hi-C colorbar (units = intrachromosomal contact probability)
    cax1.set_position([
        bbox.x0+bbox.width-0.05, 
        bbox.y0, 
        0.015, 
        bbox.height,
    ])
    cbar = f.colorbar(imA, cax=cax1)
    cmin, cmax = cbar.get_clim()
    cticks = np.linspace(cmin, cmax, 5)
    cbar.set_ticks(cticks)
    cbar.set_ticklabels(['{:0.1e}'.format(np.exp(t)/colsum) for t in cticks])

    # LD colorbar (units = (log10?) r^2-value)
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
    cbar.set_ticklabels(['{:.1e}'.format(t) for t in cticks])

    # identify loci
    for name, point in name_point.items():
        a, b = point
        kw = {}
        if name == 'rs1421085':
            kw['marker'] = 'o'
            kw['markerfacecolor'] = 'k'
            kw['markeredgecolor'] = 'k'
            kw['markeredgewidth'] = 1
        else:
            kw['marker'] = 'o'
            kw['markerfacecolor'] = 'none'
            kw['markeredgecolor'] = 'k'
            kw['markeredgewidth'] = 1
        ax.plot(a-START, b-START, **kw)

    unit = 80
    if binsize != 5000:
        unit = 10
    
    names_ = ['CHD9', 'RBL2', 'FTO', 'rs1421085', 'IRX3', 'IRX5', 'IRX6']
    texts = ['CHD9', 'RBL2', 'FTO\nRFGRIP1L', 'rs1421085', 'IRX3', 'IRX5\nCRNDE', 'IRX6']
    mults = [2,2,4,2,2,2,1] 
    for name, text, mult in zip(names_, texts, mults):
        p = name_point[name][0]-START
        d = mult*unit
        ax.plot([p, p], [p, p+d], 'k--', linewidth=1)
        ax.text(p, p+d+mult, text)

    plt.savefig(
        out+'.{}.pdf'.format(datetime.date.today()),
        bbox_inches='tight', 
        pad_inches=0.5
    )



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("hicfile", type=str)
    parser.add_argument("ldaggfile", type=str)
    parser.add_argument("binsize", type=int)
    parser.add_argument("--out", type=str, required=True)

    args = parser.parse_args()
    main(**vars(args))
