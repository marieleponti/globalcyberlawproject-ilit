# Global CyberLaw Resource Project
## National Statements Visualizations — Documentation

---

## Table of Contents

- [Project Phase 1: Low/No-Code Visualizations](#project-phase-1-lowno-code-visualizations)
  - [Resources](#resources)
  - [Visualization Tools Used](#visualization-tools-used)
  - [Data Scope](#data-scope)
  - [Visualization Process](#visualization-process)
    - [Symbol Map](#symbol-map)
    - [Choropleth Map](#choropleth-map)
    - [Heatmap](#heatmap)
    - [Grouped Questions Survey](#grouped-questions-survey)
  - [What Worked](#what-worked)
  - [Key Issues With the Dataset](#key-issues-with-the-dataset)
  - [Ideas for Future Iterations](#ideas-for-future-iterations)
- [Project Phase 2: Django Web App](#project-phase-2-django-web-app)
  - [Overview](#overview)
  - [Visualizations Included](#visualizations-included)
  - [Methodology](#methodology)
  - [Data Methodology & Coding Standards (Sankey Diagrams)](#data-methodology--coding-standards-sankey-diagrams)
  - [Data Structure](#data-structure)
  - [Code Structure: `core/views.py`](#code-structure-coreviewspy)
  - [Utility Module Reference](#utility-module-reference)
  - [Deployment (Render)](#deployment-render)

---

## Project Phase 1: Low/No-Code Visualizations

This phase of the project consisted of creating initial visualizations using low- or no-code tools. Of the tools tested, the best results came from **Flourish** and **Datawrapper**.

### Resources

- [Data Institute 2023 — Day 1](https://github.com/cjddatainstitute/data-institute-2023?tab=readme-ov-file#day-1)
- [Intro to Charts and Visualization](https://lenagroeger.com/show-me-your-data/#/)
- [Making Timelines](http://lenagroeger.s3.amazonaws.com/talks/nicar-2015/timelines-nicar/timelines.html)
- [What Are You Trying to Show?](https://lenagroeger.com/show-me-your-data/#/4)
- [Quantitative Data Analysis: A Comprehensive Guide (Hevo Data)](https://hevodata.com)

### Visualization Tools Used

- [Flourish.studio](https://flourish.studio)
- [Datawrapper](https://www.datawrapper.de)

### Data Scope

For this stage, the team focused on the **Statement Matrix (All Issues)**.

### Visualization Process

#### First Draft

Two visualizations were produced:

1. **Heat map**
2. **Symbol map**

#### Symbol Map

Two approaches were originally considered:

- **By region** — the size of a symbol (e.g., a circle) represents the percentage of countries in that region that have released national statements.
- **By country** — each country gets its own symbol, so instead of one circle representing "Europe," each European country has its own circle.

**Quantifying the data:** The first attempt assigned `0` to "no," `1` to "ambiguous," and `2` to "yes." This raised a problem: a circle would appear over a country even if that country had no statement on the topic (e.g., Application of International Law). This led to an open question — *if a country has not published any statement, should a symbol appear at all?*

#### Choropleth Map

Countries were color-coded to show participation (i.e., whether a statement had been published).

**Open questions raised during planning:**

- If a country's statement was published in a given year (e.g., 2021), does that mean all subsequent categories (Application of IL, Non-Intervention, ..., Dispute Settlement) were also addressed that year?
- Is it valuable for the map to chart not just year-by-year State participation, but also categories? If so, can we assume all categories were published in the same year?

##### Documentation: Building the Choropleth Map

**Step 1 — Source data.** The Statement Matrix (All Issues) was downloaded and uploaded to Excel, in the shared *National Statements Visualization* folder.

**Step 2 — Quantify participation.** Participation was graded "yes," "no," or "ambiguous" using the following formula:

```excel
=IF(E2="Yes", 1, IF(E2="No", 0, IF(E2="Ambiguous", 0.5, null)))
```

This produces a numerical representation where "yes" = `1`, "no" = `0`, and "ambiguous" = `0.5`.

**Step 3 — One sheet per year.** A separate sheet was created for each year, starting from the earliest year a statement was published (2016) through the present. For example, the 2023 sheet is a copy of the matrix, with any country whose statement was released in 2024 changed from `1` back to `0` — reflecting that, as of 2023, that country did not yet have a published statement.

**Step 4 — Automate the year-by-year conversion.** A `<Current Year>` column was added to each sheet (e.g., the sheet representing 2021 data has `<Current Year> = 2021`). A formula compares the current year to each statement's publish date: if the publish date is on or before the current year, the category value is `1`; otherwise, it is `0`.

**Step 5 — Upload to Datawrapper.** The data was uploaded to the team's [Datawrapper archive](https://app.datawrapper.de/archive/team/H2_4w6co) as a separate spreadsheet per year, so each map shows cumulative participation to date. For example, since the United States has a `1` in 2016 (having published a statement that year), it appears highlighted on that year's map.

This was repeated for every year from 2016–2024. The spreadsheet structure: countries as rows, years as columns, with each `[row, column]` cell holding a boolean indicating whether that country had a published statement by that year. For example, Chile published its first statement in 2018, so it is `0` for 2016–2017 and `1` starting in 2018.

**Step 6 — Generate the map.** Datawrapper generates the choropleth map based on the selected column (year).

This process was repeated for every year in the dataset, producing one map per year.

**Step 7 — Animate the sequence.** Each yearly map was downloaded as a PNG and combined into an animated GIF using [Animated GIF Maker (ezgif.com)](https://ezgif.com/maker).

#### Heatmap

The goal of the heatmap was to show the intensity of discussion for each topic over time, independent of which States were involved. A key assumption: once a statement addressing a topic was released, that topic is considered "discussed" in every subsequent year — even if a later statement from the same country omits it.

**First iteration.** Counted the number of statements published per year, non-cumulatively (i.e., it counted prior years' statements but not duplicate discussions of the same issue by the same state). For example:

- In 2012, the US published a statement discussing the application of international law (IL) to cyberspace → counted as `1` for 2012.
- In 2016, the US remained the only state to have addressed that topic → still `1`.
- In 2018, the UK also published a statement addressing IL → the count became `2`. (The US's 2018 statement on the same topic was not double-counted.)

This version made 2021 appear as the peak of the conversation, since that year had the most national statements (driven by the UNGA and GGE processes). The team felt this misrepresented the steady, ongoing progression of state engagement — implying discussion of IL only began in 2021, which was inaccurate.

**Second iteration.** Switched to a cumulative count to better reflect the progression of participation.

This version looked better visually, but the cumulative approach effectively doubled the dataset, which caused the legend to display an incorrect total number of national statements.

**Outcome:** This phase raised further questions — Could a visualization show how many states have addressed a given issue? Could it capture *which* states and *when* they raised an issue? Could it distinguish issues discussed by most states, by a smaller majority, by a minority, or only briefly mentioned? These questions led the team to pivot to a different visualization method.

#### Grouped Questions Survey

The team researched methods better suited to the client's questions and settled on a **grouped questions survey**, a feature available in Flourish. This format allows questions to be grouped together to compare answer frequency across chosen criteria.

Data was prepared in **Google Sheets** rather than Excel — Google Sheets' autofill/predictive editing was more effective for bulk edits, saving time over manual updates in Excel. Once finalized, the data was copied into Flourish.

##### First Attempt: States and Issues in Flourish

🔗 [View visualization](https://public.flourish.studio/visualisation/19149954/)

**How it was made:**

Participation was measured as binary (`1` = yes, `0` = no), along with the year each statement was published. The same assumption applied — once a topic is mentioned, it is considered to "stand" going forward.

Using the [States and Issues spreadsheet](#):

- On the **`Yes/No and 1,0`** sheet, data copied from Airtable was converted using:

  ```excel
  =IF(B2="yes", 1, IF(B2="No", 0, 0.5))
  ```

  Any entry that was neither "yes" nor "no" (i.e., a partial publication) was assigned `0.5`.

- On the **`Overview`** sheet, a `Year` column was added, dynamically extracting the year from the publication date string (avoiding manual entry).

- The cleaned data (boolean publication status only — "yes"/"no" columns removed) was copied into Flourish.

**Flourish data configuration:**

| Setting | Value |
|---|---|
| Categorical columns | B–N (Country, Year, and Topics) |
| Geographic columns | B (Countries) |
| Label | B |
| Info for pop-ups | B–C (Country and Year) |

In Flourish's **Grouped Questions** section:

| Field | Value |
|---|---|
| Name column | A ("Topic") |
| Question | B |
| Display answer as | C (topic name) |
| Answers to include | D (1) |

🔗 [Edit in Flourish](https://app.flourish.studio/visualisation/19186602/edit)

This produced the first version of the grouped-questions-survey visualization.

**Refinements:**

- To show the number of States represented in each group, **Group label → "Show number of dots in group"** was set to `true`.
- By default, Flourish hides some country labels depending on string length. This was overridden via a manual label override.
- To color-code by year, the legend's **"Shade by"** setting was set to `Year`.

##### Third Draft

🔗 [View story](https://public.flourish.studio/story/2542233/)

**How it was made:** Added a filter for the `Year` field and converted the visualization into a Flourish "story."

##### Fourth Draft

🔗 [View story](https://public.flourish.studio/story/2561898/)

**How it was made:** To make the visualization cumulative, the dataset was restructured so that each country has one row *per year*, starting from its first publication year through the present (rather than one row per country with a single initial-publication year).

- Restructured data: [Flourish Data – States and Issues, One Country One Row](#) (Discussion increase over years)
- 🔗 [Edit in Flourish](https://app.flourish.studio/visualisation/19211841/edit)
- 🔗 **Final published visualization:** [View here](https://public.flourish.studio/visualisation/19982361/)

### What Worked

- The Airtable data, originally qualitative, converted cleanly into quantitative/binary form when needed. This worked well for straightforward comparisons — e.g., comparing issue prevalence across groups.

### Key Issues With the Dataset

- **Limited dataset size** reduced the effectiveness of some visualization methods that could otherwise be compelling (e.g., time-series analysis).
- **Duplicate national positions in 2021** (particularly overlapping GGE and UNGA statements with few new topics) inflated the apparent number of distinct perspectives/additions. This was mitigated in the survey by combining each country's UNGA and GGE statements into a single entry, which produced a more accurate depiction of topic-discussion frequency.
- **Limits of binary (yes/no → 1/0) data** for visualization — deeper analysis (e.g., a chi-squared test) would be needed to go further.
- **Version control in Flourish:** Republishing over the same visualization (rather than duplicating, renaming descriptively, and then publishing) made it difficult to trace the original form of earlier visualizations after edits based on client feedback. **Going forward:** always duplicate → rename with a clear, descriptive name → publish, to preserve a clean history.

### Ideas for Future Iterations

- Add other data categories (e.g., North/South classification, GDP) to enable richer analysis — for example, a cluster analysis incorporating an additional data dimension.

---

## Project Phase 2: Django Web App

### Overview

Phase 2 is a web app built with **Django** (Python), using **Pandas** and **NumPy** for data processing and **Plotly** for graph generation. It incorporates the Airtable data and introduces new visualizations of state responses to Use of Force policy questions.

### Visualizations Included

1. A **Sankey diagram** showing States and their responses to each topic area (Sovereignty, Use of Force, Non-Intervention).
2. A **Sankey diagram** showing States and their responses to each Use of Force question, layered with democracy score range (Sovereignty, Use of Force, Non-Intervention).
3. A **scatter plot** of overall Use of Force questions (Sovereignty, Use of Force).
4. A **scatter plot** of Use of Force questions, filterable by state (Sovereignty, Use of Force).
5. A **Sankey diagram** showing States and their responses to Question 8 of Use of Force, layered with NATO membership (Sovereignty, Use of Force).
6. A **comparison table** of EU member states' responses vs. the EU's own response, in the Use of Force issue area (Sovereignty, Use of Force).
7. A **comparison table** of EU member states' responses vs. non-EU states' responses, in the Use of Force issue area (Sovereignty).

### Methodology

The process began with research into visualization types and tools best suited to producing effective visualizations for attorneys, policymakers, and the public. Key considerations: the underlying data is question-and-response style, with multiple-choice-style data points.

After consulting visualization resources and a Data Scientist, the team selected:

- Sankey Diagrams
- Scatter Plots
- Comparison Tables
- A Sunburst Chart

**Why Django:** After experimenting with no-code platforms, the team chose to build a Django app to take advantage of Python's data analysis libraries (NumPy, Pandas) and Plotly's compatibility with Python for visually rich charts.

**Architecture:** A Dockerized Django app was built. No database was used — data is sourced directly from CSVs exported from the coded Airtable base. Some CSVs required minimal adaptation; others required processing/reformatting to fit the required visualization structure.

To visualize relationships between question responses and other markers (e.g., democracy scores, NATO membership), the data tables were joined within Python functions.

### Data Methodology & Coding Standards (Sankey Diagrams)

This section documents how the underlying national-statement data was defined, coded, and validated for the Sankey diagram visualizations.

#### Objective

The purpose of the Sankey diagram was to visualize how nations have voiced their statements on select UN resolutions by depicting the flow from each country to its assigned response value (e.g., Yes, No, Silent, Ambiguous). A Sankey diagram was chosen over a table or other visualization format because it can display voting/response patterns across many countries at once.

#### Scope

Country-level values apply to an individual country's position on a specific question, based on the categorization of that nation's response.

#### Data Collected

Each nation's statements were assigned a value (Yes / No / Ambiguous / Silent) based on extracted official statements on specific topics (e.g., Use of Force). Coding was peer-reviewed by research assistants, legal fellows, and law school professors, and reflects assigned values based on publicly available official statements.

#### Data Preparation

Nation names and statement categorizations were standardized, duplicate entries were removed, and missing values were checked by research assistants and tech fellows. Preparation included inspecting CSV imports/exports for inconsistencies and cross-checking against the Airtable source, to ensure the Sankey diagrams accurately reflected the national statements.

#### Data Validation

Validation was conducted by legal fellows and research assistants: a research assistant visually inspected each CSV file, which was then proofread by a legal fellow to verify it was free of errors.

#### Sources

- UNGA Official Compendium of Voluntary National Contributions
- OAS Survey Responses Submitted
- Position papers issued by the respective countries

#### Definitions

**National Statement:** A public statement issued by a government body or head of state.

#### Variables

**Categorical (response value):**

| Value | Definition |
|---|---|
| **Yes** | The country has issued a clear public statement indicating support or agreement with the question. |
| **No** | The country has issued a clear public statement indicating disagreement with the question. |
| **Ambiguous** | The country has issued a public statement that is mixed or conditional and does not clearly state support or opposition. |
| **Silent** | No public statement has been made by the country. |

**Date of Position:** The date of the most recent statement is either 2025 or 2026.

### Data Structure

| Table | Description |
|---|---|
| **Topic CSVs** | One CSV per topic (Sovereignty, Use of Force, etc.). Required minimal processing — the main addition was an ISO country code column, since Python join functions use ISO codes (more consistent and less error-prone than matching on country name). |
| **EU States & Non-EU** | Reference table distinguishing EU member states from non-EU states. |
| **NATO & Non-NATO** | Reference table distinguishing NATO members from non-members. |
| **Democracy Index Scores** | Democracy score data per state, used to layer Sankey diagrams. |
| **Citations Table** | Source citation references for statements. |

### Code Structure: `core/views.py`

The app follows a consistent pattern across views: **load data → transform/build a figure → render an HTML template with the figure embedded**. Data loading and figure-building logic live in reusable helper modules under `core/utils/`, not in the views themselves — this keeps `views.py` focused on routing and page assembly.

#### Helper modules used by `views.py`

| Module | Responsibility |
|---|---|
| `core.utils.data_loader` | Loads and prepares each dataset (Use of Force, Sovereignty, Non-Intervention, Democracy Index, EU/NATO membership, citations) from CSV. Also exposes `get_questions()` to extract question columns from a topic dataframe. |
| `core.utils.sankey_utils` | Builds Sankey diagram figures — including the state-vs-democracy-score layered version and the NATO-membership layered version. |
| `core.utils.scatter_utils` | Builds scatter plot figures (overall and by-state). |
| `core.utils.parallel_categories_utils` | Builds the parallel-categories figure comparing Use of Force and Sovereignty responses. |
| `core.utils.sunburst_utils` | Builds the sunburst chart for Question 8 of Use of Force. |
| `core.utils.members_comparison_utils` | Builds the EU-vs-EU-response and EU-vs-non-EU comparison tables. |
| `core.utils.html_utils` | Converts Plotly figures to embeddable HTML (`generate_sankey_html`, `generate_plot_html`, `generate_sunburst_html`), and generates a fallback error HTML block (`generate_error_html`) shown in place of a chart if data loading or figure generation fails. |

#### Page (routing) views

Simple views that render a static page/template with no chart logic:

| View function | URL | Template | Purpose |
|---|---|---|---|
| `home` | `/` | `core/home.html` | Landing page |
| `methodology` | `/methodology` | `core/methodology.html` | Methodology write-up page |
| `use_of_force` | `/uof` | `core/uof.html` | Use of Force topic landing page |
| `sovereignty` | `/sovereignty` | `core/sovereignty.html` | Sovereignty topic landing page |
| `nonintervention` | `/nonintervention` | `core/nonintervention.html` | Non-Intervention topic landing page |

#### Chart-generating views

Each of these follows the same `try/except` pattern: load the needed dataframe(s), build the figure, convert it to HTML, and pass it into the template context. If anything fails (missing data, malformed CSV, etc.), the `except` block renders the **same template** with an error message in place of the chart via `generate_error_html()`, rather than crashing the page.

| View function | URL | Topic | Visualization |
|---|---|---|---|
| `uof_sankey` | `/uof-sankey` | Use of Force | Sankey diagram of state responses |
| `uof_demscore_sankey` | `/uof-demscore-sankey` | Use of Force | Sankey diagram layered with democracy score |
| `uof_scatter` | `/uof-scatter` | Use of Force | Scatter plot, overall |
| `uof_by_state_scatter` | `/uof-by-state-scatter` | Use of Force | Scatter plot, filterable by state |
| `uof_sov_parallel_categories` | `/uof-sovereignty-parallel-categories` | Use of Force + Sovereignty | Parallel categories comparison |
| `uof_q8_nato_sankey` | `/uof-art51-nato-sankey` | Use of Force (Q8 / Art. 51) | Sankey diagram layered with NATO membership |
| `sovereignty_sankey` | `/sovereignty-sankey` | Sovereignty | Sankey diagram of state responses |
| `sov_demscore_sankey` | `/sov-demscore-sankey` | Sovereignty | Sankey diagram layered with democracy score |
| `sovereignty_by_state_scatter` | `/sov-by-state-scatter` | Sovereignty | Scatter plot, filterable by state |
| `nonintervention_sankey` | `/nonintervention-sankey` | Non-Intervention | Sankey diagram of state responses |
| `nonintervention_demscore_sankey` | `/nonint-demscore-sankey` | Non-Intervention | Sankey diagram layered with democracy score |

#### Comparison table views

These use `opy.plot(..., output_type='div', include_plotlyjs=False)` instead of the `html_utils` helpers, and do **not** wrap data loading in a `try/except` — an error in these views will surface as a normal Django error page rather than an inline error message.

| View function | URL | Table |
|---|---|---|
| `eu_comparison_uof_view` | `/uof-eu-states-to-eu-uof` | EU member states vs. EU's own response — Use of Force |
| `eu_comparison_sov_view` | `/sov-eu-states-to-eu-sov` | EU member states vs. EU's own response — Sovereignty |
| `eu_non_eu_comparison_sov_view` | `/sov-non-eu-states-to-eu-sov` | EU member states vs. non-EU states — Sovereignty |
| `state_comparison_view` | `/uof-state-comparison` | State-by-state comparison — Use of Force (transposed data) |

> 🚧 **Note for maintainers — feature in progress:** `state_comparison_view` calls `create_state_comparison_table()`, but this is not yet implemented. `core/utils/state_comparison_utils.py` currently exists only as a commented-out stub:
>
> ```python
> # # member comparison table utils
> # import pandas as pd
> # import plotly.graph_objects as go
> #
> # def create_state_comparison_table(df, preguntas):
> #
> #     return fig
> ```
>
> The corresponding import in `views.py` is also commented out. As written, visiting `/uof-state-comparison` will raise a `NameError`. To finish this view: implement `create_state_comparison_table()` (it needs to build and return a Plotly figure — `fig` is currently referenced but never defined), then uncomment both the function body and the import line in `views.py`.

### Data Layer: `core/utils/data_loader.py`

All raw data lives as CSVs in the `data/` folder and is loaded fresh on every request (no database — `db.sqlite3` exists in the project but is not used for this app's content). Every loader function follows the same shape: build the file path from `settings.BASE_DIR`, read the CSV with `pandas`, rename the `ISO` column to lowercase `iso` (for consistent joins across tables), and return the dataframe.

| Function | Source CSV (`data/`) | Column renames | Notes |
|---|---|---|---|
| `load_uof_data()` | `uof-mar2026.csv` | `ISO` → `iso` | Main Use of Force response dataset |
| `load_uof_citations_data()` | `uof_citations-feb2026.csv` | `ISO` → `iso` | Citations backing Use of Force statements |
| `load_uof_transposed_data()` | `uof_transposed-mar2026.csv` | `ISO` → `iso` | Transposed version of the UoF dataset, used for `state_comparison_view` |
| `load_sovereignty_data()` | `sovereignty-mar2026.csv` | `ISO` → `iso` | Main Sovereignty response dataset |
| `load_sovereignty_citations_data()` | `sovereignty_citations-feb2026.csv` | `ISO` → `iso` | Citations backing Sovereignty statements |
| `load_nonintervention_data()` | `nonintervention-mar2026.csv` | `ISO` → `iso` | Main Non-Intervention response dataset |
| `load_nonintervention_citations_data()` | `nonintervention_citations-feb2026.csv` | `ISO` → `iso` | Citations backing Non-Intervention statements |
| `load_membership_data()` | `eu-states.csv` | `ISO` → `iso`, `Membership` → `membership` | EU membership status per state |
| `load_nato_data()` | `NATO_EU_Member.csv` | `ISO` → `iso` | NATO (and EU) membership status per state |
| `load_democracy_data()` | `democracy-index-eiu.csv` | `Year` → `year`, `Code` → `iso`, `Democracy score` → `dem_score` | Filters to only the **most recent year** present in the file before returning — so the app always reflects the latest available democracy scores, not a historical series |

**`get_questions(df)`** — a shared helper (not a loader) that returns the list of question columns from any topic dataframe, assuming columns `0` and `1` are metadata (e.g., State and ISO) and every column from index `2` onward is a question/topic column.

> 📌 **Note:** the CSV filenames are date-stamped (e.g., `-mar2026`, `-feb2026`), meaning updates to the underlying data currently require **replacing the file and updating the filename inside `data_loader.py`** rather than the app reading "the latest file" automatically. Worth keeping in mind for future data refreshes.

**No database is used for app content.** `models.py` is empty and `db.sqlite3` (present in the project as Django's default) is not used to store any of the visualization or statement data — everything is read fresh from the CSVs in `data/` on every request.

## Utility Module Reference

This section documents each helper module in `core/utils/` at the function level, based on a review of the source code.

### `html_utils.py`

Wraps a Plotly figure's `.to_html()` output in a styled `<div>` (white background, rounded corners, drop shadow) so charts look consistent when embedded in Django templates.

| Function | Purpose |
|---|---|
| `generate_sankey_html(fig)` | Wraps a Sankey figure's HTML in the styled card `<div>`. Loads Plotly.js from the CDN (`include_plotlyjs='cdn'`). |
| `generate_plot_html(fig)` | Same styled-card treatment for general (non-Sankey) figures. Also loads Plotly.js from CDN. |
| `generate_sunburst_html(fig)` | Converts a sunburst figure to HTML — **no styled card wrapper**, unlike the other two (worth aligning if visual consistency matters). |
| `generate_error_html(error_message)` | Renders a red-bordered error card ("Error al cargar el gráfico") with the exception message, shown in place of a chart when a view's `try/except` catches an error. |

> Because `include_plotlyjs='cdn'` is used in multiple places, **the app requires an internet connection to render charts** (Plotly.js is not bundled locally). Worth knowing if this is ever deployed somewhere without outbound internet access.

### `sankey_utils.py`

The most complex utility module — builds all Sankey diagrams, including citation tooltips.

| Function | Purpose |
|---|---|
| `create_sankey_figure(df_main, df_citations)` | Builds the main per-topic Sankey (state → response), with a dropdown to switch between questions. Reshapes the wide dataframe to long format via `prepare_merged_dataframe()`, then builds one Sankey trace per question (only the first is visible by default; the dropdown toggles `visible`). |
| `prepare_merged_dataframe(df_main, df_citations)` | Melts the response dataframe into long format (one row per state/question/answer), cleans question text via `clean_question()`, and left-joins in the matching citation text. Missing citations are filled with `"No citation available"`. |
| `create_sankey_data(df_long)` | Groups the long dataframe by state → answer per question and builds the actual `go.Sankey` node/link structures, including wrapped citation text in the hover tooltip. |
| `create_issue_demscore_sankey_figure(df_issue, df_dem, df_citations)` | Builds the three-stage Sankey: **country → democracy-score range → response**. |
| `create_issue_demscore_sankey_data(...)` | Merges response data with democracy scores, buckets scores into 8 ranges (`[0-2)` … `[9-10]`), and builds the two-stage link structure (country→range, then range→response). Citations are attached only to the country→range links. |
| `create_uof_art51_nato_sankey(df_force, df_nato)` | Builds the Use-of-Force / Article 51 Sankey layered by NATO membership, with a per-country dropdown that highlights that country's flow (other flows fade to low opacity). |
| `create_sankey_dropdown_menu(...)` / `create_demscore_sankey_buttons(...)` | Build the dropdown menu configs used above. |
| `clean_question(text)` | Strips leading numbering (e.g., `"1.1"`), leading parenthetical tags, and stray punctuation from question column headers, then capitalizes the first letter — used to get human-readable labels for hover text and dropdowns. |
| `wrap_text(text, width=60)` | Wraps long citation strings onto multiple lines (`<br>`-separated) for readability in hover tooltips. |

> ⚠️ **Hardcoded column index:** `create_uof_art51_nato_sankey()` selects the Article 51 question via `df_force.columns[15]` — a **fixed column position**, not a column name lookup. If the Use of Force CSV's column order ever changes (e.g., a question is added, removed, or reordered), this will silently point to the wrong question instead of raising an error. The same hardcoded-index pattern (`column_index = 15`) appears in `sunburst_utils.py` for the same question — both would need to be updated together.

### `scatter_utils.py`

| Function | Purpose |
|---|---|
| `create_uof_scatter_figure(df, preguntas)` | Scatter plot of all states' responses to the *first* Use of Force question (`preguntas[0]`), with a dropdown to switch which question is plotted. |
| `create_by_state_scatter_figure(df, preguntas, estados)` | Scatter plot of one state's responses across *all* questions, with a dropdown to switch states. Defaults to the first state (`estados[0]`). |
| `create_scatter_dropdown_buttons(df, preguntas)` | Builds the question-switching dropdown for the overall scatter plot. |
| `create_state_scatter_buttons(df_uof, preguntas_uof, estados)` | Builds the state-switching dropdown for the by-state scatter plot. |

> 🧹 **Cleanup note:** the file contains a second, commented-out copy of `create_by_state_scatter_figure` (with a slightly different y-axis ordering). Safe to delete once confirmed the active version above is the intended one — keeping it may cause confusion for future editors.

### `parallel_categories_utils.py`

| Function | Purpose |
|---|---|
| `create_parallel_categories_figure(df_uof, df_sov, questions_uof, questions_sov)` | Builds a 3-dimension parallel-categories (Parcats) figure: Country → Use of Force response → Sovereignty response. Defaults to the *first* UoF question and the *second* Sovereignty question (`questions_uof[0]`, `questions_sov[1]`). Two independent dropdowns let the user swap which UoF question and which Sovereignty question are shown. |
| `create_parallel_categories_buttons_uof(...)` / `create_parallel_categories_buttons_sov(...)` | Build each dropdown's button list, restyling dimension 1 or dimension 2 respectively via Plotly's `restyle` method. |
| `create_parallel_categories_menu(buttons, x_position, y_position)` | Shared layout config for a dropdown menu, positioned via the given coordinates. |

> Note the default selection asymmetry: Sovereignty starts on `questions_sov[1]` (the **second** question) while Use of Force starts on `questions_uof[0]` (the **first**). If that's not intentional, it's a one-line fix (`questions_sov[0]`).

### `sunburst_utils.py`

| Function | Purpose |
|---|---|
| `create_uofq8_sunburst_figure(df_force, df_nato)` | Builds the drill-down sunburst chart for Use of Force Question 8: NATO status → response → country. Filters to the four expected answers (`Yes`, `No`, `Silent`, `Ambiguous`) before building the chart, so any other value in that column is silently excluded. Shares the same hardcoded `column_index = 15` assumption noted above for `sankey_utils.py`. |

### `members_comparison_utils.py`

| Function | Purpose |
|---|---|
| `create_eu_comparison_table(df_issue, preguntas, df_membership)` | Builds a Plotly table comparing the EU's own response (row with `iso == 'EUN'`) against each EU member state's response, one column per country. Cells are color-coded green if a country's answer matches the EU's answer, coral/red if it differs. |
| `create_eu_non_members_comparison_table(df_issue, preguntas, df_membership)` | Same comparison logic, but against **non-EU** states instead of members. |

Both functions wrap their logic in a `try/except` that prints the error to the console and returns an **empty** `go.Figure()` on failure — so a data problem here shows up as a blank chart in the browser rather than the app's usual red error card (the `generate_error_html()` pattern used elsewhere is not used in this module).

> 🧹 **Cleanup note:** in `create_eu_comparison_table`, `colors = []` is assigned twice in a row (redundant, not a bug). `state_comparison_utils.py` — the module `state_comparison_view` depends on — is still a commented-out stub with no working implementation (see the note under Comparison table views above).

---

## Deployment (Render)

The app is deployed on [Render](https://render.com) as a Docker-based Web Service, connected to a managed PostgreSQL database. **Access is restricted — a login is required to view the site** (via `core.middleware.LoginRequiredMiddleware`, redirecting to `/login/`). This is intentional for now; the app is not publicly accessible. Admin accounts already exist and are managed through `/admin/`.

### Settings.py fixes made for Render

The project was originally configured for Railway and required two fixes before it would run on Render:

| Issue | Fix |
|---|---|
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` referenced an undefined `RAILWAY_HOST` variable, which would raise a `NameError` on startup with `DEBUG=False` | Replaced with `RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")` — a variable Render injects automatically, no manual configuration needed |
| `SECRET_KEY` was hardcoded in `settings.py` (a `django-insecure-...` development key, exposed in Git history) | Changed to `SECRET_KEY = os.environ.get("SECRET_KEY")`, with a newly generated production key set as an environment variable on Render (never committed to the repo) |

### Environment variables (Render dashboard)

| Variable | Value | Notes |
|---|---|---|
| `SECRET_KEY` | New production key | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | |
| `DATABASE_URL` | — | Set automatically by Render when a PostgreSQL service is attached |
| `RENDER_EXTERNAL_HOSTNAME` | — | Injected automatically by Render; do not set manually |

### Pre-Deploy Command

Since the app depends on PostgreSQL for `auth`/`sessions`/`admin` tables, migrations must run before the service takes traffic. Configured in Render as the **Pre-Deploy Command**:

```bash
python manage.py migrate
```

### Deployment checklist

- [x] `RAILWAY_HOST` → `RENDER_HOST` fix applied
- [x] `SECRET_KEY` moved to an environment variable
- [x] `SECRET_KEY`, `DEBUG=False` configured in Render's dashboard
- [x] PostgreSQL service attached (provides `DATABASE_URL` automatically)
- [x] Pre-Deploy Command set to `python manage.py migrate`
- [x] Admin account already exists — no `createsuperuser` step needed
- [ ] Confirm `python manage.py collectstatic --dry-run` passes locally before deploying (`STATICFILES_STORAGE` uses `CompressedManifestStaticFilesStorage`, which fails the build if a template references a static file that doesn't exist)
- [ ] Confirm the `data/` folder (CSVs) is not excluded by `.gitignore` — every view depends on these files being present in the deployed image

---

*Document prepared for the Global CyberLaw Resource Project.*