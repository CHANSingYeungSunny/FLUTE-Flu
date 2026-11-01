"""Reproduce author END-of-epoch updates without shifting them by one epoch."""
def author_update_value(epoch_just_completed,base=5e-4):
    e=epoch_just_completed
    return base if e<3 else base*.9**(e-3)

def lr_at_training_epoch(e,base=5e-4):
    # Epoch 1 has no preceding update; epoch e uses update from e-1.
    return base if e==1 else author_update_value(e-1,base)

def r1c_existing_lr_at_epoch(e,base=5e-4):
    return base if e<3 else base*.9**(e-3)

if __name__=='__main__':
    import argparse,pandas as pd
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    pd.DataFrame([dict(training_epoch=e,author_end_update_matched=lr_at_training_epoch(e),
        packaged_R1C_start_update=r1c_existing_lr_at_epoch(e)) for e in range(1,21)]).to_csv(a.out,index=False)
    assert lr_at_training_epoch(4)==5e-4
    assert abs(lr_at_training_epoch(5)-4.5e-4)<1e-12
    assert abs(r1c_existing_lr_at_epoch(4)-4.5e-4)<1e-12
