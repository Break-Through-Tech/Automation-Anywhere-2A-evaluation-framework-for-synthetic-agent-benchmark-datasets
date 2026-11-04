# Pilot Agent Test (#28)

## What I ran
- 10 tau-bench tasks: 4 airline, 3 retail, 3 telecom, with the number of write actions ranging from 0 to 8.
- Agent and simulated user: GPT-4.1, 1 trial per task
- Per-task runtime and cost were extracted from tau2-bench's results.json files into pilot_results.csv

## Results
- Average cost per task: $0.074 (agent + simulated user)
- Average runtime per task: 19 seconds
- 4 of 10 tasks passed
- Average cost by domain: $0.05 for airline, $0.06 for retail, $0.12 for telecom

## Estimated full run
- For all 278 tasks, using each domain's average cost, one trial would cost about $23 and take about 1.6 hours if run one at a time. 
- That scales with the number of trials: roughly $69 and 4.9 hours for 3 trials, $92 and 6.5 hours for 4, and $115 and 8.1 hours for 5.

## Recommendation
- n = 4 trials per task (~$92), which gives difficulty scores in steps of 0.25.
- Or, n = 3 (~$69) to save money.
- Sample size: all 278 base tasks. If the budget is limited, a sample of about 100 tasks spread across all domains at n = 4 would cost about $33.