# 🎬 Reel Insights - TMDB Movie Industry Analysis
# 🎬 Reel Insights - TMDB Movie Analytics Dashboard

**Live Demo:** https://reelinsightsmovieanalytics-nprfnh7u3wsrhk2d9xf49r.streamlit.app/

Explore movies, ratings, revenue, and trends with an interactive dashboard built with Streamlit and Python.

## Project Overview
Analysis of TMDB movies to understand what makes a movie successful.
Analyzed Budget, Revenue, Genre, Runtime, Rating, Cast & Crew.

## 📁 Project Structure
- Notebooks/ - 01_data_cleaning, 02_sql_analysis, 03_pandas_analysis, 04_visualization
- Dashboard/app.py - Streamlit App with Filters, Dashboard, Query Explorer
- Cleaned data/ - Cleaned CSV files + tmdb.sql
- Data/ - Original raw CSV files

## 🧹 Data Cleaning - Orphan Check (Final Summary)
We checked all child tables. We checked if every movie_id in child table is there in parent movies table or not.

| Child Table | Orphan Rows | Result |
| --- | --- | --- |
| movie_keywords | 0 | No orphan, Clean |
| cast | 0 | No orphan, Clean |
| crew | 0 | No orphan, Clean |
| movie_genres | 0 | No orphan, Clean |

Conclusion: All child tables have 0 orphan rows. Every movie_id matches with movies table. Data is clean and safe to load into MySQL Workbench. No rows will fail due to Foreign Key.

Loaded to MySQL using: pymysql + sqlalchemy

## Key Insights
1. Avatar is No.1: Earned 2.92 Billion, highest revenue.
2. Best Return Genres: Adventure earns highest average (390M), but Animation (83M budget -> 359M revenue) and Family (84M -> 343M) give best return for low budget.
3. Peak Year is 2016: Data from 1921 to 2026 (89 years). Most movies released in 2016.
4. Budget vs Rating = -0.13: High budget does NOT mean high rating.
5. Budget vs Revenue = 0.68, Rating vs Revenue = 0.08: Budget decides revenue, rating does NOT decide revenue.

## 🛠️ Tools Used
Python, Pandas, MySQL, MySQL Workbench, Matplotlib, Seaborn, Streamlit, VS Code

## ▶️ How to Run Dashboard
streamlit run Dashboard/app.py

## 👩‍💻 Author
Shivani - GUVI Data Science Project
GitHub: github.com/Shivani230299/Reel_Insights_Movie_Analytics
