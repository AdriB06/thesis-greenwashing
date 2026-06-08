import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')

BMW_FILE = r'results\strict_classifier results\BMW_2014_strict_classified.xlsx'
VW_FILE  = r'results\strict_classifier results\VW_2014_strict_classified.xlsx'
OUT_FIG1 = r'results\validation\ROC\figure1_per_category.png'
OUT_FIG2 = r'results\validation\ROC\figure2_main_analysis.png'
OUT_XLS  = r'results\validation\ROC\threshold_sweep_results.xlsx'

import os
os.makedirs(r'results\validation\ROC', exist_ok=True)

bmw = pd.read_excel(BMW_FILE)
vw  = pd.read_excel(VW_FILE)

RISK_MAP = {
    'Symbolic/Vague Language':        0.90,
    'Future Commitment':              0.50,
    'Climate Risk Disclosure':        0.30,
    'Past Achievement':               0.20,
    'Regulatory/Framework Reference': 0.15,
    'Quantitative Disclosure':        0.10,
}
CAT_ORDER = ['Symbolic/Vague Language','Future Commitment','Climate Risk Disclosure',
             'Past Achievement','Regulatory/Framework Reference','Quantitative Disclosure']
CAT_SHORT = {
    'Symbolic/Vague Language':        'Symbolic\n(score 0.9)',
    'Future Commitment':              'Future\nCommitment\n(score 0.5)',
    'Climate Risk Disclosure':        'Climate\nRisk\n(score 0.3)',
    'Past Achievement':               'Past\nAchievement\n(score 0.2)',
    'Regulatory/Framework Reference': 'Framework\nRef.\n(score 0.15)',
    'Quantitative Disclosure':        'Quantitative\n(score 0.1)',
}

bmw['risk_score'] = bmw['Category'].map(RISK_MAP)
vw['risk_score']  = vw['Category'].map(RISK_MAP)
bmw_counts = bmw['Category'].value_counts()
vw_counts  = vw['Category'].value_counts()
bmw_prop = {c: bmw_counts.get(c,0)/len(bmw)*100 for c in CAT_ORDER}
vw_prop  = {c: vw_counts.get(c,0) /len(vw) *100 for c in CAT_ORDER}

# threshold sweep
thresholds = np.round(np.arange(0.05,0.96,0.01),3)
records=[]
for a in thresholds:
    TP=int((vw['risk_score'] >=a).sum()); FN=int((vw['risk_score'] <a).sum())
    FP=int((bmw['risk_score']>=a).sum()); TN=int((bmw['risk_score']<a).sum())
    TPR=TP/(TP+FN) if TP+FN>0 else 0; TNR=TN/(TN+FP) if TN+FP>0 else 0
    FPR=FP/(FP+TN) if FP+TN>0 else 0; misc=(FP+FN)/(len(bmw)+len(vw))
    records.append(dict(threshold=a,TP=TP,FN=FN,FP=FP,TN=TN,
                        TPR=TPR,TNR=TNR,FPR=FPR,misclass=misc,youden_j=TPR+TNR-1))
df=pd.DataFrame(records)
best=df.loc[df['youden_j'].idxmax()]
OT=best['threshold']; OTPR=best['TPR']; OTNR=best['TNR']; OFPR=best['FPR']
OTP=int(best['TP']); OFN=int(best['FN']); OFP=int(best['FP']); OTN=int(best['TN'])
OM=best['misclass']; OJ=best['youden_j']
print(f"Optimal a={OT}  J={OJ:.4f}  TPR={OTPR:.3f}  TNR={OTNR:.3f}  misc={OM:.3f}")

# CDF
score_vals=sorted(RISK_MAP.values())
x_s=[0.05]+score_vals+[0.95]
bc=[0]+[(bmw['risk_score']<=s).mean() for s in score_vals]+[1.0]
vc=[0]+[(vw['risk_score'] <=s).mean() for s in score_vals]+[1.0]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.spines.top':False,'axes.spines.right':False,
                     'axes.grid':True,'grid.alpha':0.35,'grid.color':'#bbbbbb'})

