#!/usr/bin/env python3
"""Regenerate the precise step-zero peak figure from the frozen peak CSV."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=pd.read_csv(ROOT/'02_数字表格/BENCH_PTE_PIE_BY_STEP.csv');names=['miflu','nlinear','patchtst'];labels=['MIFlu','NLinear','PatchTST'];q=d[d.step==0].groupby('model')[['PTE_wk','PIE_pct']].mean().loc[names]
 fig,axs=plt.subplots(1,2,figsize=(11.4,4.3),constrained_layout=True)
 for ax,col,threshold,title,unit in zip(axs,['PTE_wk','PIE_pct'],[1.,25.],['Peak timing error at step zero','Peak intensity error at step zero'],['Weeks','Percent']):
  v=q[col].to_numpy();ax.bar(labels,v,color=['#16877B' if x<=threshold else '#BD5A2B' for x in v],width=.6);ax.axhline(threshold,color='#AA3333',ls='--',lw=1.6,label=f'Tolerance {threshold:g}');ax.set_ylim(0,max(threshold*1.14,max(v)*1.2));ax.set_ylabel(unit);ax.set_title(title,fontsize=12);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
  for i,x in enumerate(v):ax.text(i,x+.025*ax.get_ylim()[1],f'{x:.3f}',ha='center',fontsize=11)
  ax.legend(loc='upper left',frameon=False)
 fig.suptitle('Mean across four horizons; each metric coloured against its own tolerance',fontsize=11)
 out=ROOT/'01_最终报告/figures/fig_ks_ranking.png';fig.savefig(out,dpi=180);plt.close(fig);print(out)
if __name__=='__main__':main()
