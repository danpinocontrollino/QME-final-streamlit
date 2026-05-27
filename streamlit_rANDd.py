import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="Sapientia CBA - R&D", layout="wide")

# =========================================================
# 1. SETUP & DATA LOADING
# =========================================================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

@st.cache_data
def load_data():
    df = pd.read_csv('final_merged_dataset_with_RD.csv')
    df['Student Population'] = df['Student Population'].astype(str).str.replace(',', '', regex=False)
    df['Student Population'] = pd.to_numeric(df['Student Population'], errors='coerce')
    df = df.dropna(subset=['GDP_per_Capita', 'Research Quality', 'R&D Expenditure (%)'])
    
    # CBA Calculation
    # Laplace Smoothing (+1.0) is used to prevent zero-division explosions from low-investment nations.
    df['R&D Efficiency'] = df['Research Quality'] / (df['R&D Expenditure (%)'] + 1.0)
    df['R&D Efficiency'] = (df['R&D Efficiency'] / df['R&D Efficiency'].max()) * 100
    df['R&D Efficiency'] = df['R&D Efficiency'].round(2)
    return df

df_master = load_data()

# Initialize Session State
if 'df_current_rd' not in st.session_state:
    st.session_state.df_current_rd = df_master.copy()
    st.session_state.current_view_rd = "country"
    st.session_state.current_metric_rd = "R&D Efficiency"
    st.session_state.ai_message_rd = ""

# =========================================================
# 2. VISUALIZATION ENGINE
# =========================================================
def draw_dashboard(dataframe, view_type='country', metric='R&D Efficiency'):
    brush = alt.selection_interval()
    hover = alt.selection_point(on='mouseover', clear='mouseout', empty='all', fields=['Name'])
    eff_scale = alt.Scale(scheme='redyellowgreen', domain=[0, 100])

    scatter = alt.Chart(dataframe).mark_circle(opacity=0.8).encode(
        x=alt.X('GDP_per_Capita:Q', title='Context (Z): GDP per Capita ($)', scale=alt.Scale(type='log')),
        y=alt.Y('Research Quality:Q', title='Output (Y): Research Quality', scale=alt.Scale(zero=False)),
        size=alt.Size('R&D Expenditure (%):Q', title='Gov. Input: R&D (%)', scale=alt.Scale(range=[20, 400])),
        color=alt.condition(brush, alt.Color('R&D Efficiency:Q', scale=eff_scale, title="Efficiency Score"), alt.value('#e8e8e8')),
        tooltip=['Name:N', 'Country:N', 'R&D Expenditure (%):Q', 'Research Quality:Q', 'R&D Efficiency:Q']
    ).add_params(brush).properties(
        width=700, height=350, 
        title=f"1. Cost-Benefit Matrix (Total: {len(dataframe)})"
    )

    if view_type == 'country':
        bars = alt.Chart(dataframe).mark_bar().encode(
            x=alt.X('mean_score:Q', title=f'Average {metric}'),
            y=alt.Y('Country:N', sort=alt.EncodingSortField(field='mean_score', order='descending'), title='Country'),
            color=alt.Color('mean_score:Q', scale=alt.Scale(scheme='blues'), legend=None),
            tooltip=['Country:N', 'mean_score:Q', 'count_uni:Q']
        ).transform_filter(brush).transform_aggregate(
            mean_score=f'mean({metric})', count_uni='count()', groupby=['Country']
        ).transform_window(
            rank='rank(mean_score)', sort=[alt.SortField('mean_score', order='descending')]
        ).transform_filter(alt.datum.rank <= 15).properties(
            width=700, height=alt.Step(20), 
            title=f"2. Regional Aggregation: Top 15 by {metric}"
        )
    else:
        bars = alt.Chart(dataframe).mark_bar().encode(
            x=alt.X(f'{metric}:Q', title=metric),
            y=alt.Y('Name:N', sort=alt.EncodingSortField(field=metric, order='descending'), title='University'),
            color=alt.Color(f'{metric}:Q', scale=alt.Scale(scheme='blues'), legend=None),
            tooltip=['Name:N', 'Country:N', f'{metric}:Q']
        ).transform_filter(brush).transform_window(
            rank=f'rank({metric})', sort=[alt.SortField(metric, order='descending')]
        ).transform_filter(alt.datum.rank <= 25).properties( 
            width=700, height=alt.Step(15), 
            title=f"2. Institutional Rankings: Top by {metric}"
        )

    parallel = alt.Chart(dataframe).transform_filter(brush).transform_fold(
        ['R&D Expenditure (%)', 'Teaching', 'Research Quality', 'R&D Efficiency'],
        as_=['Dimension', 'Score']
    ).mark_line(interpolate='monotone', point=alt.OverlayMarkDef(size=120, filled=True, opacity=1)).encode(
        x=alt.X('Dimension:N', title=None, sort=['R&D Expenditure (%)', 'Teaching', 'Research Quality', 'R&D Efficiency']),
        y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 100]), title="Relative Score"),
        color=alt.condition(hover, alt.Color('R&D Efficiency:Q', scale=eff_scale, legend=None), alt.value('lightgray')),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.05)),
        strokeWidth=alt.condition(hover, alt.value(4), alt.value(1)),
        detail='Name:N',
        tooltip=['Name:N', 'Country:N', 'R&D Efficiency:Q']
    ).add_params(hover).properties(
        width=700, height=300, 
        title="3. The CBA Pipeline"
    )

    return scatter & bars & parallel