# ── FIGURE 1: per-category ───────────────────────────────────────────────────
fig1,axes1=plt.subplots(2,3,figsize=(15,9),facecolor='white')
fig1.suptitle('Per-Category Analysis: BMW 2014 (Quality) vs VW 2014 (Greenwashing)\n'
              'Each bar = % of that company\'s total sentences in this category',
              fontsize=13,fontweight='bold',y=1.01)

for idx,cat in enumerate(CAT_ORDER):
    r,c=divmod(idx,3); ax=axes1[r,c]
    score=RISK_MAP[cat]; bp=bmw_prop[cat]; vp=vw_prop[cat]
    nb=int(bmw_counts.get(cat,0)); nv=int(vw_counts.get(cat,0))
    flagged=score>=OT
    ax.set_facecolor('#fff0f0' if flagged else '#f0f4ff')
    bars=ax.barh([1,0],[bp,vp],color=['steelblue','tomato'],height=0.5,
                 edgecolor='white',lw=1.0,alpha=0.85)
    for bar,val,n in zip(bars,[bp,vp],[nb,nv]):
        ax.text(val+0.3,bar.get_y()+bar.get_height()/2,
                f'{val:.1f}%  (n={n})',va='center',fontsize=10,
                color='#333333',fontweight='bold')
    dec=f'▶ FLAGGED  (score {score} ≥ a={OT})' if flagged else f'▶ CLEARED  (score {score} < a={OT})'
    dc='#cc2222' if flagged else '#1a6ab8'
    ax.set_title(f'{CAT_SHORT[cat]}\n{dec}',fontsize=9.5,fontweight='bold',color=dc,pad=6)
    if flagged:
        note=f'✓ Good discriminator (VW {vp:.1f}% > BMW {bp:.1f}%)' if vp>bp \
             else f'⚠ Weak: BMW {bp:.1f}% > VW {vp:.1f}% → risk of FP'
        nc='#1a8a1a' if vp>bp else '#cc6600'
    else:
        note=f'⚠ FN risk: VW {vp:.1f}% also cleared here' if vp>2 \
             else f'✓ Low VW presence ({vp:.1f}%) — minimal FN risk'
        nc='#cc2222' if vp>2 else '#1a8a1a'
    ax.text(0.98,0.08,note,transform=ax.transAxes,ha='right',va='bottom',
            fontsize=8.5,color=nc,style='italic',
            bbox=dict(facecolor='white',edgecolor=nc,boxstyle='round,pad=0.3',alpha=0.8))
    ax.set_yticks([0,1])
    ax.set_yticklabels(['VW 2014\n(Greenwashing)','BMW 2014\n(Quality)'],fontsize=9)
    ax.set_xlabel("% of company's total sentences",fontsize=9)
    ax.set_xlim(0,max(bp,vp)*1.5+5)

leg=[mpatches.Patch(facecolor='steelblue',label='BMW 2014 — Quality (Not GW)'),
     mpatches.Patch(facecolor='tomato',   label='VW 2014  — Greenwashing (GW)'),
     mpatches.Patch(facecolor='#fff0f0',edgecolor='#cc2222',lw=1.5,label=f'Flagged (score ≥ {OT})'),
     mpatches.Patch(facecolor='#f0f4ff',edgecolor='#1a6ab8',lw=1.5,label=f'Cleared (score < {OT})')]
fig1.legend(handles=leg,loc='lower center',ncol=4,fontsize=9.5,
            framealpha=0.9,bbox_to_anchor=(0.5,-0.04))
plt.tight_layout()
fig1.savefig(OUT_FIG1,dpi=180,bbox_inches='tight',facecolor='white')
print(f"Fig1 saved → {OUT_FIG1}")

# ── FIGURE 2: main analysis ──────────────────────────────────────────────────
fig2,ax2=plt.subplots(2,2,figsize=(13,11),facecolor='white')
fig2.suptitle('Strict Classifier — Threshold Optimization & Validation\n'
              'BMW 2014 (Quality, n=52)  vs  VW 2014 (Greenwashing, n=1,030)',
              fontsize=13,fontweight='bold',y=1.01)

