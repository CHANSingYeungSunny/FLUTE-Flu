"""Local-run shim ONLY. The HPC environment has real peft 0.17.1.
PEFT defaults to 0 in the released code, so this branch never executes."""
LoraConfig = get_peft_model = PeftModel = set_peft_model_state_dict = None


def prepare_model_for_int8_training(model, *a, **k):
    return model
