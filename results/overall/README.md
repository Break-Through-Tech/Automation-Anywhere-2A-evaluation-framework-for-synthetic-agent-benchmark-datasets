# Overall summary (Issue #21)

This folder contains a single “at-a-glance” comparison between **τ²-bench** and the
**synthetic** dataset.

## What gets plotted

`overall_radar.png` / `overall_radar.svg` plot three normalized axes:

- `difficulty_write_norm`: mean write-action count per dataset, normalized to `[0, 1]`
  across τ² and synthetic.
- `coverage_vendi_norm`: normalized Vendi score from `coverage/vendi_scores.csv` (domain=`all`).
- `coverage_attribute_diversity`: attribute diversity average from `coverage/attribute_scores.csv`.

The underlying numeric values are saved to `overall_scores.csv`.

## Generate

```powershell
python plot_overall_summary.py
```
