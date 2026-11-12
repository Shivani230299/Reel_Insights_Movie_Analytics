import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Reel Insights - TMDB Dashboard", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    base = Path(__file__).parent.parent / "Cleaned data"
    # Try both Cleaned data and cleaned_data folder names
    if not base.exists():
        base = Path(__file__).parent.parent / "Cleaned_Data"
    movies = pd.read_csv(base / "movies_clean.csv", low_memory=False)
    genres = pd.read_csv(base / "genres_clean.csv", low_memory=False)
    mg = pd.read_csv(base / "movie_genres_clean.csv", low_memory=False)
    cast = pd.read_csv(base / "cast_clean.csv", low_memory=False)
    crew = pd.read_csv(base / "crew_clean.csv", low_memory=False)
    kw = pd.read_csv(base / "movie_keywords_clean.csv", low_memory=False)
    return movies, genres, mg, cast, crew, kw

movies, genres, mg, cast_df, crew_df, kw_df = load_data()

# ---------- NORMALIZE COLUMN NAMES ----------
# Your CSVs may have id / movie_id / title / name etc. This makes code work either way
def find_col(df, options):
    for c in options:
        if c in df.columns:
            return c
    return df.columns[0]

m_id = find_col(movies, ["id", "movie_id", "movieId"])
m_title = find_col(movies, ["title", "original_title", "name"])
m_date = find_col(movies, ["release_date", "releaseDate"])
m_budget = find_col(movies, ["budget"])
m_rev = find_col(movies, ["revenue"])
m_rating = find_col(movies, ["vote_average", "rating", "voteAverage"])
m_lang = find_col(movies, ["original_language", "language"])

g_id = find_col(genres, ["id", "genre_id", "genreId"])
g_name = find_col(genres, ["name", "genre_name", "genre"])

mg_mid = find_col(mg, ["movie_id", "id"])
mg_gid = find_col(mg, ["genre_id", "id", "genreId"])

# Clean movies
movies[m_date] = pd.to_datetime(movies[m_date], errors="coerce")
movies["year"] = movies[m_date].dt.year
movies = movies.dropna(subset=[m_title])
movies[m_budget] = pd.to_numeric(movies[m_budget], errors="coerce").fillna(0)
movies[m_rev] = pd.to_numeric(movies[m_rev], errors="coerce").fillna(0)
movies[m_rating] = pd.to_numeric(movies[m_rating], errors="coerce").fillna(0)

# Merge movies + genres for filtering
movies_genres = mg.merge(genres, left_on=mg_gid, right_on=g_id, how="left")
movies_genres = movies_genres.rename(columns={mg_mid: "movie_id"})

all_genres = sorted(movies_genres[g_name].dropna().unique().tolist())
all_langs = sorted(movies[m_lang].dropna().unique().tolist())
min_year = int(movies["year"].min())
max_year = int(movies["year"].max())

# ---------- SESSION STATE FOR FILTERS ----------
if "genre_sel" not in st.session_state:
    st.session_state.genre_sel = all_genres
if "year_range" not in st.session_state:
    st.session_state.year_range = (min_year, max_year)
if "min_rating" not in st.session_state:
    st.session_state.min_rating = 0.0
if "lang_sel" not in st.session_state:
    st.session_state.lang_sel = "All"

# ---------- SIDEBAR NAVIGATION ----------
st.sidebar.title("Reel Insights")
page = st.sidebar.radio("Go to", ["Filters", "Dashboard", "Query Explorer"])
st.sidebar.markdown("---")
st.sidebar.info("Filters are saved in session_state and apply to Dashboard + Query Explorer.")

# ---------- FILTER FUNCTION ----------
def get_filtered():
    df = movies.copy()
    # Genre filter
    if st.session_state.genre_sel and len(st.session_state.genre_sel) != len(all_genres):
        ids = movies_genres[movies_genres[g_name].isin(st.session_state.genre_sel)]["movie_id"].unique()
        df = df[df[m_id].isin(ids)]
    # Year filter
    y1, y2 = st.session_state.year_range
    df = df[(df["year"] >= y1) & (df["year"] <= y2)]
    # Rating filter
    df = df[df[m_rating] >= st.session_state.min_rating]
    # Language filter
    if st.session_state.lang_sel != "All":
        df = df[df[m_lang] == st.session_state.lang_sel]
    return df

filtered = get_filtered()

