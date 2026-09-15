# Training & Evaluation Logs

Drop the raw logs from the SFT run here so the reported metrics are traceable
(Gate 2: *loss / performance logs*).

Expected files:

- `train_log.txt` / `trainer_state.json` — per-step loss (TRL writes
  `trainer_state.json` into the `output_dir`; copy it here).
- `eval_metrics.json` — final eval loss / token accuracy.
- `profiling.txt` — the llama.cpp / ADTC profiler output backing the t/s, TTFT,
  and peak-RSS figures in REPORT.md (must match, since organizers re-run it).

The `trainer_state.json` produced by `SFTTrainer` already contains the full
`log_history` (loss per `logging_steps`); it is the simplest single source of
truth to include.

Do **not** hand-edit these — they exist to prove the numbers, so they must be
the real run output.
