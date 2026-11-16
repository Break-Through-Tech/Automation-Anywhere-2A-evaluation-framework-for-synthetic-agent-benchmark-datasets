"""Export the issue #66 diagnostic figure from saved findings; no API calls."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).parent;v=json.loads((P/'findings.json').read_text());d=v['retail_minus_airline'];ws=v['weight_sensitivity']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(12,4.8));fig.subplots_adjust(left=.15,right=.97,top=.78,bottom=.23,wspace=.40)
fig.suptitle('Airline vs retail: different strengths, almost tied composite',fontsize=15,fontweight='bold',y=.97)
rows=d['dimension_contributions'];axs[0].barh([r['dimension'].replace('_',' ') for r in rows],[r['difficulty_point_difference'] for r in rows],color='#31668b');axs[0].invert_yaxis();axs[0].set_ylabel('Difficulty dimension');axs[0].set_xlabel('Retail − airline difficulty contribution (0–100 points)');axs[0].set_title('The 5.77-point difficulty gap comes\nmainly from dependencies and tool use',fontsize=11,pad=13);axs[0].set_xlim(0,2.7)
for i,r in enumerate(rows):axs[0].text(r['difficulty_point_difference']+.05,i,f"{r['difficulty_point_difference']:.2f}",va='center')
axs[1].plot([100*w['coverage_weight'] for w in ws],[w['retail_minus_airline'] for w in ws],marker='o',color='#31668b',label='Retail − airline composite')
axs[1].axhline(0,color='#666666',linewidth=.8);axs[1].axvline(50,color='#999999',linestyle=':',label='Selected 50% Coverage');axs[1].scatter([50],[d['composite_points_at_50_50']],color='#b35635',zorder=3);axs[1].set_xlabel('Coverage weight (%); remaining weight is Difficulty');axs[1].set_ylabel('Composite difference (0–100 points)');axs[1].set_title('Composite ordering reverses at\n50.40% Coverage weight',fontsize=11,pad=13);axs[1].legend(frameon=False,fontsize=8,loc='upper right');axs[1].text(50.8,.15,'50/50 gap: +0.046',fontsize=9)
fig.text(.02,.08,'Sources: frozen workflow labels/catalog; finalized v1.1 task scores; Ronnit’s #65 profiles. Native tasks: airline n=50, retail n=114.',fontsize=9)
fig.text(.02,.035,'Descriptive source-consistency and sensitivity checks, November 15, 2026. Shared sources and judge; no independent validity or significance claim.',fontsize=9,color='#555555')
for ext in ('png','svg'):fig.savefig(P/('domain_difference_checks.'+ext),dpi=160)
plt.close(fig)
