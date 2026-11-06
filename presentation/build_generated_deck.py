#!/usr/bin/env python3
"""Deterministic editable python-pptx deck built from deck_spec.json.
Usage: python presentation/build_deck.py [--out repeat.pptx]
The spec supplies every scientific value. make_deck_spec.py regenerates it from frozen CSVs.
"""
from pathlib import Path
import json,zipfile,io,argparse,datetime,hashlib,re
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE,XL_LABEL_POSITION,XL_LEGEND_POSITION,XL_TICK_MARK
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
INK='182A3B';NAVY='183F59';TEAL='087F83';ORANGE='BA5B2B';MUTED='536678';PALE='EAF2F4';GRAY='DEE4E9';WHITE='FFFFFF'
def rgb(s):return RGBColor.from_string(s)
def text(sl,x,y,w,h,content,size=22,bold=False,color=INK,align=None):
 box=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame;tf.clear();tf.word_wrap=True
 tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(str(content).split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line
  p.font.name='Liberation Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color);p.space_after=Pt(6)
  if align is not None:p.alignment=align
 return box

def rect(sl,x,y,w,h,color,line=None):
 sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=rgb(color)
 for eff in sh._element.xpath('./p:style/a:effectRef'):eff.set('idx','0')
 if line:sh.line.color.rgb=rgb(line)
 else:sh.line.fill.background()
 return sh

def picture(sl,path,x,y,w,h):
 with Image.open(path) as im:iw,ih=im.size
 sc=min(w/iw,h/ih);ww,hh=iw*sc,ih*sc
 return sl.shapes.add_picture(str(path),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))

def table(sl,rows,x,y,w,h,widths=None,fs=22):
 sh=sl.shapes.add_table(len(rows),len(rows[0]),Inches(x),Inches(y),Inches(w),Inches(h));tb=sh.table
 if widths:
  for c,v in zip(tb.columns,widths):c.width=Inches(v)
 for i,row in enumerate(rows):
  for j,value in enumerate(row):
   cell=tb.cell(i,j);cell.text=str(value);cell.margin_left=Inches(.14);cell.margin_right=Inches(.12);cell.margin_top=Inches(.10);cell.margin_bottom=Inches(.07);cell.vertical_anchor=MSO_ANCHOR.MIDDLE
   cell.fill.solid();cell.fill.fore_color.rgb=rgb(NAVY if i==0 else (WHITE if i%2 else PALE))
   for p in cell.text_frame.paragraphs:
    p.font.name='Liberation Sans';p.font.size=Pt(fs-2 if i==0 else fs);p.font.bold=(i==0);p.font.color.rgb=rgb(WHITE if i==0 else INK)
 return sh

def chart(sl,ctype,categories,series,x,y,w,h):
 data=CategoryChartData();data.categories=categories
 for name,values in series:data.add_series(name,values)
 ch=sl.shapes.add_chart(ctype,Inches(x),Inches(y),Inches(w),Inches(h),data).chart
 ch.has_title=False;ch.has_legend=len(series)>1
 if ch.has_legend:ch.legend.position=XL_LEGEND_POSITION.BOTTOM;ch.legend.include_in_layout=False;ch.legend.font.size=Pt(16)
 ch.chart_style=10
 for axis in [ch.category_axis,ch.value_axis]:
  axis.tick_labels.font.name='Liberation Sans';axis.tick_labels.font.size=Pt(17);axis.tick_labels.font.color.rgb=rgb(MUTED)
  axis.major_tick_mark=XL_TICK_MARK.NONE;axis.minor_tick_mark=XL_TICK_MARK.NONE
 ch.value_axis.minimum_scale=0;ch.value_axis.maximum_scale=2.2;ch.value_axis.major_unit=.5
 ch.value_axis.has_major_gridlines=True;ch.value_axis.major_gridlines.format.line.color.rgb=rgb(GRAY)
 plot=ch.plots[0];plot.has_data_labels=True
 plot.data_labels.position=XL_LABEL_POSITION.OUTSIDE_END;plot.data_labels.number_format='0.0000';plot.data_labels.font.size=Pt(15);plot.data_labels.font.name='Liberation Sans'
 for i,ser in enumerate(ch.series):
  ser.format.fill.solid();ser.format.fill.fore_color.rgb=rgb([TEAL,GRAY][i%2]);ser.format.line.fill.background()
 return ch