def query_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-3.5-flash') # Retained as per notebook
        response = model.generate_content(prompt)
        return response.text if response.parts else "{}"
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'

# =========================================================
# 3. UI LAYOUT & LOGIC
# =========================================================
st.title("🧠 Sapientia: AI-Powered Cost-Benefit Analysis")

tab1, tab2 = st.tabs(["Dashboard", "Methodological Cost-Benefit Analysis"])

with tab1:
    chart = draw_dashboard(st.session_state.df_current_rd, st.session_state.current_view_rd, st.session_state.current_metric_rd)
    st.altair_chart(chart, use_container_width=True)

    st.write("### Ask AI")
    user_req = st.text_area("What do you want to analyze?", key="rd_query", placeholder="e.g., Show me the top 15 universities sorted by R&D Efficiency")

    col1, col2, col3 = st.columns(3)
    if col1.button("Modify Study", type="primary", key="rd_mod"):
        if user_req:
            with st.spinner("AI is running complex Cost-Benefit transformations..."):
                col_list = df_master.columns.tolist()
                ai_prompt = f"""
                You are an expert Data Scientist. Columns: {col_list}. 
                User request: "{user_req}"
                Respond ONLY with a valid JSON object. No markdown.
                {{
                    "pandas_code": "Pandas chaining string starting with df_master", 
                    "view_type": "university" or "country", 
                    "metric": "R&D Efficiency"
                }}
                """
                raw_response = query_gemini(ai_prompt).strip().replace("```json", "").replace("```", "").strip()
                raw_response = re.sub(r'[\x00-\x1f]', '', raw_response) 
                
                try:
                    ai_instructions = json.loads(raw_response)
                    code_str = ai_instructions.get("pandas_code", "df_master")
                    
                    st.session_state.current_view_rd = ai_instructions.get("view_type", "country")
                    st.session_state.current_metric_rd = ai_instructions.get("metric", "R&D Efficiency")
                    st.session_state.df_current_rd = eval(code_str, {"df_master": df_master, "pd": pd})
                    st.session_state.ai_message_rd = f"**✅ Study Reconfigured!**\n\nLogic: `{code_str}`"
                    st.rerun()
                except Exception as e:
                    st.session_state.ai_message_rd = f"**❌ Analysis Error:** {e}"
                    st.rerun()

    if col2.button("Generate Hypotheses", key="rd_hyp"):
        with st.spinner("Gemini is extracting metrics and compiling hypotheses..."):
            stats = st.session_state.df_current_rd[['GDP_per_Capita', 'Research Quality', 'R&D Expenditure (%)', 'R&D Efficiency']].describe().to_string()
            ai_prompt = f"Act as a Lead Academic Researcher. Look at these stats:\n{stats}\nFormulate 3 Research Hypotheses mapping Context (GDP), Gov. Input (R&D Expenditure), Output (Research Quality), and ROI (R&D Efficiency). No markdown asterisks."
            response = query_gemini(ai_prompt)
            st.session_state.ai_message_rd = f"**💡 Active View Hypotheses:**\n\n{response}"

    if col3.button("Reset View", key="rd_reset"):
        st.session_state.df_current_rd = df_master.copy()
        st.session_state.current_view_rd = "country"
        st.session_state.current_metric_rd = "R&D Efficiency"
        st.session_state.ai_message_rd = "**🔄 View Reset.** Displaying the complete master dataset pool."
        st.rerun()

    if st.session_state.ai_message_rd:
        st.info(st.session_state.ai_message_rd)

