"""Local shape/API checks with randomly initialized tiny models, NOT forecasts.

No pretrained weights, no GPU measurement, no mechanism contradiction verdict.
"""
import argparse,importlib.util,json,sys,types
from pathlib import Path
import numpy as np
import torch
from common import *

def main(a):
    torch.set_num_threads(2);torch.manual_seed(17)
    root=Path(a.root).resolve();checks={}
    from scheduler_contract import lr_at_training_epoch
    assert lr_at_training_epoch(4)==.0005 and abs(lr_at_training_epoch(5)-.00045)<1e-12
    checks['C2_end_epoch_timeline']='PASS'
    # Imported author/R1B code is exercised without downloading weights.
    sys.path.insert(0,str(root/'code/hpc_compat'))
    sys.path.insert(0,str(root/'inputs/handoff/02_author_repo/code'))
    sys.path.insert(0,str(root/'inputs/handoff/05b_r1b_model'))
    import peft
    if not hasattr(peft,'prepare_model_for_int8_training'):
        def unused(*a,**k):raise RuntimeError('Legacy import shim unexpectedly executed')
        peft.prepare_model_for_int8_training=unused
    from transformers import GPT2Model,GPT2Config,Qwen2Config,Qwen2ForCausalLM
    orig=GPT2Model.from_pretrained
    GPT2Model.from_pretrained=classmethod(lambda cls,*a,**kw:GPT2Model(GPT2Config(n_layer=6,n_embd=768,n_head=12,vocab_size=31,n_positions=1024)))
    from r1b_model import R1BCorrectedMIFlu
    from argparse import Namespace
    cfg=Namespace(backbone='gpt2',patch_size=24,pretrain=1,stride=2,multimodal=1,seq_len=104,pred_len=24,textmodel='gpt2',
        target_modules=['c_attn'],lora_r=4,gpt_layers=6,freeze=1,PEFT=1,d_model=768)
    try:
        model=R1BCorrectedMIFlu(cfg,'cpu',text_embeddings=np.random.default_rng(17).normal(size=(3,768))).eval()
        with torch.no_grad():y=model(torch.randn(1,104,7))
        assert y.shape==(1,24,7) and torch.isfinite(y).all()
        assert len(model.llmmodel.base_model.model.h)==6
        trainable=sum(p.numel() for p in model.parameters() if p.requires_grad)
        assert trainable==1673496,trainable
        checks['C2_author_subclass_shape_K6_LoRA_trainable_inventory']='PASS random initialized GPT2, 3 text tokens; no reproduction score'
    finally:GPT2Model.from_pretrained=orig
    # Qwen: encode, deterministic generate, and pooling API used by the runner.
    qc=Qwen2Config(vocab_size=32,hidden_size=32,intermediate_size=64,num_hidden_layers=1,num_attention_heads=4,
        num_key_value_heads=2,bos_token_id=1,eos_token_id=2,pad_token_id=0)
    qm=Qwen2ForCausalLM(qc).eval();ids=torch.tensor([[1,5,6,7]])
    with torch.no_grad():
        h=qm.base_model(input_ids=ids,use_cache=False,return_dict=True).last_hidden_state
        g=qm.generate(ids,max_new_tokens=2,do_sample=False,use_cache=True,pad_token_id=0)
    assert h.shape==(1,4,32) and g.shape[1]>=5
    checks['Qwen_encoding_and_generation_APIs']='PASS tiny random Qwen2; no pretrained/model-memory claim'
    # DeepSeek's exact pinned model source: instantiate tiny configuration,
    # including its custom AutoModel/causal-LM API and cached generation.
    source=root/'protocol/model_source'
    name='test_pinned_deepseek';pkg=types.ModuleType(name);pkg.__path__=[str(source)];sys.modules[name]=pkg
    loaded={}
    for module,filename in [('configuration_deepseek','configuration_deepseek.py'),('modeling_deepseek','modeling_deepseek.py')]:
        path=source/('deepseek-ai__DeepSeek-V2-Lite-Chat__'+filename)
        spec=importlib.util.spec_from_file_location(name+'.'+module,path);mod=importlib.util.module_from_spec(spec)
        sys.modules[name+'.'+module]=mod;spec.loader.exec_module(mod);loaded[module]=mod
    dc=loaded['configuration_deepseek'].DeepseekV2Config(vocab_size=32,hidden_size=32,intermediate_size=64,
        moe_intermediate_size=16,num_hidden_layers=1,num_attention_heads=4,num_key_value_heads=4,
        kv_lora_rank=8,q_lora_rank=None,qk_nope_head_dim=4,qk_rope_head_dim=4,v_head_dim=4,
        n_routed_experts=4,n_shared_experts=1,num_experts_per_tok=2,first_k_dense_replace=0,
        topk_method='greedy',scoring_func='softmax',norm_topk_prob=False,n_group=1,topk_group=1,routed_scaling_factor=1.0,
        max_position_embeddings=64,bos_token_id=1,eos_token_id=2,pad_token_id=0,rope_scaling=None)
    dc._attn_implementation='eager'
    dm=loaded['modeling_deepseek'].DeepseekV2ForCausalLM(dc).eval()
    with torch.no_grad():
        h=dm.base_model(input_ids=ids,use_cache=False,return_dict=True).last_hidden_state
        g=dm.generate(ids,max_new_tokens=2,do_sample=False,use_cache=True,pad_token_id=0)
    assert h.shape==(1,4,32) and g.shape[1]>=5
    checks['DeepSeek_pinned_custom_MoE_encoding_and_cached_generation_APIs']='PASS tiny random MoE; no full-checkpoint/GPU-memory claim'
    checks['environment']={'torch':torch.__version__,'transformers':__import__('transformers').__version__,'peft':peft.__version__}
    Path(a.out).write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);main(p.parse_args())
