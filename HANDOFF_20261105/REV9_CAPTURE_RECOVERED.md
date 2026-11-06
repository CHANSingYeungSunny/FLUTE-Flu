# REV9 live capture (after opportunistic stuck-probe kill)

- UTC: 2026-11-05T15:22:48.780861+00:00
- SSH exit 0; kill commands issued: True
- No job submitted, no job cancelled, no file deleted.

```
PKILL_A=1
PKILL_B=1
PKILL_C=1
PKILL_D=0
PKILL_E=1
KILL_COMMANDS_ISSUED
SHELL_OK
Thu Nov  5 15:22:05 UTC 2026
SQUEUE
739549|miflu_7ch_export|PENDING|0:00
739628|mlflu_p3_s1|PENDING|0:00
737762|legacy_todo_ctl|PENDING|0:00
737759|legacy_todo_ctl|RUNNING|9:28:02
739626|mlflu_p3_driver|RUNNING|2:14:22
Last update in 0 seconds ago
CELLOK_CORE
CELLOK_ALL
NPZ7CH
0
JOB7CH
            739549  gpu_a100 miflu_7c sychan55 PD       0:00      1 (Priority)
Last update in 0 seconds ago
JOB7CH_END
QUOTA
home       USR        23374512   52428800  104857600       8160     none |   104781       0        0        0     none
scratch    USR       329453424  314572800 1073741824          0   9 days |    25734       0        0        0     none
CAPTURE_DONE
PKILL_ROUND2=1
```