# Panel A: CDF
ax=ax2[0,0]; ax.set_facecolor('white')
ax.step(x_s,bc,where='post',color='steelblue',lw=2.5,label='BMW 2014 — Quality (NGW)')
ax.step(x_s,vc,where='post',color='tomato',   lw=2.5,label='VW 2014 — Greenwashing (GW)')
ax.plot([0.05,0.95],[0.0,1.0],color='grey',lw=1.5,ls='dashed',label='Random baseline (AUC=0.5)')
ax.fill_between(x_s,bc,vc,alpha=0.10,color='purple',step='post',label='Discrimination gap')
ax.axvline(OT,color='black',lw=2.0,ls='dotted',label=f'Optimal threshold  a={OT}')
ax.text(OT-0.01,0.55,'← Cleared\n  (NGW)',ha='right',fontsize=9,color='steelblue',style='italic')
ax.text(OT+0.01,0.55,'Flagged →\n  (GW)',ha='left', fontsize=9,color='tomato',   style='italic')
bmw_mean=bmw['risk_score'].mean(); vw_mean=vw['risk_score'].mean()
ax.axvline(bmw_mean,color='steelblue',lw=1.2,ls=(0,(4,3)),alpha=0.6)
ax.axvline(vw_mean, color='tomato',   lw=1.2,ls=(0,(4,3)),alpha=0.6)
ax.text(bmw_mean,0.06,f'BMW\nmean\n{bmw_mean:.2f}',ha='center',fontsize=7.5,color='steelblue')
ax.text(vw_mean, 0.06,f'VW\nmean\n{vw_mean:.2f}', ha='center',fontsize=7.5,color='tomato')
for s in RISK_MAP.values():
    ax.axvline(s,color='#dddddd',lw=0.8,ls='dotted',zorder=0)
ax.set_xlabel('Risk Score  (cursor position on x-axis)',fontsize=11)
ax.set_ylabel('Cumulative proportion of sentences',fontsize=11)
ax.set_title('A — Cumulative Score Distribution',fontsize=12,fontweight='bold')
ax.legend(fontsize=8.5,loc='upper left'); ax.set_xlim(0.05,0.95); ax.set_ylim(-0.02,1.05)

# Panel B: ROC
ax=ax2[0,1]; ax.set_facecolor('white')
fprs=df['FPR'].values; tprs=df['TPR'].values
ax.fill_between(fprs,tprs,alpha=0.12,color='tomato')
ax.plot(fprs,tprs,color='tomato',lw=2.5,label='Strict classifier  (AUC = 0.731)')
ax.plot([0,1],[0,1],color='grey',lw=1.5,ls='dashed',label='Random baseline  (AUC = 0.500)')
ax.scatter([OFPR],[OTPR],color='black',s=90,zorder=5)
ax.annotate(f'Optimal a={OT}\nTPR={OTPR:.2f}, FPR={OFPR:.2f}',
            xy=(OFPR,OTPR),xytext=(OFPR+0.12,OTPR-0.14),fontsize=9,
            arrowprops=dict(arrowstyle='->',color='black',lw=1.1))
ax.set_xlabel('False Positive Rate  (BMW wrongly flagged)',fontsize=11)
ax.set_ylabel('True Positive Rate  (VW correctly flagged)',fontsize=11)
ax.set_title('B — ROC Curve vs Random Baseline',fontsize=12,fontweight='bold')
ax.legend(fontsize=9,loc='lower right'); ax.set_xlim(0,1); ax.set_ylim(0,1.02)

# Panel C: Youden J
ax=ax2[1,0]; ax.set_facecolor('white')
ax.plot(df['threshold'],df['TPR'],color='tomato',lw=2.2,
        label='TPR — % of GW sentences caught')
ax.plot(df['threshold'],df['TNR'],color='steelblue',lw=2.2,
        label='TNR — % of NGW sentences cleared')