# ================= PAGE 1: FILTERS =================
if page == "Filters":
    st.title("Page 1 - Filters")
    st.write("Select filters once. They will apply to Dashboard and Query Explorer.")

    st.session_state.genre_sel = st.multiselect("Select Genre", all_genres, default=st.session_state.genre_sel)
    st.session_state.year_range = st.slider("Release Year Range", min_year, max_year, value=st.session_state.year_range)
    st.session_state.min_rating = st.slider("Minimum Rating", 0.0, 10.0, value=float(st.session_state.min_rating), step=0.5)
    st.session_state.lang_sel = st.selectbox("Select Language", ["All"] + all_langs, index=(["All"] + all_langs).index(st.session_state.lang_sel))

    st.markdown("---")
    st.metric("Movies matching current filters", len(filtered))
    st.success(f"Showing {len(filtered)} movies out of {len(movies)} total movies.")
    st.dataframe(filtered[[m_title, m_date, m_rating, m_rev, m_lang]].head(20))

# ================= PAGE 2: DASHBOARD =================
elif page == "Dashboard":
    st.title("Page 2 - Dashboard")
    st.write(f"Showing results for {len(filtered)} movies with current filters.")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Movies", len(filtered))
    c2.metric("Total Genres", len(all_genres))
    # Total actors - try to find actor column
    actor_col = None
    for cand in ["name", "actor", "actor_name", "cast_name"]:
        if cand in cast_df.columns:
            actor_col = cand
            break
    total_actors = cast_df[actor_col].nunique() if actor_col else len(cast_df)
    c3.metric("Total Actors", total_actors)
    c4.metric("Average Rating", round(filtered[m_rating].mean(), 2) if len(filtered) > 0 else 0)

    st.markdown("---")
    # Top 10 by Revenue
    st.subheader("Top 10 Movies by Revenue")
    top10 = filtered.sort_values(m_rev, ascending=False).head(10)
    fig1 = px.bar(top10, x=m_title, y=m_rev, color=m_rev, title="Top 10 by Revenue")
    st.plotly_chart(fig1, use_container_width=True)

    # Genre distribution + Budget vs Revenue
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Genre Distribution")
        genre_counts = movies_genres[movies_genres["movie_id"].isin(filtered[m_id])][g_name].value_counts().reset_index()
        genre_counts.columns = ["Genre", "Count"]
        fig2 = px.pie(genre_counts, names="Genre", values="Count")
        st.plotly_chart(fig2, use_container_width=True)
    with colB:
        st.subheader("Budget vs Revenue")
        fig3 = px.scatter(filtered, x=m_budget, y=m_rev, hover_data=[m_title], opacity=0.6)
        st.plotly_chart(fig3, use_container_width=True)

    # Insight
    if len(genre_counts) > 0:
        top_genre = genre_counts.iloc[0]["Genre"]
        st.info(f"Insight: Highest count genre in filtered data is {top_genre}. Top grossing movie is {top10.iloc[0][m_title]} with revenue {top10.iloc[0][m_rev]:,.0f}.")

