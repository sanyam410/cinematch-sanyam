import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
from sklearn.metrics.pairwise import cosine_similarity
import os
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import re

df = pd.read_csv("Clean_Data.csv")
embeddings  = np.load("movie_embeddings.npy")

model = SentenceTransformer("all-MiniLM-L6-v2")

def normalize(title):
    title = str(title).lower().strip()
    title=re.sub(r'[:\---]','',title)
    roman_to_num={"i":"1","ii":"2","iii":"3","iv":"4","v":"5"}
    def convert_part(match):
        num=match.group(1).lower()
        return f'part{roman_to_num.get(num, num)}'
        title=re.sub(r'\bpart\s+(i{1,3}|iv|v|\d+)\b)', convert_part,title)
        title=re.sub(r'\s+','',title).strip()
        
    return title

def find_local(title, threshold=85):
    query = normalize(title)
    candidates = df["name"].apply(normalize)

    # If user supplied a year, it MUST match
    year_match = re.search(r'\b(19|20)\d{2}\b', title)

    # Also understand "Heat of 95" / "Heat 95"
    if not year_match:
        short_year_match = re.search(r'\b(?:of\s+)?(\d{2})\b', title)

        if short_year_match:
            short_year = int(short_year_match.group(1))

            if short_year <= 30:
                year = 2000 + short_year
            else:
                year = 1900 + short_year

            title_without_year = re.sub(
                r'\b(?:of\s+)?\d{2}\b',
                '',
                title,
                count=1
            )

            query = normalize(title_without_year)

            candidates = candidates[df["year"] == year]

            # Requested year doesn't exist → DON'T fuzzy-match another year
            if len(candidates) == 0:
                return None

    else:
        year = int(year_match.group())

        title_without_year = re.sub(
            r'\b(19|20)\d{2}\b',
            '',
            title
        )

        query = normalize(title_without_year)

        candidates = candidates[df["year"] == year]

        # Requested year doesn't exist → DON'T fuzzy-match another year
        if len(candidates) == 0:
            return None

    # 1. Exact match FIRST
    exact_matches = candidates[candidates == query]

    if len(exact_matches) > 0:
        return exact_matches.index[0]

    # 2. If user explicitly gave a Part number,
    #    NEVER use fuzzy matching
    if re.search(r'\bpart\b', query):
        return None

    # 3. Fuzzy matching only for normal titles / typos
    match = process.extractOne(
        query,
        candidates,
        scorer=fuzz.token_sort_ratio
    )

    if match is None or match[1] < threshold:
        return None

    return match[2]

    return match[2]

def recommend(idx, top_n=5):
    """Given a row index, find its top_n most similar movies by plot embedding."""
    query_vec = embeddings[idx].reshape(1, -1)
    sims = cosine_similarity(query_vec, embeddings)[0]
    results=df.copy()
    results['similarity']=sims
    results['bonus']=0.0
    results.loc[results['director']==df.iloc[idx]['director'],'bonus']+=0.05
    results.loc[results['lead_actor']==df.iloc[idx]['lead_actor'],'bonus']+=0.03
    if "genre" in df.columns:
        query_genres = set(str(df.iloc[idx]['genre']).lower().split(", "))
        for movie_idx in results.index:
                movie_genres = set(str(results.loc[movie_idx]['genre']).lower().split(", "))
                shared_genres = query_genres & movie_genres
                genre_bonus = min(0.02 * len(shared_genres), 0.04)
                results.loc[movie_idx, "bonus"] += genre_bonus
           
    results['final_score']=results['similarity']+results['bonus']
    results=results.drop(index=idx)
    results=results.sort_values(by='final_score',ascending=False).head(top_n)
    return results[['name','year','lead_actor','director','imdb_rating','plot','similarity','bonus','final_score']]
    
def get_recommendations(title, top_n=5):
    idx = find_local(title)

    if idx is None:
        return None

    results = recommend(idx, top_n)

    return results
# --------------------------------------------------
# EXPLORE PAGE
# --------------------------------------------------

def get_genres():

    if "genre" not in df.columns:
        return []

    genres = set()

    for value in df["genre"].dropna():

        for genre in str(value).split(","):

            genre = genre.strip()

            if genre:
                genres.add(genre)

    return sorted(genres)


def get_movies_by_genre(genre=None, limit=12):

    movies = df.copy()

    if genre and genre.lower() != "all":

        movies = movies[
            movies["genre"]
            .fillna("")
            .str.lower()
            .str.contains(genre.lower(), regex=False)
        ]

    return movies.head(limit)[
        [
            "name",
            "year",
            "lead_actor",
            "director",
            "imdb_rating",
            "genre"
        ]
    ]

print(get_recommendations("Inception"))