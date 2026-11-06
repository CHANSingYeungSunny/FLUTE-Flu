#!/usr/bin/env python3
"""Regenerate the four-axis deck specification from frozen CSVs and authored notes."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from verify_snapshot import facts

def make():
 a,t,r=facts();p=pd.read_csv(ROOT/'02_数字表格/BENCH_PTE_PIE_BY_STEP.csv');v=pd.read_csv(ROOT/'02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv')
 assert a['pair_raw_rank']==117 and a['corrected_significant_pairs']==0
 spec={'title':'Re-evaluating Multimodal LLMs for Influenza Forecasting',
       'subtitle':'A 28-Model Benchmark of Accuracy, Peak Skill, Parameter Efficiency and Statistical Evidence',
       'author':'CHAN Sing Yeung','snapshot_date':'2026-11-03','revision':'3',
       'slide_width_inches':13.333333333333334,'slide_height_inches':7.5,'planned_duration_seconds':300,
       'spoken_duration_status':'Planned 5:00; actual delivery and native PowerPoint inspection not executed',
       'source_csv_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (ROOT/'02_数字表格').glob('*.csv')},
       'assets_sha256':{'fig_pareto_presentation.png':hashlib.sha256((ROOT/'01_最终报告/figures/fig_pareto_presentation.png').read_bytes()).hexdigest()},'slides':[]}
 def slide(title,layout,duration,spoken,zh,question,answer,refs,**more):
  q={'id':len(spec['slides'])+1,'title':title,'layout':layout,'duration_seconds':duration,
     'speaker_notes':spoken,'preparation_zh':zh,'follow_up_question':question,'follow_up_answer':answer,
     'sources':refs,'figure':None};q.update(more);spec['slides'].append(q)
 mse='02_数字表格/BENCH_MSE_BY_MODEL_L.csv';peak='02_数字表格/BENCH_PTE_PIE_BY_STEP.csv';repro='02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv';eff='02_数字表格/BENCH_EFFICIENCY.csv';paired='02_数字表格/BENCH_PAIRED_TESTS.csv'
 slide(spec['title'],'cover',15,
  'My project re-evaluates multimodal LLMs for influenza forecasting. I examine MIFlu and compare twenty-eight implementations. The question is how model choice changes when average accuracy, peak errors, model size and statistical evidence are considered together.',
  '开场先说明研究问题：不是只复现一个分数，而是重新检查选模依据。标题中的 28 指整个比较名单，不表示四个维度都覆盖 28 个模型。副标题对应后面四条评价主线。',
  'What is the contribution beyond reproduction?',
  'A four-axis re-evaluation with an explicit statistical correction and implementation/provenance limits. Broad negative-LLM findings already exist; this is the specific influenza audit, not a first-ever claim.',[mse,peak,'audit/CLAIM_AUDIT.md'])
 slide('Four evaluation axes ask different questions','axes',25,
  'I use four evaluation axes. Accuracy measures overall prediction error. Peak skill measures timing and height. Parameter efficiency compares model size with error. Statistical evidence asks what differences the test design can support. Their coverage differs: twenty-eight, twenty-eight, eleven and seventeen models. Those denominators must stay separate.',
  '请按四个问题解释，不要说成四个独立数据集。参数图只有 11 个有导出参数量的模型；配对检验只有 17 个非编码器模型。覆盖范围不同，是导师很可能追问的地方。',
  'Why do the denominators differ?',
  'The source exports have different membership. Accuracy/peak cover 28 retained arms. Parameter data cover 11, excluding MIFlu and encoders. Paired comparisons cover 17 including MIFlu, excluding DLinear and encoders.',[mse,peak,eff,paired],
  axes=[['1','Accuracy','MSE and MAE','28 models'],['2','Peak skill','Timing, height and joint screen','28 models'],['3','Parameter efficiency','MSE versus parameter count','11 models'],['4','Statistical evidence','Paired tests with proper Holm','17 models']])
 slide('Reproduction and benchmarking use separate run sets','protocols',25,
  'The reproduction uses ten seeds to compare with the reported paper table. The wider benchmark uses three seeds under shared scored windows. Its roster contains thirteen conventional models, four LLM-based models and eleven frozen encoders. Both protocols use train-only scaling and local validation selection. Their MIFlu means answer different questions.',
  '1.4995 与 1.5574 来自不同种子集合，不能当成同一次实验的前后变化。三个种子是算力取舍，不是期刊统一规定。窗口沿用完整批量裁剪，所有比较模型使用相同计分样本。上游缺陷归因仍待固定版本核实。',
  'Why three seeds rather than ten for every model?',
  'The retained benchmark is 28 × 4 × 3 = 336 cells. Three reflects the compute budget. More seeds can improve uncertainty; no adequate-power or no-benefit claim follows.',[repro,mse,'05_程序代码/eval_windows.py'],
  rows=[['Purpose','Reproduction','Benchmark'],['Seeds','2021–2030 (10)','42 / 43 / 44 (3)'],['MIFlu mean MSE','1.4995','1.5574'],['Scored windows','160 / 144 / 144 / 128','Same windows across arms']],
  footer='966 rows, 7 channels. Chronological split 676 / 97 / 193. Full-window sensitivity remains open.')
 rows=[x for x in a['reproduction'] if x['L']!='4L-mean']
 slide('Reproduction differs by horizon and error measure','reproduction',30,
  'The reproduction’s mean MSE is four point five percent higher than the paper table. It is lower at horizons twenty-four and thirty-six, but higher at forty-eight and sixty. MAE is seven point nine percent higher overall, with only one lower horizon. The two error measures need separate explanations, and the causes of the gaps remain unresolved.',
  '左图只画复现 MSE 的四个跨度，不要把基准预测曲线误说成十种子复现轨迹。右侧区分 MSE 两低两高与 MAE 一低三高。检查点、种子和配置可能解释差异，但未进行受控因果拆分，不能把原因说死。',
  'Does the figure prove an exact reproduction?',
  'No. The plotted means are verified against the supplied reproduction CSV. Raw ten-seed predictions/logs and a pinned author revision remain unavailable for independent complete reproduction.',[repro,'audit/NUMERICAL_AUDIT.md'],
  horizons=[str(x['L']) for x in rows],ours=[x['our_MSE'] for x in rows],paper=[x['paper_MSE'] for x in rows],
  mse_mean=[1.4995,1.4355],mae_mean=[0.8043,0.7452])
 leaders=[{'key':key,'name':{'miflu':'MIFlu','patchtst':'PatchTST','nlinear':'NLinear'}[key],
           'mse':float(r.loc[key,'mse']),'mae':float(r.loc[key,'mae']),'pte':float(r.loc[key,'PTE']),'pie':float(r.loc[key,'PIE']),'passes':int(r.loc[key,'passes'])}
          for key in ['miflu','patchtst','nlinear']]
 slide('MIFlu leads the observed average-error ranking','accuracy',25,
  'MIFlu has the lowest observed mean MSE, about one point five five seven four. PatchTST and NLinear follow in that order, and MAE gives the same leading three. This comparison concerns project implementations on one national split. It does not show that the multimodal component caused MIFlu’s advantage.',
  '本页属于维度一。横向柱长是平均 MSE，越短越好；旁边 MAE 也是越低越好。只展示前三名是为了汇报可读性，内部报告保留完整 28 模型表。模型名称表示项目实现，未逐一证明与每篇原论文完全一致。',
  'Are these the original algorithms with verified identical implementation?',
  'They are project implementations/adaptations. Their exact equivalence to each published comparator has not been independently established. The ranking alone cannot prove method fidelity.',[mse],leaders=leaders)
 slide('Peak skill separates timing from height','peak_metrics',25,
  'Peak errors use ILITOTAL in patient counts, rather than the seven-channel standardised loss. The joint screen requires timing error within one week and height error within twenty-five percent in the same aggregated cell. MIFlu and NLinear each pass four of sixteen cells. These are horizon–lead combinations, not independent seasons.',
  '本页属于维度二。PTE 是周误差，PIE 是峰高相对误差，不能把 PIE 叫概率校准。文献支持分别采用一周及 25% 容差；本项目把两者联合应用于平均误差，属于工程筛选，不是临床部署认证。',
  'Is 4/16 an estimated 25% season-success probability?',
  'No. There are four horizons times four fixed leads. The errors are aggregated within each cell before applying thresholds. Event-level success probabilities require a different analysis.',[peak,'audit/LITERATURE_REVIEW.md source [2]'],leaders=leaders,
  tolerances={'pte_wk':1,'pie_pct':25},footer='Project joint mean-error screen. Each denominator is 4 horizons × 4 leads.')
 grid=[]
 for q in leaders:
  cells=[]
  for L in [24,36,48,60]:
   for step in range(4):
    x=p[(p.model==q['key'])&(p.L==L)&(p.step==step)].iloc[0]
    cells.append({'L':L,'step':step,'pass':bool(x.PTE_wk<=1 and x.PIE_pct<=25),'pte':float(x.PTE_wk),'pie':float(x.PIE_pct)})
  grid.append({'name':q['name'],'passes':q['passes'],'cells':cells})
 slide('Equal pass counts hide different passing cells','peak_grid',25,
  'The grid shows different passing locations. NLinear passes the first lead at all four horizons. MIFlu passes three first-lead cells and the second lead at horizon forty-eight. Across all cells, NLinear has lower peak-height error, while MIFlu has better timing. The leading-three ordering is inverted at both ends between MSE and peak-height error.',
  '每行 16 格，分成 L24、L36、L48、L60 四组，每组 s0–s3。绿色表示同一格两项都通过。请先指出绿色位置，再解释同为 4/16 不代表同样表现。所谓 inverted at both ends 是具体两种排序不同，不是证明统计独立或全局脱钩。',
  'Does this demonstrate peak-skill decoupling?',
  'It demonstrates local objective-dependent rankings and a timing–height trade-off. Overall correlations remain +0.736 for MSE–PIE and −0.429 for MSE–pass count. Independence or universal decoupling is not established.',[peak,mse],grid=grid,
  orders={'mse':['MIFlu','PatchTST','NLinear'],'pie':['NLinear','MIFlu','PatchTST']})
 slide('The parameter frontier exposes a size–error trade-off','pareto',25,
  'The parameter frontier covers eleven exported arms. NLinear is smaller, while PatchTST has lower MSE. PatchTST uses about two hundred and eleven times as many parameters for eleven point two percent lower observed MSE. The size fit explains only about two percent of observed MSE variation. Parameter count remains a size proxy, with runtime unmeasured.',
  '本页属于维度三。越靠左参数越少，越靠下 MSE 越低。互不支配的点构成子集前沿。MIFlu 与冻结编码器缺少这一参数导出，所以不能声称是 28 模型全局前沿。R² 低不等于容量无作用，也不能把观测增益叫噪声。',
  'Why is MIFlu absent, despite the study title mentioning LLMs?',
  'Its parameter count is not in the supplied efficiency export. Missing values remain missing. The full benchmark has 28 arms, but this measured subset has 11.',[eff,mse],figure='fig_pareto_presentation.png',
  parameter_ratio=531878/2520,mse_reduction_pct=(float(r.loc['nlinear','mse'])-float(r.loc['patchtst','mse']))/float(r.loc['nlinear','mse'])*100,
  r2=a['r2'],slope=a['slope'])
 slide('Correct Holm supports no familywise rejection','statistics',30,
  'The paired family has seventeen models, including MIFlu. Proper Holm rejects zero of one hundred and thirty-six pairs. The NLinear–PatchTST p-value is zero point one one seven two. Coarse exact-test resolution already blocks the first Holm threshold, and dependent cells add concern. The observed gain remains. Equivalence is unproven.',
  '本页属于维度四。源导出 Holm 列方向错误，必须从原始 p 重算。17 模型包括 MIFlu，排除 DLinear 与 11 编码器。0/136 是当前检验设计与分辨率的限制，不能解释成所有模型一样好。精确网格恢复与六位小数导出直接重算均在显示精度上得到 0.1172。',
  'Why is the minimum adjusted p already above 0.05?',
  'At n=12 the documented two-sided exact raw-p floor is 2/4096. Multiplying by the first Holm factor 136 gives about 0.0664. This family cannot pass the first threshold at that resolution. Dependence is a separate validity concern.',[paired,'audit/HOLM_RECOMPUTATION.csv'],raw_count=128,adjusted_count=0,pair_count=136,model_count=17,
  frontier_adjusted_p=float(a['pair']['p_holm_grid_recovered']),minimum_adjusted_p=float(t.p_holm_grid_recovered.min()))
 enc=r[r.family=='llm_encoder']
 slide('Frozen-feature encoders underperform in this protocol','encoders',20,
  'Eleven frozen encoders with a linear readout all perform worse than the decision tree and pass zero joint cells. This is a negative result for the tested feature pipeline. Generation, prompting, fine-tuning and numerical time-series foundation models remain outside this test.',
  '这部分解释模型家族结果：冻结编码器加线性头，与直接生成、提示、微调、Chronos 等数值时序预训练并不是同一测试。可以报告所测配置表现差，但不能从结果单独判定是语义不迁移、容量不足还是读出选择造成。',
  'Does this prove that all LLM forecasting is ineffective?',
  'No. It is restricted to the frozen-feature/readout protocol. Broader LLM-based and numerical foundation methods require their own faithful comparisons and controls.',[mse,peak],mse_min=float(enc.mse.min()),mse_max=float(enc.mse.max()),tree_mse=float(r.loc['decision_tree','mse']))
 slide('The text pathway needs a controlled runtime check','text_path',20,
  'In the inspected default path, time tokens precede text and causal attention blocks later information. The head reads time positions. This supports a static text-invariance hypothesis. The supplied model assertions remain unexecuted. Ablation is owner-reported at twenty-seven of sixty, without an aggregated scientific result.',
  '静态代码可以解释“为什么可能没有文本作用”，但不能冒充模型运行结果。默认 author_faithful 路径只支持确定性评估前向推断；其他融合路径和独立训练随机性需另测。27/60 是用户快照，不是本次连接 HPC 的实时进度。',
  'Are the archived tests sufficient to claim bitwise equality?',
  'Their assertions are statically inspectable, but the three named model checks must actually run without skips in the pinned environment. Exact files and commands are in audit/NO_TEXT_VERIFICATION.md. No passing archived-suite claim is made.',
  ['05_程序代码/miflu_model.py','tests_archive/test_miflu_ablations.py','audit/NO_TEXT_VERIFICATION.md'],ablation_done=27,ablation_planned=60)
 slide('O1 prioritises independent validation','next_steps',20,
  'My default is O1: strengthen the evidence through model checks, rolling origins, regions and stronger numerical controls. Optional O2 is validation-only peak-height recalibration. It needs no new GPU training if suitable predictions already exist, but those validation exports are not established here.',
  '先补证据，再决定是否加机制。O2 只是可选项，不是已经实现的新方法。其零 GPU 训练成本有前提：已有可审计验证及测试预测。CPU 时间、费用未测量；几个工作日属于工程估计。任何校准都不能在当前测试季拟合。',
  'Would a small new method make the paper submission-ready?',
  'No. A recalibrator cannot replace provenance, external validation or modern controls. O1 is the accepted default, O2 is conditional, and the present journal draft remains not submission-ready.',
  ['audit/INNOVATION_DECISION.md','audit/REPO_AUDIT.md','audit/GRADE_READINESS.md'])
 slide('Model choice depends on the evaluation objective','closing',15,
  'MIFlu leads average MSE. NLinear offers lower peak-height error at low exported parameter count. Corrected tests establish no familywise rejection. I propose validating these trade-offs across origins and regions before adding a mechanism. That is the next supervision decision.',
  '结尾用可支持的结论回答开场问题，并给导师一个具体决策：是否按 O1 优先做区域及滚动原点验证。不要用“LLM 无用”或“已经可部署”收尾。学校资料还要求在截止前完成向导师与评阅人的汇报及提交。',
  'What can you confidently defend today?',
  'The exported arithmetic, bounded local trade-offs and proper Holm correction. The internal report Q01–Q25 supplies the explanations and evidence locators. Deployment value and complete independent reproduction remain unestablished.',
  [mse,peak,paired,'Requirements_ProjectProgressReport_2627A (1).pdf'])
 assert sum(x['duration_seconds'] for x in spec['slides'])==300 and len(spec['slides'])==13
 spec['spoken_script_whitespace_words']=sum(len(x['speaker_notes'].split()) for x in spec['slides'])
 (HERE/'deck_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
 print('Spec:',len(spec['slides']),'slides,',sum(x['duration_seconds'] for x in spec['slides']),'planned seconds,',spec['spoken_script_whitespace_words'],'whitespace-delimited spoken-script words')
 return spec
if __name__=='__main__':make()
