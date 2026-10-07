# F–J reuse decision

- all stage runs valid reuse: **True**
- reruns required: **False**

## Cross-stage spec overlap (blocking the freeze population)

Specs scheduled in MORE THAN ONE of F/G/H/I/J: **36**

| spec (model, enc, fusion, horizon, seed) | stages |
|---|---|
| dlinear, none, identity, 24, 42 | F, G, I, J |
| dlinear, none, identity, 24, 43 | F, G, I, J |
| dlinear, none, identity, 24, 44 | F, G, I, J |
| dlinear, none, identity, 36, 42 | F, J |
| dlinear, none, identity, 36, 43 | F, J |
| dlinear, none, identity, 36, 44 | F, J |
| dlinear, none, identity, 48, 42 | F, J |
| dlinear, none, identity, 48, 43 | F, J |
| dlinear, none, identity, 48, 44 | F, J |
| dlinear, none, identity, 60, 42 | F, G, I, J |
| dlinear, none, identity, 60, 43 | F, G, I, J |
| dlinear, none, identity, 60, 44 | F, G, I, J |
| nlinear, none, identity, 24, 42 | F, I, J |
| nlinear, none, identity, 24, 43 | F, I, J |
| nlinear, none, identity, 24, 44 | F, I, J |
| nlinear, none, identity, 36, 42 | F, J |
| nlinear, none, identity, 36, 43 | F, J |
| nlinear, none, identity, 36, 44 | F, J |
| nlinear, none, identity, 48, 42 | F, J |
| nlinear, none, identity, 48, 43 | F, J |

The controller assigned experiment_stage='full' to stages F, G, H, I AND J, so the SAME (model, horizon, seed) spec was executed in more than one stage (e.g. F and I and J). The selector's eligible population therefore contains 2-5 eligible runs per mandatory Full-Evaluation cell, which violates the v2.9 freeze precondition 'no duplicate mandatory cells'. A lawful champion therefore requires a scientific decision on the champion POPULATION (scope to the pre-registered Stage-F matrix).