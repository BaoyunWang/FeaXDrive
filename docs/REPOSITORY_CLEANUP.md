# Repository cleanup

This cleanup starts from `BaoyunWang/FeaXDrive` main commit
`31669441221cdc80d61a08f7e5eae96a579e479d` and removes 64 superseded files.
The model implementation, tensor names, feature/cache formats, loss functions,
sampling, formal mode overrides and benchmark scoring are unchanged.

## Supported entrypoints

| Task | Shell entry | Python entry |
| --- | --- | --- |
| Hidden-state caching | `scripts/repro/slurm/submit_cache_feaxdrive.slurm` | `navsim/planning/script/run_dataset_caching_multi_node.py` |
| Metric caching | Same cache launcher | `navsim/planning/script/run_metric_caching.py` |
| IL and FA-GRPO training | `scripts/repro/slurm/submit_train_feaxdrive.slurm` | `navsim/planning/script/run_training_feaxdrive_rl.py` |
| Final evaluation | `scripts/repro/slurm/submit_eval_feaxdrive.slurm` | `navsim/planning/script/run_pdm_score_feaxdrive.py` |

Training modes remain `eps`, `dt`, `dyn`, and `fa`. `drivedyn` remains an
evaluation mode. FA-GRPO training uses `pdm_score_feaxdrive_fagrpo.py` and
`feaxdrive_fagrpo_scorer.py`; final evaluation uses `pdm_score.py` and
`pdm_scorer.py`.

## Removed files and retained dependencies

| Group | Count | Reason |
| --- | ---: | --- |
| Historical ReCogDrive agent/planner variants, Orin DiT, projector shims and unused SDF copy | 26 | No retained Python, Hydra or shell caller; main agent and dependency closure retained |
| FeaXDrive planner/projector import shims | 4 | Unused star-import wrappers; current callers import canonical modules directly |
| Old training/evaluation Python entries, Accelerate runner and EMA callback package | 9 | Superseded paths outside the current reproduction chain |
| Old cache and Accelerate shell launchers | 12 | Replaced by the three reproduction launchers; old agent configuration is absent |
| Old FA-GRPO/Orin scoring files and enum copy | 6 | Unused after historical planner removal; current reward and final scorers retained |
| Duplicate dataset/Lightning modules | 3 | No import or configured caller |
| Unused historical Hydra configuration copies | 4 | No defaults or entrypoint references |

The five `navsim/planning/script/plt_*.py` visualization tools still import
`navsim/agents/recogdrive/recogdrive_agent.py`. That agent and its dependency
closure are retained without changing their behavior. Its projection API differs
from the current FeaXDrive agent, so a global import replacement is not valid.
NAVSIM baseline agents, generic training/evaluation, InternVL, VQA tools, data
generation and the original reproduction records are also retained.

The two dataset-generation launchers and CFQA defaults now select the existing
`feaxdrive_v4drive_agent` configuration instead of the absent `recogdrive_agent`
configuration. This repairs configuration lookup; it does not establish that the
optional data-generation pipelines run successfully end to end.

The training launcher's syntax check no longer lists the two removed legacy FA
scorer files. Duplicate `.gitignore` rules are removed, and the README clone URL
points to this repository. Shell scripts and Slurm workers use LF line endings
via `.gitattributes`, including on Windows checkouts.

## Checkpoint boundary

The current agent loads a tensor `state_dict` and strips the `agent.` prefix.
The FA-GRPO planner strips `agent.action_head.` for its reference policy. Neither
matching operation uses a historical module filename. The current Lightning
modules do not call `save_hyperparameters`; their checkpoint hooks filter tensor
state. Current model modules, classes and parameter names are preserved.

This does not guarantee compatibility with arbitrary external whole-object
pickle files or old Hydra snapshots naming removed targets. Such artifacts were
not supplied. Historical source remains available at the base Git commit.

## Validation

Run the dependency-free structural checks from the repository root:

```bash
python -m unittest discover -s tests -v
bash -n scripts/repro/slurm/submit_cache_feaxdrive.slurm
bash -n scripts/repro/slurm/submit_train_feaxdrive.slurm
bash -n scripts/repro/slurm/submit_eval_feaxdrive.slurm
git diff --check
```

The structural suite checks NAVSIM Python import paths, local Hydra target
modules and symbols, literal agent configuration selections, and Python paths
referenced by shell launchers. These are static checks. No training, cache
generation, GPU inference, checkpoint load or benchmark evaluation is claimed.