with tab2:
    st.header("⚖️ Methodological Cost-Benefit Analysis")
    st.markdown("""
    **The Benefits:** The Sapientia VAE completely outperforms traditional lists in *Contextual Fairness* (by adjusting for GDP/R&D), *Analytical Depth*, and *Interactivity*.
    
    **The Costs:** However, this implementation trades off *Ease of Use* (Parallel Coordinates require statistical literacy) and *Data Coverage* (institutions are dropped if World Bank macroeconomic data is missing).
    """)

    cba_data = pd.DataFrame([
        {"Dimension": "Contextual Fairness", "System": "Traditional Rankings", "Score": 2},
        {"Dimension": "Contextual Fairness", "System": "Sapientia VAE", "Score": 9},
        {"Dimension": "Analytical Depth (Multi-dimensionality)", "System": "Traditional Rankings", "Score": 3},
        {"Dimension": "Analytical Depth (Multi-dimensionality)", "System": "Sapientia VAE", "Score": 10},
        {"Dimension": "Dynamic Interactivity & AI", "System": "Traditional Rankings", "Score": 0},
        {"Dimension": "Dynamic Interactivity & AI", "System": "Sapientia VAE", "Score": 10},
        {"Dimension": "Ease of Use (Low Cognitive Load)", "System": "Traditional Rankings", "Score": 9},
        {"Dimension": "Ease of Use (Low Cognitive Load)", "System": "Sapientia VAE", "Score": 5},
        {"Dimension": "Data Coverage (Independence)", "System": "Traditional Rankings", "Score": 10},
        {"Dimension": "Data Coverage (Independence)", "System": "Sapientia VAE", "Score": 7}
    ])

    lines = alt.Chart(cba_data).mark_rule(color='#ccc', strokeWidth=2).encode(
        x=alt.X('min(Score):Q', title='Performance Score (0-10)', scale=alt.Scale(domain=[0, 10])),
        x2=alt.X2('max(Score):Q'),
        y=alt.Y('Dimension:N', title=None, sort='-x')
    )

    points = alt.Chart(cba_data).mark_circle(size=250, opacity=1).encode(
        x=alt.X('Score:Q'),
        y=alt.Y('Dimension:N', sort='-x'),
        color=alt.Color('System:N', 
                        scale=alt.Scale(domain=['Traditional Rankings', 'Sapientia VAE'], 
                                        range=['#ff9999', '#1f77b4']), 
                        title='Methodology'),
        tooltip=['Dimension', 'System', 'Score']
    )

    dumbbell_chart = (lines + points).properties(
        height=300,
        title="Methodological CBA: Traditional Rankings vs. Sapientia VAE"
    ).configure_title(fontSize=16, anchor='start')

    st.altair_chart(dumbbell_chart, use_container_width=True)