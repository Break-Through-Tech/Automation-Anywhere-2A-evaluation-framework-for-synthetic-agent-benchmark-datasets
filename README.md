# AI Studio Challenge Project Title

## Run the evaluation framework (issue #15)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py --seed 42
```

This computes **coverage** (normalized Vendi Score and Attribute Diversity)
and **structural difficulty** (ground-truth write-action counts) for the
committed 278-task τ²-bench base split and all 64 synthetic tasks.
It also recomputes empirical difficulty and Spearman validation using the
saved v2 τ²-bench baseline trials. It does not rerun agents or require an API key.
The public sentence-transformer model downloads on first use; its revision
is pinned and inference runs on CPU.

Outputs are saved under `results/framework/`:

- `metrics_summary.json`: overall scores, task counts, and limitations.
- `metrics_by_domain.csv`: overall and per-domain/category scores.
- `coverage_vendi.csv`, `coverage_attribute_scores.csv`,
  `coverage_attribute_counts.csv`: coverage scores and counts.
- `difficulty_tasks.csv`: structural and empirical scores for every task.
- `difficulty_validation.json`, `difficulty_scatter.png`: validation results.
- `run_metadata.json`: input/source hashes, seed, model revision, and versions.

Use `--output-dir` to keep runs separate. For example:

```bash
python run_all.py --seed 42 --output-dir /tmp/framework-repeat
```

The synthetic baseline runner and evaluation protocol are documented in
[`baseline/SYNTHETIC_BASELINE.md`](baseline/SYNTHETIC_BASELINE.md).
When `results/baseline/v2_synthetic_full/trials.csv` exists, the framework
automatically includes its empirical scores. Invalid-reference tasks remain
unscored, not zero. `--synthetic-trials path/to/trials.csv` selects another
saved run using the same fixed baseline settings.
Trial columns are `domain,task_id,trial,reward,passed` (additional columns
are allowed). Use the original synthetic agent-category domain and processed
task ID. Only trials with rewards enter the empirical denominator; duplicate
trials and unknown task IDs are rejected. Do not combine the old v1 pilot
with the v2 full baseline. `--tau-trials` selects a different saved tau run.

Synthetic Attribute Diversity uses four broad domains, while its Vendi and
write-count breakdowns use seven agent categories. Tool entropy retains the
existing observed-vocabulary definition. Vendi VS/n depends on sample size
and repeated descriptions; higher difficulty does not imply higher quality.

Run the focused checks with `python -m unittest discover -s tests -v`.
The framework reads the committed task file, so a local tau2-bench clone
is not needed for this command.

---

> 💡 **Note for the team:** This is just a template. Update the above title with your AI Studio Challenge Project name. Remove all guidance notes and example text in this template and populate this README with your own content. You can work on this README throughout AI Studio, and get feedback from your AI Studio Coach and Challenge Advisor before finalizing it.  

---

### 👥 **Team Members**

**Example:**

| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Taylor Nguyen    | @taylornguyen | Data exploration, visualization, overall project coordination            |
| Jordan Ramirez   | @jramirez     | Data collection, exploratory data analysis (EDA), dataset documentation  |
| Amina Hassan     | @aminahassan  | Data preprocessing, feature engineering, data validation                 |
| Priya Mehta      | @pmehta       | Model selection, hyperparameter tuning, model training and optimization  |
| Chris Park       | @chrispark    | Model evaluation, performance analysis, results interpretation           |

---

## 🎯 **Project Highlights**

**Example:**

- Developed a machine learning model using `[model type/technique]` to address `[challenge project task]`.
- Achieved `[key metric or result]`, demonstrating `[value or impact]` for `[host company]`.
- Generated actionable insights to inform business decisions at `[host company or stakeholders]`.
- Implemented `[specific methodology]` to address industry constraints or expectations.

---

## 👩🏽‍💻 **Setup and Installation**

**Provide step-by-step instructions so someone else can run your code and reproduce your results. Depending on your setup, include:**

* How to clone the repository
* How to install dependencies
* How to set up the environment
* How to access the dataset(s)
* How to run the notebook or scripts

---

## 🏗️ **Project Overview**

**Describe:**

- How this project is connected to the Break Through Tech AI Program
- Your AI Studio host company and the project objective and scope
- The real-world significance of the problem and the potential impact of your work

---

## 📊 **Data Exploration**

**You might consider describing the following (as applicable):**

* The dataset(s) used: origin, format, size, type of data
* Data exploration and preprocessing approaches
* Insights from your Exploratory Data Analysis (EDA)
* Challenges and assumptions when working with the dataset(s)

**Potential visualizations to include:**

* Plots, charts, heatmaps, feature visualizations, sample dataset images

---

## 🧠 **Model Development**

**You might consider describing the following (as applicable):**

* Model(s) used (e.g., CNN with transfer learning, regression models)
* Feature selection and Hyperparameter tuning strategies
* Training setup (e.g., % of data for training/validation, evaluation metric, baseline performance)


---

## 📈 **Results & Key Findings**

**You might consider describing the following (as applicable):**

* Performance metrics (e.g., Accuracy, F1 score, RMSE)
* How your model performed
* Insights from evaluating model fairness

**Potential visualizations to include:**

* Confusion matrix, precision-recall curve, feature importance plot, prediction distribution, outputs from fairness or explainability tools

---

## 🚀 **Next Steps**

**You might consider addressing the following (as applicable):**

* What are some of the limitations of your model?
* What would you do differently with more time/resources?
* What additional datasets or techniques would you explore?

---

## 📝 **License**

Specify how your project can be used by others. Choose an appropriate license and link it here (e.g., MIT, Apache 2.0). Make sure your Challenge Advisor approves of the selected license type. 

**Example:**
This project is licensed under the MIT License.

---

## 📄 **References** (Optional but encouraged)

Cite relevant papers, articles, or resources that supported your project.

---

## 🙏 **Acknowledgements** (Optional but encouraged)

Thank your Challenge Advisor, host company representatives, TA, and others who supported your project.