def normalise_package(raw):
 """Normalise outer OOXML and embedded chart workbooks, including core dates."""
 result=io.BytesIO()
 with zipfile.ZipFile(io.BytesIO(raw)) as zin,zipfile.ZipFile(result,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zout:
  for name in sorted(zin.namelist()):
   data=zin.read(name)
   if name.endswith('.xlsx'):data=normalise_package(data)
   elif name=='docProps/core.xml':
    data=re.sub(rb'(<dcterms:(?:created|modified)[^>]*>)[^<]+',rb'\g<1>2026-11-04T00:00:00Z',data)
   info=zipfile.ZipInfo(name,(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o600<<16;zout.writestr(info,data)
 return result.getvalue()

def build(spec_path,out):
 spec=json.loads(spec_path.read_text())
 for rel,digest in spec['source_csv_sha256'].items():
  if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=digest:raise ValueError('CSV changed; regenerate spec: '+rel)
 for name,digest in spec['assets_sha256'].items():
  if hashlib.sha256((ROOT/'01_最终报告/figures'/name).read_bytes()).hexdigest()!=digest:raise ValueError('Figure changed: '+name)
 assert len(spec['slides'])==13 and sum(q['duration_seconds'] for q in spec['slides'])==300
 prs=Presentation();prs.slide_width=Inches(spec['slide_width_inches']);prs.slide_height=Inches(spec['slide_height_inches'])
 cp=prs.core_properties;cp.title=spec['title'];cp.subject=spec['subtitle'];cp.author=spec['author'];cp.last_modified_by=spec['author'];cp.revision=3
 fixed=datetime.datetime(2026,11,4,0,0,0,tzinfo=datetime.timezone.utc);cp.created=fixed;cp.modified=fixed
 for q in spec['slides']:
  sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=rgb(WHITE)
  layout=q['layout'];num=q['id']
  if layout!='cover':
   rect(sl,.65,.46,.09,.55,TEAL);text(sl,.94,.42,11.5,.95,q['title'],30,True)
  text(sl,.8,7.10,10.5,.19,'CHAN Sing Yeung   •   Experimental snapshot 3 November 2026',10,color=MUTED)
  text(sl,12.05,7.04,.55,.24,f'{num:02d}/13',10,color=MUTED,align=PP_ALIGN.RIGHT)
  if layout=='cover':
   rect(sl,.83,.87,.12,1.7,TEAL)
   text(sl,1.17,.86,11.1,1.75,'Re-evaluating Multimodal LLMs\nfor Influenza Forecasting',37,True,NAVY)
   text(sl,1.19,3.05,10.95,1.45,spec['subtitle'],27,color=INK)
   text(sl,1.19,5.25,10.9,.65,spec['author'],25,True)
   text(sl,1.19,6.02,10.9,.55,'Final Year Project   •   Progress Presentation',20,color=MUTED)
  elif layout=='axes':
   rows=[['#','Dimension','Evidence','Coverage']]+q['axes'];table(sl,rows,.85,1.7,11.65,3.9,[.8,3.05,5.4,2.4],22)
   text(sl,.9,6.06,11.4,.6,'One shared study, with explicitly different analysis subsets',23,color=TEAL)
  elif layout=='protocols':
   table(sl,q['rows'],.85,1.8,11.65,3.55,[3.05,4.3,4.3],23)
   text(sl,.9,5.75,11.5,.62,'28 retained arms = 13 conventional + 4 LLM-based + 11 frozen encoders',23,True,TEAL)
   text(sl,.9,6.48,11.4,.38,q['footer'],15,color=MUTED)
  elif layout=='reproduction':
   ch=chart(sl,XL_CHART_TYPE.COLUMN_CLUSTERED,['L'+x for x in q['horizons']],[('Reproduction',q['ours']),('Paper table',q['paper'])],.72,1.65,8.0,4.8)
   for point in ch.series[1].points:point.data_label.position=XL_LABEL_POSITION.INSIDE_END
   text(sl,9.0,1.8,3.15,.45,'MSE mean',22,True);text(sl,9.0,2.35,3.15,.55,f"{q['mse_mean'][0]:.4f} / {q['mse_mean'][1]:.4f}",26,True,NAVY)
   text(sl,9.0,3.03,3.15,.6,f"+{(q['mse_mean'][0]/q['mse_mean'][1]-1)*100:.1f}%\nTwo lower, two higher",21,color=MUTED)
   text(sl,9.0,4.23,3.15,.45,'MAE mean',22,True);text(sl,9.0,4.78,3.15,.55,f"{q['mae_mean'][0]:.4f} / {q['mae_mean'][1]:.4f}",26,True,NAVY)
   text(sl,9.0,5.45,3.15,.75,f"+{(q['mae_mean'][0]/q['mae_mean'][1]-1)*100:.1f}%\nOne lower, three higher",21,color=MUTED)
   text(sl,.9,6.56,11.5,.28,'Source: reproduction CSV. Raw ten-seed runs are not independently rescored here.',14,color=MUTED)
  elif layout=='accuracy':
   leaders=q['leaders'];rev=leaders[::-1]
   ch=chart(sl,XL_CHART_TYPE.BAR_CLUSTERED,[v['name'] for v in rev],[('Mean MSE',[v['mse'] for v in rev])],.8,1.67,11.55,4.35)
   for point,color in zip(ch.series[0].points,[ORANGE,NAVY,TEAL]):point.format.fill.solid();point.format.fill.fore_color.rgb=rgb(color)
   text(sl,.95,6.05,11.4,.6,'Mean MAE:  '+ '     '.join(f"{v['name']} {v['mae']:.4f}" for v in leaders),21)
   text(sl,.95,6.6,11.4,.28,'Lower is better. Leading three shown; the full 28-model table is in the internal report.',14,color=MUTED)
  elif layout=='peak_metrics':
   text(sl,.9,1.5,11.5,.7,'Joint screen: PTE ≤ 1 week AND PIE ≤ 25%',28,True,TEAL)
   rows=[['Model','Mean PTE (weeks)','Mean PIE (%)','Joint passes']]+[[v['name'],f"{v['pte']:.3f}",f"{v['pie']:.3f}",f"{v['passes']}/16"] for v in q['leaders']]
   table(sl,rows,.85,2.5,11.65,3.05,[2.7,3.05,2.95,2.95],25)
   text(sl,.9,5.94,11.5,.65,'MIFlu has lower mean timing error. NLinear has lower mean height error.',22)
   text(sl,.9,6.55,11.5,.3,q['footer'],15,color=MUTED)
  elif layout=='peak_grid':
   x0=2.6;cw=.46;gap=.07;group=4*(cw+gap)
   for gi,L in enumerate([24,36,48,60]):
    text(sl,x0+gi*group,1.65,group-.07,.4,f'L{L}',22,True,NAVY,PP_ALIGN.CENTER)
    for step in range(4):text(sl,x0+(gi*4+step)*(cw+gap),2.17,cw,.25,f's{step}',14,color=MUTED,align=PP_ALIGN.CENTER)
   for i,row in enumerate(q['grid']):
    y=2.77+i*.88;text(sl,.87,y+.08,1.65,.45,row['name'],24,True)
    for j,cell in enumerate(row['cells']):
     xx=x0+j*(cw+gap);rect(sl,xx,y,cw,.58,TEAL if cell['pass'] else GRAY)
     text(sl,xx,y+.16,cw,.23,'Yes' if cell['pass'] else '–',12,color=WHITE if cell['pass'] else MUTED,align=PP_ALIGN.CENTER)
    text(sl,11.43,y+.06,1.05,.48,f"{row['passes']}/16",24,True,NAVY,PP_ALIGN.RIGHT)
   text(sl,.95,5.63,11.4,.5,'MSE order:  '+' < '.join(q['orders']['mse']),23)
   text(sl,.95,6.19,11.4,.5,'PIE order:    '+' < '.join(q['orders']['pie']),23,color=TEAL)
   text(sl,.95,6.73,11.4,.23,'Each green cell passes both thresholds. s0–s3 are forecast weeks 1–4.',13,color=MUTED)
  elif layout=='pareto':
   picture(sl,ROOT/'01_最终报告/figures'/q['figure'],.72,1.48,8.45,5.15)
   text(sl,9.4,1.75,2.8,.7,f"{q['parameter_ratio']:.0f}×",46,True,NAVY)
   text(sl,9.4,2.58,2.9,.8,'PatchTST / NLinear\nparameter count',21)
   text(sl,9.4,3.72,2.9,.7,f"{q['mse_reduction_pct']:.1f}%",42,True,TEAL)
   text(sl,9.4,4.55,2.9,.7,'lower observed MSE',21)
   text(sl,9.4,5.55,2.9,.7,f"11 exported arms\nR² = {q['r2']:.4f}",20,color=MUTED)
   text(sl,.9,6.68,11.5,.24,'Subset frontier. MIFlu and encoders excluded. Parameter count is a size proxy, not measured runtime.',13,color=MUTED)
  elif layout=='statistics':
   text(sl,1.0,1.7,5.2,.5,'Before correction',24,True);text(sl,7.05,1.7,5.2,.5,'After proper Holm',24,True)
   text(sl,1.0,2.38,5.2,.9,f"{q['raw_count']} / {q['pair_count']}",54,True,NAVY)
   text(sl,7.05,2.38,5.2,.9,f"{q['adjusted_count']} / {q['pair_count']}",54,True,ORANGE)
   text(sl,1.0,3.48,11.3,.55,'Pairs with p < 0.05 in the declared family',22,color=MUTED)
   text(sl,1.0,4.35,11.3,.62,f"NLinear–PatchTST  p ≈ {q['frontier_adjusted_p']:.4f}",31,True,TEAL)
   text(sl,1.0,5.28,11.3,.65,'Observed gain remains. Equivalence is unproven.',24)
   text(sl,1.0,6.2,11.3,.7,f"17 models including MIFlu. DLinear and encoders excluded.\nMinimum adjusted p ≈ {q['minimum_adjusted_p']:.4f}; exact-test resolution and dependence limit inference.",17,color=MUTED)
  elif layout=='encoders':
   text(sl,.9,1.57,11.5,.6,'Frozen encoder + trained linear readout',29,True)
   text(sl,.9,2.65,11.5,.9,f"MSE {q['mse_min']:.4f}–{q['mse_max']:.4f}",43,True,NAVY)
   text(sl,.9,3.85,11.5,.7,f"All 11 exceed decision tree MSE {q['tree_mse']:.4f}",28)
   text(sl,.9,4.9,11.5,.7,'Each encoder passes 0/16 joint cells',29,True,TEAL)
   text(sl,.9,6.04,11.5,.75,'Scope: these feature/readout configurations. Generation, prompting, fine-tuning and numerical foundation models remain untested.',21,color=MUTED)
  elif layout=='text_path':
   text(sl,.9,1.54,6.4,.4,'Default author_faithful path',22,True)
   rect(sl,.9,2.25,3.0,.8,PALE);text(sl,1.05,2.46,2.7,.4,'Time positions',24,True,NAVY)
   rect(sl,4.2,2.25,3.05,.8,GRAY);text(sl,4.35,2.46,2.75,.4,'Later text',22,True)
   text(sl,.95,3.38,6.2,1.08,'Causal attention prevents time positions\nfrom reading later text',23)
   rect(sl,.9,4.88,3.0,.8,NAVY);text(sl,1.05,5.10,2.7,.37,'Forecast head',24,True,WHITE)
   text(sl,4.2,4.94,3.12,.9,'Head reads time\npositions only',22,color=MUTED)
   text(sl,8.1,1.8,4.15,.5,'Evidence status',24,True)
   text(sl,8.1,2.62,4.15,1.1,'Static inspection suggests\ntext invariance',23)
   text(sl,8.1,4.05,4.15,1.1,'Archived model assertions:\nnot executed',23,True,ORANGE)
   text(sl,8.1,5.43,4.15,.9,f"Ablation {q['ablation_done']}/{q['ablation_planned']}\nowner-reported, not aggregated",21,color=MUTED)
   text(sl,.95,6.58,11.3,.28,'Deterministic evaluation-path inference. Other fusion paths and training randomness require separate tests.',14,color=MUTED)
  elif layout=='next_steps':
   lines=[('1','Recover provenance and execute model checks'),('2','Validate across origins and regions'),('3','Add stronger numerical foundation controls')]
   for i,(n,line) in enumerate(lines):
    yy=1.7+i*1.03;text(sl,.95,yy,.6,.5,n,28,True,TEAL);text(sl,1.75,yy,10.65,.68,line,28)
   text(sl,.95,5.14,11.3,.55,'Optional O2: validation-only peak-height recalibration',25,True,NAVY)
   text(sl,.95,5.94,11.3,.77,'0 new GPU training if suitable validation/test predictions exist. Validation exports remain unestablished; CPU time and money are unmeasured.',21,color=MUTED)
  elif layout=='closing':
   text(sl,.95,1.67,11.4,.73,'MIFlu: lowest observed average MSE',30,True,NAVY)
   text(sl,.95,2.7,11.4,1.05,'NLinear: lower peak-height error at low parameter count',28,True,TEAL)
   text(sl,.95,3.94,11.4,.72,'Corrected tests: no familywise rejection at this resolution',26)
   text(sl,.95,5.12,11.4,.92,'Proposed supervision decision: O1, with rolling-origin and regional validation before a new mechanism',27,True)
  else:raise ValueError(layout)
  notes='SPOKEN SCRIPT (planned '+str(q['duration_seconds'])+' seconds)\n'+q['speaker_notes']+'\n\nPREPARATION ONLY / 中文理解\n'+q['preparation_zh']+'\n\nIF ASKED / NOT IN THE FIVE-MINUTE SCRIPT\nQ: '+q['follow_up_question']+'\nA: '+q['follow_up_answer']+'\n\nSOURCES\n'+'\n'.join(q['sources'])+'\n\nActual human delivery and native PowerPoint inspection: not executed.'
  sl.notes_slide.notes_text_frame.text=notes
 raw=io.BytesIO();prs.save(raw);raw.seek(0);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_bytes(normalise_package(raw.getvalue()))
 print(out.name,hashlib.sha256(out.read_bytes()).hexdigest());return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--spec',type=Path,default=HERE/'deck_spec.json');ap.add_argument('--out',type=Path,default=HERE/'Generated_Alternative.pptx');a=ap.parse_args();build(a.spec,a.out)
