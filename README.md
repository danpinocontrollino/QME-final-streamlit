# 🧠 Sapientia: AI-Powered University Value-Added Evaluator (VAE)

Welcome to **Project Sapientia**, an advanced, context-aware Cost-Benefit Analysis (CBA) system for evaluating global university performance. 

Traditional university rankings evaluate institutions predominantly on raw output (like total publications or citations), which inherently biases the scales toward wealthy institutions in high-GDP countries. **Sapientia** solves this by evaluating universities on their **Efficiency**—how well they convert governmental inputs (R&D Expenditure) into academic outputs (Research Quality)—strictly relative to their macroeconomic peer groups.

Through a pipeline involving graph theory, fuzzy record linkage, non-parametric frontier calculations, and an interactive AI-driven dashboard, this project fundamentally redesigns how academic excellence is measured.

---

## 🚀 The Dashboard (Streamlit App)

The final product of this mathematical pipeline is an interactive web dashboard built with **Streamlit** and **Altair**. 
You can run the web-app locally or view it hosted on Streamlit Cloud.

**Core Features:**
*   **Cost-Benefit Matrix:** A dynamic scatter plot visualizing GDP per Capita (Context), R&D Expenditure (Input Size), Research Quality (Output), and the calculated Conditional Efficiency (Color).
*   **Gemini AI Integration:** Allows users to interactively query the dataset in natural language (e.g., *"Show me the top 15 universities sorted by R&D Efficiency"*). Gemini autonomously rewrites pandas instructions to filter and adapt the UI on the fly.
*   **CBA Parallel Coordinates:** Tracks the transformation of universities from raw input parameters to final efficiency scores.

*(Note: The cloud deployment uses a lightweight `requirements.txt` to run the pre-computed `final_sapientia_master.csv`, actively avoiding heavy R-compilation overheads on the Streamlit servers).*

---

## ⚙️ The Methodological Pipeline

The core engine is located in `methodology_pipeline.ipynb`. It is split into four rigorous computational stages:

### Step 1: Global Bibliometric Fetch (OpenAlex API)
Traditional datasets (like *Times Higher Education*) often lack granular, open-source bibliometrics. We iterate globally across all countries in the master dataset, securely fetching API records from **OpenAlex** (converting nation names to safe ISO-2 codes via `pycountry`).

### Step 2: Probabilistic Record Linkage (Fuzzy Matching)
Because university names vary wildly across databases (e.g., "MIT" vs. "Massachusetts Institute of Technology"), we utilize `thefuzz` (Levenshtein distances) to link institutions. 
To drop computation time by 99% and strictly prevent cross-country false positives, the matching is **Partitioned by Country**.

### Step 3: Macroeconomic Peer Clustering (Louvain Algorithm)
A university in Uganda cannot be fairly compared directly to Stanford. 
Using `scikit-learn` and `networkx`, we project universities into an $N$-dimensional space based on their Context Variables (GDP per capita, baseline R&D). 
By sparsifying the distance matrices into a Graph, we apply the **Louvain Community Detection Algorithm** to agglomerate institutions into exactly 6 macroeconomic "Core Archetypes" (Clusters).

### Step 4: Conditional Order-$m$ Efficiency (`rpy2` & `nonparaeff`)
Within each discrete Louvain Cluster, we calculate how efficient an institution is relative to *its specific peers*. 
Using the R-language `nonparaeff` wrapper accessed natively in Python via `rpy2`'s `localconverter`, we run **Conditional Order-m calculations** ($m=50$). 
*   **Mathematical Safety:** We apply a constant **Laplace Smoothing** term (+1.0) to the R&D denominators to prevent mathematical explosions (division by zero) for low-investment nations.

---

## 📂 Repository Structure

*   `streamlit_rANDd.py`: The production Streamlit UI script.
*   `methodology_pipeline.ipynb`: The full 4-step data architecture and R-bridge calculation engine.
*   `implementation_rANDd.ipynb`: Legacy dashboard playground inside Jupyter using `ipywidgets`.
*   `requirements.txt`: Cloud-safe deployment dependencies (Altair, Pandas, Streamlit, Google Generative AI). *If running the methodology pipeline locally, you will additionally need `rpy2`, `networkx`, `thefuzz`, `python-louvain` and a local installation of the R language*.
*   **Data Artifacts:**
    *   `final_merged_dataset.csv`: Base rankings dataset.
    *   `openalex_bibliometrics_global.csv`: Output from Step 1.
    *   `master_with_openalex_linked.csv`: Output from Step 2.
    *   `master_with_clusters.csv`: Output from Step 3.
    *   `final_sapientia_master.csv`: **Final Output** from Step 4 (Order-m integration). This is what the dashboard consumes!

---

## ⚖️ Meta-Analysis: Traditional Rankings vs Sapientia VAE

| Dimension | Traditional Rankings | Sapientia VAE |
| :--- | :--- | :--- |
| **Contextual Fairness** | Low (Raw outputs dominate) | High (Normalized by GDP/Peers) |
| **Analytical Depth** | Low (Flat scalar scores) | High (Multi-dimensional topologies) |
| **Interactivity & AI** | None (Static PDF reports) | High (Conversational generative UI) |
| **Ease of Use** | High (Simple lists) | Moderate (Requires statistical literacy) |
| **Data Coverage** | High | Moderate (Drops if WB/Macro-data is missing) |

## ✅ Deployment Hook
To push changes to the frontend app, simply push to the `main` branch. Streamlit Cloud is configured to listen to this repository and will rebuild the interface automatically.