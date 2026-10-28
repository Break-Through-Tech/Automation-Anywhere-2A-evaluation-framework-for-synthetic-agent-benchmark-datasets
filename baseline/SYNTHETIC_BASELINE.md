# Synthetic empirical difficulty (issue #44)

This adds the synthetic counterpart of the fixed v2 tau2 baseline. It preserves
the saved ReAct prompt template verbatim (`results/baseline/v2_full/prompt.txt`),
the v2 model (`gpt-6.1-terra`), the user model, decoding settings, run seed,
four trials per task, 200-step limit, and concurrency of four. The original
tau2 agent implementation and synthetic fixtures are unchanged.

## Run

With the dependencies in `requirements.txt` installed, configure
`OPENAI_API_KEY` and optionally `BASE_URL` in `.env` or the environment.
The model comes from `baseline_config.yaml`; `.env`'s `MODEL_NAME` does not
override it. Credentials are never written into results.

```bash
# Offline preflight: inspect references, without calling a model.
python baseline/run_synthetic_baseline.py --full --preflight-only

# Small pilot, with a separate output directory.
python baseline/run_synthetic_baseline.py --num-tasks 2 --num-trials 1 --run-id v2_synthetic_pilot

# Full run: 64 tasks × 4 actual attempts. These calls incur API charges.
python baseline/run_synthetic_baseline.py --full --run-id v2_synthetic_full

# Continue an interrupted run; completed attempts are not rerun.
python baseline/run_synthetic_baseline.py --full --run-id v2_synthetic_full --resume

# Retry only API-failed attempts. Their original error traces are archived.
python baseline/retry_synthetic_errors.py --run-dir results/baseline/v2_synthetic_full

# Recompute scores from saved attempts without making API calls.
python baseline/compute_difficulty.py --trials results/baseline/v2_synthetic_full/trials.csv --out results/baseline/v2_synthetic_full/difficulty
python run_all.py --seed 42
```

The full trial CSV is picked up automatically by `run_all.py`. An explicit
`--synthetic-trials` path selects another run. When both baseline manifests
exist, the framework checks that the fixed agent settings agree.

## Saved artifacts

Each run is stored in `results/baseline/<run-id>/`:

- `trials.csv`: one row per attempted task/trial, with reward, pass/fail,
  evaluation status, termination reason, elapsed time, call counts, token
  usage, and trace path.
- `traces/<domain>/*.json.gz`: the agent/user prompts and conversation,
  tool calls/results, evaluation, actual model identifiers, fingerprints,
  request IDs, and token usage. No credentials or SDK request headers.
- `manifest.json`: baseline configuration, source/input hashes, trial plan,
  SDK version, and completion counts. Dollar costs remain blank because
  the endpoint does not return billed cost; they are not reported as zero.
- `reference_preflight.json`: reference tool calls that fail the supplied
  signature/schema or raise an exception in the unmodified mock.
- `difficulty/`: empirical difficulty and per-domain summaries.

CSV checkpoints are replaced atomically after each completed attempt. Resume
refuses changed configuration, task plans, or hashed runner/fixture sources.
The Python run seed determines trial seeds. As with the tau2 v2 runner,
no sampling seed is sent to the model. API generations are not guaranteed
to reproduce exactly; scoring the same saved attempts is deterministic.
The retry command leaves evaluated trials and invalid-reference tasks alone.
It archives the previous CSV and original error traces under `retries/`, then
replaces only the failed trial slots. The empirical denominator counts the
resulting valid attempts once; retry history remains available for auditing.

## Evaluation and limits

The agent receives the domain role/goal/action plan, public tool schemas, and
messages from a simulated customer. The customer receives only the task
narrative and its input data. Neither sees `expected_tool_calls`, milestones,
or expected outputs. Customer simulation reuses tau2's global text guidelines;
`HUMAN_IN_THE_LOOP` uses a fixed acknowledgement with no hidden helper model.

The deterministic oracle requires the reference tool calls in order, with
matching structured arguments and the reference terminal result data. Extra
reads are allowed; extra successful writes fail evaluation. Descriptive
`message`, `ai_message`, `content`, `description`, `rationale`, and `notes`
strings may be paraphrased. A bare `SUCCESS` is insufficient. Tool exceptions
do not count as successful execution.

These mocks have no shared database state. This is therefore a **reference
trajectory and structured-outcome proxy**, not the same evaluator used by tau2.
It can reject alternative valid workflows and does not establish semantic
correctness of free-form text. Compare empirical scores with this limitation.
Some supplied customer scenarios omit values required by their reference
calls, and mock responses may use hard-coded values that differ from reference
arguments. Failures can therefore reflect fixture constraints and missing
information as well as the agent's choices; they are not proof that these
workflows are intrinsically harder than tau2 workflows.

Preflight currently finds **17 invalid-reference tasks**: some expected inputs
violate declared TypedDict/function schemas, and others cause the supplied
mock implementation to raise. All requested attempts are still recorded, but
these tasks get blank rewards and blank empirical difficulty. API failures
also have blank rewards, with a separate `infrastructure_error` status.
Neither is included in the denominator `n` or silently counted as an agent
failure. Scores for the remaining tasks do not represent all 64 tasks.

The reference annotations or tool definitions need a separate reviewed repair
before the invalid tasks can receive valid empirical scores. This runner
does not change them to improve agent performance.

The initial adapter incorrectly forbade extra nested fields that the original
LangChain runner accepts. This was corrected before continuing the run. The
110 checkpointed attempts were retained only after verifying byte-identical
agent prompts and identical results for every executed tool event. Their
reference classifications were recomputed. The run preserves the initial
source snapshots and a compatibility audit; at most four in-flight requests
were interrupted during this correction. This is distinct from retrying
completed attempts or treating fixture problems as agent failures.

The API client follows the official
[Chat Completions Python reference](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create).
