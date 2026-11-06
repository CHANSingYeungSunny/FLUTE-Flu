#!/usr/bin/env python3
"""Presentation-specific plot of the unchanged eleven-model parameter subset."""
from pathlib import Path
import pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1];e=pd.read_csv(r/'02_数字表格/BENCH_EFFICIENCY.csv').dropna(subset=['params'])
fig,ax=plt.subplots(figsize=(9,5.1),dpi=200);fig.patch.set_facecolor('white');ax.set_facecolor('white')
other=e[~e.model.isin(['nlinear','patchtst'])]
ax.scatter(other.params,other.mse_mean,s=60,c='#8798A7',label='Other measured arms',zorder=3)
for name,label,color,offset in [('nlinear','NLinear','#087F83',(10,18)),('patchtst','PatchTST','#BA5B2B',(12,-28))]:
 q=e[e.model==name].iloc[0];ax.scatter([q.params],[q.mse_mean],s=130,c=color,marker='D',zorder=4)
 ax.annotate(label,(q.params,q.mse_mean),xytext=offset,textcoords='offset points',fontsize=17,fontweight='bold',color=color)
front=e[e.model.isin(['nlinear','patchtst'])].sort_values('params');ax.plot(front.params,front.mse_mean,c='#536678',lw=1.5,ls='--',zorder=2,label='Measured subset frontier')
ax.set_xscale('log');ax.set_ylim(1.1,6.2);ax.set_xlim(1000,4e9)
ax.set_xlabel('Parameter count (log scale)',fontsize=15,labelpad=12);ax.set_ylabel('Mean MSE',fontsize=15,labelpad=10)
ax.tick_params(labelsize=13);ax.grid(axis='y',color='#E1E7EB',lw=.7)
for side in ['top','right']:ax.spines[side].set_visible(False)
ax.spines['bottom'].set_color('#9AA9B4');ax.spines['left'].set_color('#9AA9B4')
ax.legend(loc='upper left',fontsize=12,frameon=False);fig.tight_layout(pad=1.4)
fig.savefig(r/'01_最终报告/figures/fig_pareto_presentation.png',bbox_inches='tight');plt.close(fig)
