import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import json

st.set_page_config(page_title="Sapientia VAE - Overall", layout="wide")

# =========================================================
# 1. SETUP & DATA LOADING
# =========================================================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

@st.cache_data
def load_data():
    df = pd.read_csv('final_merged_dataset.csv')
    df['Student Population'] = df['Student Population'].astype(str).str.replace(',', '', regex=False)
    df['Student Population'] = pd.to_numeric(df['Student Population'], errors='coerce')
    df = df.dropna(subset=['GDP_per_Capita', 'Research Quality', 'Student Population'])
    return df

df_master = load_data()

# Initialize Session State
if 'df_current' not in st.session_state:
    st.session_state.df_current = df_master.copy()
    st.session_state.current_view = "country"
    st.session_state.current_metric = "Overall Score"
    st.session_state.ai_message = ""

# =========================================================
# 2. VISUALIZATION ENGINE
# =========================================================
def draw_dashboard(dataframe, view_type='country', metric='Overall Score'):
    brush = alt.selection_interval()
    color_scale = alt.Scale(scheme='category20')
    hover = alt.selection_point(on='mouseover', clear='mouseout', empty='all', fields=['Name'])

    # 1. SCATTER PLOT
    scatter = alt.Chart(dataframe).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X('GDP_per_Capita:Q', title='Context (Z): GDP per Capita ($)', scale=alt.Scale(type='log')),
        y=alt.Y('Research Quality:Q', title='Output (Y): Research Quality', scale=alt.Scale(zero=False)),
        size=alt.Size('Student Population:Q', title='Input (X): Student Pop.', scale=alt.Scale(range=[10, 500])),
        color=alt.condition(brush, 'Country:N', alt.value('#e0e0e0'), scale=color_scale, legend=None),
        tooltip=['Name:N', 'Country:N', 'Rank:Q', 'Research Quality:Q', 'GDP_per_Capita:Q']
    ).add_params(brush).properties(
        width=700, height=350, 
        title=f"1. Sapientia VAE Overview (Total Universities: {len(dataframe)})"
    )

    # 2. DYNAMIC BAR CHART
    if view_type == 'country':
        bars = alt.Chart(dataframe).mark_bar().encode(
            x=alt.X('mean_score:Q', title=f'Average {metric}'),
            y=alt.Y('Country:N', sort=alt.EncodingSortField(field='mean_score', order='descending'), title='Country'),
            color=alt.Color('Country:N', scale=color_scale, legend=None),
            tooltip=['Country:N', 'mean_score:Q', 'count_uni:Q']
        ).transform_filter(brush).transform_aggregate(
            mean_score=f'mean({metric})', count_uni='count()', groupby=['Country']
        ).transform_window(
            rank='rank(mean_score)', sort=[alt.SortField('mean_score', order='descending')]
        ).transform_filter(alt.datum.rank <= 15).properties(
            width=700, height=alt.Step(20), 
            title=f"2. Country Aggregation: Top 15 by {metric}"
        )
    else:
        bars = alt.Chart(dataframe).mark_bar().encode(
            x=alt.X(f'{metric}:Q', title=metric),
            y=alt.Y('Name:N', sort=alt.EncodingSortField(field=metric, order='descending'), title='University'),
            color=alt.Color('Country:N', scale=color_scale, legend=None),
            tooltip=['Name:N', 'Country:N', f'{metric}:Q']
        ).transform_filter(brush).transform_window(
            rank=f'rank({metric})', sort=[alt.SortField(metric, order='descending')]
        ).transform_filter(alt.datum.rank <= 25).properties( 
            width=700, height=alt.Step(15), 
            title=f"2. University Rankings: Top by {metric}"
        )

    # 3. PARALLEL COORDINATES
    parallel = alt.Chart(dataframe).transform_filter(brush).transform_fold(
        ['Teaching', 'Research Environment', 'Research Quality', 'Industry Impact', 'International Outlook'],
        as_=['Dimension', 'Score']
    ).mark_line(interpolate='monotone', point=alt.OverlayMarkDef(size=120, filled=True, opacity=1)).encode(
        x=alt.X('Dimension:N', title=None, axis=alt.Axis(labelAngle=-15)),
        y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 100]), title="Score (0-100)"),
        color=alt.condition(hover, 'Country:N', alt.value('lightgray'), scale=color_scale, legend=None),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.05)),
        strokeWidth=alt.condition(hover, alt.value(4), alt.value(1)),
        detail='Name:N',
        tooltip=['Name:N', 'Country:N', 'Overall Score:Q']
    ).add_params(hover).properties(
        width=700, height=300, 
        title="3. Parallel Coordinates"
    )

    return scatter & bars & parallel