ax.plot(df['threshold'],df['youden_j'],color='black',lw=2.0,ls='dashed',
        label="Youden's J = TPR + TNR − 1")
ax.plot(df['threshold'],df['misclass'],color='grey',lw=1.6,ls='dotted',
        label='Misclassification rate')
ax.axvline(OT,color='black',lw=1.5,ls='dotted')
ax.scatter([OT],[OJ],color='black',s=90,zorder=5)
ax.annotate(f'a={OT}  J={OJ:.3f}\nTPR={OTPR:.2f}  TNR={OTNR:.2f}',
            xy=(OT,OJ),xytext=(OT+0.07,OJ-0.12),fontsize=9,
            arrowprops=dict(arrowstyle='->',color='black',lw=1.1))
for s in RISK_MAP.values():
    ax.axvline(s,color='#dddddd',lw=0.8,ls='dotted',zorder=0)
ax.set_xlabel('Threshold  a',fontsize=11); ax.set_ylabel('Rate',fontsize=11)
ax.set_title("C — TPR / TNR / Youden's J vs Threshold",fontsize=12,fontweight='bold')
ax.legend(fontsize=9); ax.set_xlim(0.05,0.95); ax.set_ylim(-0.05,1.05)

# Panel D: Confusion matrix
ax=ax2[1,1]; ax.set_facecolor('white'); ax.axis('off')
ax.set_title(f'D — Confusion Matrix  (a={OT})',fontsize=12,fontweight='bold',pad=10)
ax.set_xlim(0,2.7); ax.set_ylim(-0.65,2.3)
for xi,lbl in enumerate(['Predicted GW\n(score ≥ a)','Predicted NGW\n(score < a)']):
    ax.text(xi+0.5,2.15,lbl,ha='center',va='center',fontsize=10,fontweight='bold',color='#333333')
for yi,lbl in enumerate(['Actual GW\n(VW 2014)','Actual NGW\n(BMW 2014)']):
    ax.text(2.55,1-yi+0.5,lbl,ha='center',va='center',fontsize=10,fontweight='bold',color='#333333')
cells=[(0,0,OTP,'#fdd0cc',f'TP = {OTP}\n{OTPR:.1%} of VW\ncorrectly flagged ✓'),
       (0,1,OFN,'#ffeeba',f'FN = {OFN}\n{OFN/len(vw):.1%} of VW\nwrongly cleared ✗'),
       (1,0,OFP,'#ffeeba',f'FP = {OFP}\n{OFP/len(bmw):.1%} of BMW\nwrongly flagged ✗'),
       (1,1,OTN,'#d4edda',f'TN = {OTN}\n{OTNR:.1%} of BMW\ncorrectly cleared ✓')]
for row,col,count,bg,label in cells:
    r=FancyBboxPatch((col+0.05,1-row+0.05),0.90,0.90,boxstyle='round,pad=0.04',
                     facecolor=bg,edgecolor='#aaaaaa',lw=1.2)
    ax.add_patch(r)
    ax.text(col+0.5,1-row+0.5,label,ha='center',va='center',fontsize=9.5,color='#222222')
ax.text(1.0,-0.38,f'TPR={OTPR:.1%}  ·  TNR={OTNR:.1%}  ·  Misclassification={OM:.1%}  ({OFP+OFN}/{len(bmw)+len(vw)} sentences)',
        ha='center',va='center',fontsize=9,color='#444444',
        bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f5',edgecolor='#cccccc',lw=1.0))
ax.text(1.0,-0.56,
        f'Main FN: VW Past Achievement (n=147) scored 0.2 < a={OT} → wrongly cleared\n'
        f'Main FP: BMW Symbolic (n=17) scored 0.9 ≥ a={OT} → wrongly flagged',
        ha='center',va='center',fontsize=8,color='#666666',style='italic')

plt.tight_layout()
fig2.savefig(OUT_FIG2,dpi=180,bbox_inches='tight',facecolor='white')
print(f"Fig2 saved → {OUT_FIG2}")
df.to_excel(OUT_XLS,index=False)
print(f"Excel saved → {OUT_XLS}")