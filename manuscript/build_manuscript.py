#!/usr/bin/env python3
"""Build the English journal manuscript from one content source and frozen evidence.
No model execution. PDF is compiled separately from the publisher LaTeX class.
"""
from pathlib import Path
import json,re,shutil,math,hashlib,sys
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent;LATEX=HERE/'overleaf';OUT=ROOT/'01_最终报告'

def cite_ids(text):
 ids=[]
 for m in re.finditer(r'\[(\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*)\]',text):
  for p in m[1].split(','):
   q=re.split('[–-]',p.strip());ids += list(range(int(q[0]),int(q[-1])+1))
 return ids

def roman(n):
 ans=''
 for v,s in [(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
  while n>=v:ans+=s;n-=v
 return ans

def tables(source):
 old=source['table_source']
 protocol=[['Analysis','Runs or models','Evaluation'],['Reproduction','MIFlu; 10 seeds','Reference-table comparison'],['Accuracy and peaks','28 models; 3 seeds','4 lengths; 16 peak cells/model'],['Parameters','11 models','Exported size and MSE'],['Paired comparisons','17 models','136 pairs; 12 contributions/pair']]
 rep=[['Length','Our MSE ± SD','Reference MSE','Our MAE','Reference MAE']]+[[r[i] for i in [0,1,2,4,5]] for r in old['reproduction'][1:]]
 accuracy=[['Rank','Implementation','Mean MSE','Mean MAE']]+[[r[i] for i in [0,1,6,7]] for r in old['accuracy'][1:]]
 peaks=[['Model','PTE (weeks)','PIE (%)','Joint passes']]+[[r[i] for i in [0,1,2,3]] for r in old['peaks'][1:]]
 paired=[['Model A','Model B','Raw p','Adjusted p']]+[[r[i] for i in [0,1,3,4]] for r in old['paired'][1:]]
 return {
 'protocol':{'rows':protocol,'caption':'Separate evaluation populations and run sets','note':'The roster contains 13 conventional models, four LLM-based models and 11 frozen encoders. Each analysis uses its stated denominator.','widths':[.95,1.1,1.3]},
 'reproduction':{'rows':rep,'caption':'MIFlu reproduction under its separate ten-seed protocol','note':'SD is reconstructed from the archived score record. Original run predictions are unavailable for independent rescoring. The four-length row reports the aggregate comparison.','widths':[.48,1.0,.63,.61,.63]},
 'accuracy':{'rows':accuracy,'caption':'Average errors of the 28 retained implementations','note':'Three benchmark seeds, four forecast lengths and the declared cropped-window contract. Names label project implementations; method fidelity is not established by the ranking.','widths':[.45,1.43,.74,.73]},
 'peaks':{'rows':peaks,'caption':'Mean peak errors and the joint aggregated-cell screen','note':'The denominator is four forecast lengths times four leads. A pass requires mean PTE at most one week and mean PIE at most 25% in the same cell; it is not a seasonal success probability.','widths':[1.03,.78,.78,.76]},
 'paired':{'rows':paired,'caption':'Selected comparisons with recomputed Holm adjustment','note':'Family: 17 non-encoder models including MIFlu, excluding DLinear and frozen encoders. There are 136 pairs and 12 matched contributions per pair. Raw p-values are rounded exports; adjusted values shown at four decimals.','widths':[1.01,1.0,.68,.66]}}

def plots():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 D=ROOT/'02_数字表格';m=pd.read_csv(D/'BENCH_MSE_BY_MODEL_L.csv');p=pd.read_csv(D/'BENCH_PTE_PIE_BY_STEP.csv');e=pd.read_csv(D/'BENCH_EFFICIENCY.csv')
 rank=m.groupby('model').agg(mse=('mse_7var_z','mean'),family=('family','first')).join(p.groupby('model').PIE_pct.mean()).sort_values('mse')
 assert len(rank)==28 and list(rank.index[:3])==['miflu','patchtst','nlinear']
 styles={'classical_ml':('#536675','o'),'neural':('#7d7298','s'),'transformer':('#b25a26','^'),'linear':('#00868b','D'),'llm':('#1c455c','P'),'llm_encoder':('#9ca9b4','x')}
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42})
 fig,ax=plt.subplots(figsize=(3.4,2.65),constrained_layout=True)
 for family,g in rank.groupby('family'):
  color,marker=styles[family];ax.scatter(g.mse,g.PIE_pct,c=color,marker=marker,s=24,linewidths=.7,label=family.replace('_',' '))
 for model,offset in [('miflu',(-2,8)),('patchtst',(7,7)),('nlinear',(6,-10))]:
  r=rank.loc[model];ax.annotate({'miflu':'MIFlu','patchtst':'PatchTST','nlinear':'NLinear'}[model],(r.mse,r.PIE_pct),xytext=offset,textcoords='offset points',fontsize=8)
 ax.set(xlabel='Mean squared error (standardised)',ylabel='Mean peak-intensity error (%)');ax.grid(alpha=.14);ax.set_axisbelow(True)
 for ext in ['pdf','png']:fig.savefig(LATEX/'figures'/('peak_scatter.'+ext),dpi=300)
 plt.close(fig)
 g=e.dropna(subset=['params']).copy();assert len(g)==11
 fig,ax=plt.subplots(figsize=(3.4,2.65),constrained_layout=True)
 ax.scatter(g.params,g.mse_mean,c='#8c9ba6',s=22)
 low=g[g.model.isin(['nlinear','patchtst'])].sort_values('params');ax.plot(low.params,low.mse_mean,'--',c='#355d72',lw=1)
 for _,r in low.iterrows():
  col='#00868b' if r.model=='nlinear' else '#b25a26';ax.scatter(r.params,r.mse_mean,c=col,marker='D',s=44)
  ax.annotate('NLinear' if r.model=='nlinear' else 'PatchTST',(r.params,r.mse_mean),xytext=(5,9 if r.model=='nlinear' else -12),textcoords='offset points',fontsize=8)
 ax.set_xscale('log');ax.set(xlabel='Exported parameter count (log scale)',ylabel='Mean squared error');ax.grid(alpha=.14);ax.set_axisbelow(True);ax.margins(x=.08,y=.12)
 for ext in ['pdf','png']:fig.savefig(LATEX/'figures'/('pareto.'+ext),dpi=300)
 plt.close(fig)