# ================= PAGE 3: QUERY EXPLORER =================
else:
    st.title("Page 3 - Query Explorer")
    st.write("Select any of your 10 SQL questions. Result is calculated from your Cleaned CSVs.")

    # Prepare helper dataframes
    cast_actor = None
    for cand in ["name", "actor", "actor_name", "cast_name"]:
        if cand in cast_df.columns:
            cast_actor = cand
            break
    cast_mid = None
    for cand in ["movie_id", "id"]:
        if cand in cast_df.columns:
            cast_mid = cand
            break
    crew_name_col = None
    for cand in ["name", "crew_name", "person_name"]:
        if cand in crew_df.columns:
            crew_name_col = cand
            break
    crew_mid = None
    for cand in ["movie_id", "id"]:
        if cand in crew_df.columns:
            crew_mid = cand
            break
    crew_job = None
    for cand in ["job", "department", "role"]:
        if cand in crew_df.columns:
            crew_job = cand
            break
    kw_col = None
    for cand in ["keyword", "name", "keyword_name"]:
        if cand in kw_df.columns:
            kw_col = cand
            break
    kw_mid = None
    for cand in ["movie_id", "id"]:
        if cand in kw_df.columns:
            kw_mid = cand
            break

    questions = [
        "Q1: Action movies released after 2015",
        "Q2: Top 10 highest-grossing movies + genre",
        "Q3: Average budget + revenue for each genre",
        "Q4: Top 10 actors in most movies",
        "Q5: Directors with more than 3 movies",
        "Q6: Top 10 most frequent keywords",
        "Q7: High budget but low revenue movies",
        "Q8: Actors in Christopher Nolan movies",
        "Q9: Genre with highest average rating (min 20 movies)",
        "Q10: Top 10 movies with most keywords",
    ]
    choice = st.selectbox("Choose a Query", questions)

    result = pd.DataFrame()
    insight = ""
    chart = None

    if choice.startswith("Q1"):
        action_ids = movies_genres[movies_genres[g_name] == "Action"]["movie_id"].unique()
        result = filtered[(filtered[m_id].isin(action_ids)) & (filtered["year"] > 2015)][[m_title, m_date]]
        insight = f"Found {len(result)} Action movies after 2015 in filtered data."
        if len(result) > 0:
            chart = px.bar(result.head(10), x=m_title, y=m_date)

    elif choice.startswith("Q2"):
        temp = filtered.copy()
        # attach genre names
        genre_map = movies_genres.groupby("movie_id")[g_name].apply(lambda x: ", ".join(x)).reset_index()
        temp = temp.merge(genre_map, left_on=m_id, right_on="movie_id", how="left")
        result = temp.sort_values(m_rev, ascending=False).head(10)[[m_title, g_name, m_rev]]
        insight = f"Top movie is {result.iloc[0][m_title]} with revenue {result.iloc[0][m_rev]:,.0f}."
        chart = px.bar(result, x=m_title, y=m_rev)

    elif choice.startswith("Q3"):
        merged = movies_genres.merge(movies, left_on="movie_id", right_on=m_id, how="inner")
        result = merged.groupby(g_name).agg(avg_budget=(m_budget, "mean"), avg_revenue=(m_rev, "mean")).reset_index().sort_values("avg_revenue", ascending=False)
        insight = f"Highest average revenue genre is {result.iloc[0][g_name]}."
        chart = px.bar(result, x=g_name, y="avg_revenue")

    elif choice.startswith("Q4"):
        result = cast_df.groupby(cast_actor).size().reset_index(name="movie_count").sort_values("movie_count", ascending=False).head(10)
        insight = f"Most frequent actor is {result.iloc[0][cast_actor]} with {result.iloc[0]['movie_count']} movies."
        chart = px.bar(result, x=cast_actor, y="movie_count")

    elif choice.startswith("Q5"):
        directors = crew_df[crew_df[crew_job].astype(str).str.contains("Director", case=False, na=False)]
        result = directors.groupby(crew_name_col).size().reset_index(name="movie_count")
        result = result[result["movie_count"] > 3].sort_values("movie_count", ascending=False)
        insight = f"Found {len(result)} directors with more than 3 movies."
        chart = px.bar(result.head(10), x=crew_name_col, y="movie_count")

    elif choice.startswith("Q6"):
        result = kw_df.groupby(kw_col).size().reset_index(name="count").sort_values("count", ascending=False).head(10)
        insight = f"Most used keyword is {result.iloc[0][kw_col]}."
        chart = px.bar(result, x=kw_col, y="count")

    elif choice.startswith("Q7"):
        avg_b = movies[m_budget].mean()
        avg_r = movies[m_rev].mean()
        result = filtered[(filtered[m_budget] > avg_b) & (filtered[m_rev] < avg_r)][[m_title, m_budget, m_rev]]
        insight = f"Average budget is {avg_b:,.0f}, average revenue is {avg_r:,.0f}. Found {len(result)} movies with high budget but low revenue."
        chart = px.scatter(result, x=m_budget, y=m_rev, hover_data=[m_title])

    elif choice.startswith("Q8"):
        nolan_ids = crew_df[(crew_df[crew_name_col] == "Christopher Nolan")][crew_mid].unique()
        result = cast_df[cast_df[cast_mid].isin(nolan_ids)][cast_actor].drop_duplicates().reset_index(drop=True)
        result.columns = ["Actor"]
        insight = f"Found {len(result)} actors who worked with Christopher Nolan."

    elif choice.startswith("Q9"):
        merged = movies_genres.merge(movies, left_on="movie_id", right_on=m_id, how="inner")
        agg = merged.groupby(g_name).agg(avg_rating=(m_rating, "mean"), movie_count=(m_id, "count")).reset_index()
        agg = agg[agg["movie_count"] >= 20].sort_values("avg_rating", ascending=False)
        result = agg
        if len(result) > 0:
            insight = f"Highest rated genre (min 20 movies) is {result.iloc[0][g_name]} with rating {result.iloc[0]['avg_rating']:.2f}."
            chart = px.bar(result, x=g_name, y="avg_rating")

    elif choice.startswith("Q10"):
        result = kw_df.groupby(kw_mid).size().reset_index(name="keyword_count").sort_values("keyword_count", ascending=False).head(10)
        result = result.merge(movies[[m_id, m_title]], left_on=kw_mid, right_on=m_id, how="left")
        result = result[[m_title, "keyword_count"]]
        insight = f"Movie with most keywords is {result.iloc[0][m_title]} with {result.iloc[0]['keyword_count']} keywords."
        chart = px.bar(result, x=m_title, y="keyword_count")

    st.dataframe(result, use_container_width=True)
    if chart is not None:
        st.plotly_chart(chart, use_container_width=True)
    st.info(f"Insight: {insight}")
    st.caption("Source: Cleaned CSVs in Cleaned data folder. Same logic as your SQL queries in Notebook 2.")