def query_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-3.5-flash')
        response = model.generate_content(prompt)
        return response.text if response.parts else "{}"
    except Exception as e:
        return f'{{"error": "{e}"}}'

# =========================================================
# 3. UI LAYOUT & LOGIC
# =========================================================
st.title("🧠 Sapientia: AI-Driven Analytics Dashboard")

# Render Chart directly
chart = draw_dashboard(st.session_state.df_current, st.session_state.current_view, st.session_state.current_metric)
st.altair_chart(chart, use_container_width=True)

st.write("### Ask AI")
user_req = st.text_area("What do you want to analyze?", placeholder="e.g., Show me the top 10 universities sorted by Research Quality")

col1, col2, col3 = st.columns(3)

if col1.button("Modify Study", type="primary"):
    if user_req:
        with st.spinner("AI is parsing your request and compiling pandas code..."):
            col_list = df_master.columns.tolist()
            ai_prompt = f"""
            You are an expert Data Scientist and UI Orchestrator. 
            Available columns: {col_list}
            User request: "{user_req}"
            
            Respond ONLY with a valid JSON object. Do not include markdown code blocks.
            {{
                "pandas_code": "Pandas method chaining string starting with df_master",
                "view_type": "university", 
                "metric": "Overall Score" 
            }}
            """
            
            raw_response = query_gemini(ai_prompt).strip()
            raw_response = raw_response.replace("```json", "").replace("```", "").strip()
            
            try:
                ai_instructions = json.loads(raw_response)
                code_str = ai_instructions.get("pandas_code", "df_master")
                
                st.session_state.current_view = ai_instructions.get("view_type", "country")
                st.session_state.current_metric = ai_instructions.get("metric", "Overall Score")
                st.session_state.df_current = eval(code_str, {"df_master": df_master, "pd": pd})
                st.session_state.ai_message = f"**✅ Dashboard Reconfigured!**\n\nLogic Used: `{code_str}`"
                
                st.rerun()  # Forces proper reload to update charts
            except Exception as e:
                st.session_state.ai_message = f"**❌ Error:** {e}\n\nAI Output: `{raw_response}`"
                st.rerun()

if col2.button("Generate Hypotheses"):
    with st.spinner("Gemini is extracting metrics and compiling hypotheses..."):
        stats = st.session_state.df_current[['GDP_per_Capita', 'Research Quality', 'Student Population']].describe().to_string()
        ai_prompt = f"Act as a Lead Academic Researcher. Review the statistical profile of this subset of universities:\n{stats}\nFormulate exactly 3 testable Research Hypotheses mapping Context (Z: GDP), Output (Y: Research Quality), and Input (X: Student Population). Maintain an academic tone. Do not use asterisks or markdown formatting."
        response = query_gemini(ai_prompt)
        st.session_state.ai_message = f"**💡 Active View Hypotheses:**\n\n{response}"

if col3.button("Reset View"):
    st.session_state.df_current = df_master.copy()
    st.session_state.current_view = "country"
    st.session_state.current_metric = "Overall Score"
    st.session_state.ai_message = "**🔄 View Reset.** Displaying the complete master dataset pool."
    st.rerun()

# Display AI Messages
if st.session_state.ai_message:
    st.info(st.session_state.ai_message)