def tex_escape(s):
 repl={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','–':'--','—':'---','−':'-','’':"'",'“':'``','”':"''",'±':r'$\pm$','×':r'$\times$','²':r'$^2$','ρ':r'$\rho$','≤':r'$\leq$','≥':r'$\geq$'}
 return ''.join(repl.get(c,c) for c in str(s))

def tex_text(s):
 chunks=[];prev=0
 for m in re.finditer(r'\[(\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*)\]',s):
  chunks.append(tex_escape(s[prev:m.start()]));chunks.append('\\cite{'+','.join('r'+str(n) for n in cite_ids(m[0]))+'}');prev=m.end()
 chunks.append(tex_escape(s[prev:]));return ''.join(chunks)

def build():
 source=json.loads((HERE/'article_source.json').read_text());LATEX.mkdir(exist_ok=True);(LATEX/'figures').mkdir(exist_ok=True);plots();T=tables(source)
 used=[]
 for sec in source['sections']:
  for p in sec['parts']:
   for n in cite_ids(p.get('text','')):
    if n not in used:used.append(n)
 mapping={n:i+1 for i,n in enumerate(used)}
 def word_text(s):
  return re.sub(r'\[(\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*)\]',lambda m:'['+', '.join(str(mapping[n]) for n in cite_ids(m[0]))+']',s)
 captions={
 'peak_scatter':'Mean MSE and mean peak-intensity error across the 28 retained implementations. Each point is a model aggregate, not an independent epidemic. The leading models differ locally despite a positive overall rank association.',
 'pareto':'Size–error frontier for the 11 models with parameter exports. The dashed segment joins the two nondominated choices in this subset. Parameter count is a size proxy; MIFlu and frozen encoders have no exported value and are excluded.'}
 # Editable Word copy with full-width opening and two-column journal body.
 d=Document();sec=d.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.7)
 for name in ['Normal','Body Text','Caption','Title','Heading 1','Heading 2']:
  st=d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0);st.font.size=Pt(10);st.paragraph_format.space_after=Pt(4)
 d.styles['Normal'].paragraph_format.line_spacing=1
 d.styles['Title'].font.size=Pt(20);d.styles['Title'].font.bold=False
 for st in [d.styles['Title'],d.styles['Caption']]:
  st.font.bold=False
  for border in list(st.element.xpath('.//w:pBdr')):border.getparent().remove(border)
 d.styles['Heading 1'].font.size=Pt(10);d.styles['Heading 1'].font.bold=False;d.styles['Heading 1'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER;d.styles['Heading 1'].paragraph_format.space_before=Pt(9)
 d.styles['Heading 2'].font.size=Pt(10);d.styles['Heading 2'].font.italic=True;d.styles['Heading 2'].font.bold=False;d.styles['Heading 2'].paragraph_format.space_before=Pt(6)
 p=d.add_paragraph(source['title'],'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 for v in [source['author'],source['affiliation'],source['email']]:
  p=d.add_paragraph(v);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  for r in p.runs:r.font.size=Pt(9)
 p=d.add_paragraph();r=p.add_run('Abstract—');r.bold=True;p.add_run(source['abstract']);p.paragraph_format.space_after=Pt(6)
 p=d.add_paragraph();r=p.add_run('Index Terms—');r.bold=True;p.add_run(source['keywords'])
 sec=d.add_section(WD_SECTION_START.CONTINUOUS);cols=sec._sectPr.find(qn('w:cols'));cols.set(qn('w:num'),'2');cols.set(qn('w:space'),'240')
 latex=[r'\documentclass[journal,twoside,print]{ieeecolor}',r'\usepackage{generic}',r'\usepackage{review_layout}',r'\usepackage[T1]{fontenc}',r'\usepackage[utf8]{inputenc}',r'\usepackage{cite,amsmath,amssymb,graphicx,url,booktabs,array,needspace,balance}',r'\def\journalname{}',r'\markboth{}{CHAN: Re-evaluating Multimodal LLMs for Influenza Forecasting}',r'\begin{document}',r'\title{'+tex_escape(source['latex_title'])+'}',r'\author{\mbox{'+tex_escape(source['author']).replace(' ','~')+'}'+r'\thanks{'+tex_escape(source['author']+' is with the '+source['affiliation']+' (e-mail: '+source['email']+').')+'}}',r'\maketitle',r'\begin{abstract}',tex_escape(source['abstract']),r'\end{abstract}',r'\begin{IEEEkeywords}',tex_escape(source['keywords']),r'\end{IEEEkeywords}']
 nt=nf=0
 for ns,section in enumerate(source['sections'],1):
  d.add_paragraph(f'{roman(ns)}. '+section['title'].upper(),'Heading 1');latex.append('\\Needspace{5\\baselineskip}\n\\section{'+tex_escape(section['title'])+'}');subn=0
  for part in section['parts']:
   kind=part['kind']
   if kind=='paragraph':
    p=d.add_paragraph(word_text(part['text']));p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;p.paragraph_format.widow_control=True;latex.append(tex_text(part['text'])+'\n')
   elif kind=='subsection':
    subn+=1;d.add_paragraph(chr(64+subn)+'. '+part['text'],'Heading 2');latex.append('\\Needspace{3\\baselineskip}\n\\subsection{'+tex_escape(part['text'])+'}')
   elif kind=='table':
    nt+=1;t=T[part['key']];p=d.add_paragraph('TABLE '+roman(nt)+'\n'+t['caption'].upper(),'Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    tb=d.add_table(rows=0,cols=len(t['rows'][0]));tb.autofit=False
    for c,w in zip(tb.columns,t['widths']):c.width=Inches(w)
    for ri,row in enumerate(t['rows']):
     cells=tb.add_row().cells
     for ci,(cell,text) in enumerate(zip(cells,row)):
      cell.width=Inches(t['widths'][ci]);p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2);p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci<2 and part['key'] in ['accuracy','paired'] else WD_ALIGN_PARAGRAPH.CENTER
      r=p.add_run(text);r.font.size=Pt(7.5);r.bold=ri==0
     trpr=tb.rows[-1]._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
     if ri==0:trpr.append(OxmlElement('w:tblHeader'))
    p=d.add_paragraph(t['note'],'Caption')
    for r in p.runs:r.font.size=Pt(7.5)
    ncol=len(t['rows'][0]);total=sum(t['widths']);layout='@{}'+''.join(('>{\\raggedright\\arraybackslash}' if i<2 else '>{\\centering\\arraybackslash}')+'p{'+str(round(w/total*.90,4))+'\\columnwidth}' for i,w in enumerate(t['widths']))+'@{}'
    latex += [r'\begin{table}[!t]',r'\caption{'+tex_escape(t['caption'])+'}',r'\label{tab:'+part['key']+'}',r'\centering',r'\footnotesize',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{'+layout+'}',r'\toprule']
    for i,row in enumerate(t['rows']):
     latex.append(' & '.join((r'\shortstack{Mean\\'+x.split()[-1]+'}' if i==0 and x.startswith('Mean ') else tex_escape(x)) for x in row)+r' \\')
     if i==0:latex.append(r'\midrule')
    latex += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip\begin{minipage}{\columnwidth}\footnotesize '+tex_escape(t['note'])+r'\end{minipage}',r'\end{table}']
   elif kind=='figure':
    nf+=1;p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(str(LATEX/'figures'/(part['key']+'.png')),width=Inches(3.35));d.add_paragraph('Fig. '+str(nf)+'. '+captions[part['key']],'Caption')
    latex += [r'\begin{figure}[!t]',r'\centering',r'\includegraphics[width=\columnwidth]{figures/'+part['key']+'.pdf}',r'\caption{'+tex_escape(captions[part['key']])+'}',r'\label{fig:'+part['key']+'}',r'\end{figure}']
 d.add_paragraph('REFERENCES','Heading 1');latex.append(r'\balance\begin{thebibliography}{99}')
 for n in used:
  ref=source['references'][str(n)].replace('AAAI (preprint record opened)','AAAI').replace('ICLR (preprint record opened)','ICLR')
  p=d.add_paragraph('['+str(mapping[n])+'] '+ref)
  for r in p.runs:r.font.size=Pt(8)
  p.paragraph_format.space_after=Pt(3)
  # Retain source bibliography facts, with stable URLs broken by LaTeX's url package.
  parts=re.split(r'(https?://\S+)',ref);tx=''.join(r'\url{'+a+'}' if a.startswith('http') else tex_escape(a) for a in parts)
  latex.append(r'\bibitem{r'+str(n)+'} '+tx)
 latex += [r'\end{thebibliography}',r'\end{document}']
 d.core_properties.author=source['author'];d.core_properties.title=source['latex_title'];d.core_properties.comments='Revision 9 journal prose and layout. Historical numerical snapshot retained. Canonical PDF is compiled from the accompanying publisher-class LaTeX source.'
 OUT.mkdir(exist_ok=True);d.save(OUT/'ieee_manuscript_en.docx');(LATEX/'main.tex').write_text('\n'.join(latex)+'\n')
 (HERE/'citation_mapping.json').write_text(json.dumps({'original_internal_reference_to_manuscript':mapping,'sources':{str(n):source['references'][str(n)] for n in used}},ensure_ascii=False,indent=2)+'\n')
 (HERE/'table_data.json').write_text(json.dumps(T,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'abstract_words':len(source['abstract'].split()),'tables':nt,'figures':nf,'references':len(used),'docx':str(OUT/'ieee_manuscript_en.docx'),'latex':str(LATEX/'main.tex')}))
if __name__=='__main__':build()
