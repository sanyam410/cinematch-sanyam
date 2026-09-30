import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
from sklearn.metrics.pairwise import cosine_similarity
import os
import requests
from dotenv import load_dotenv
import re
from functools import lru_cache

load_dotenv()

BASE = os.path.dirname(__file__)
df = pd.read_csv(os.path.join(BASE, "Clean_Data.csv"))
embeddings = np.load(os.path.join(BASE, "movie_embeddings.npy"))

# Fails fast if CSV rows and embedding rows ever get out of sync
assert len(df) == embeddings.shape[0], (
    f"Row mismatch: CSV has {len(df)} rows but embeddings have "
    f"{embeddings.shape[0]} — rebuild movie_embeddings.npy from this CSV."
)

df["year"] = pd.to_numeric(df["year"], errors="coerce")


def normalize(title):
    title = str(title).lower().strip()
    title = re.sub(r'[:\---]', '', title)
    roman_to_num = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5"}

    def convert_part(match):
        num = match.group(1).lower()
        return f'part{roman_to_num.get(num, num)}'

    # "part II" → "part2" BEFORE spaces are stripped
    title = re.sub(r'\bpart\s+(i{1,3}|iv|v|\d+)\b', convert_part, title)
    title = re.sub(r'\s+', '', title).strip()
    return title


df["norm_name"] = df["name"].apply(normalize)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer   # always available (HF / local)
    return SentenceTransformer("all-MiniLM-L6-v2")


def find_local(title, threshold=85):
    # "1917", "2012", "1984" → movie TITLES, not year filters
    if re.fullmatch(r'(19|20)\d{2}', str(title).strip()):
        candidates = df["norm_name"]
        query = normalize(title)
        exact = candidates[candidates == query]
        if len(exact) > 0:
            return exact.index[0]
        match = process.extractOne(query, candidates, scorer=fuzz.token_sort_ratio)
        if match is None or match[1] < threshold:
            return None
        return match[2]

    query = normalize(title)
    raw_query = str(title).lower().strip()   # SPACED form, used by guard 5
    candidates = df["norm_name"]

    # Year hint: "godfather 1990" / "heat of 95" → the year MUST match
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if not year_match:
        short_year_match = re.search(r'\bof\s+(\d{2})\b', title)
        if short_year_match:
            short_year = int(short_year_match.group(1))
            year = 2000 + short_year if short_year <= 30 else 1900 + short_year
            title_without_year = re.sub(r'\bof\s+\d{2}\b', '', title, count=1)
            query = normalize(title_without_year)
            raw_query = title_without_year.lower().strip()
            candidates = candidates[df["year"] == year]
            if len(candidates) == 0:
                return None
    else:
        title_without_year = re.sub(r'\b(19|20)\d{2}\b', '', title).strip()
        if title_without_year:
            year = int(year_match.group())
            query = normalize(title_without_year)
            raw_query = title_without_year.lower().strip()
            candidates = candidates[df["year"] == year]
            if len(candidates) == 0:
                return None

    # 1. Exact match FIRST
    exact_matches = candidates[candidates == query]
    if len(exact_matches) > 0:
        return exact_matches.index[0]

    # 2. Explicit Part number → NEVER fuzzy (raw title; query has no spaces)
    if re.search(r'\bpart\s+(?:i{1,3}|iv|v|\d+)\b', title.lower()):
        return None

    # 3. Fuzzy matching for typos
    match = process.extractOne(query, candidates, scorer=fuzz.token_sort_ratio)
    if match is None or match[1] < threshold:
        return None

    # 4. Sequel-absorption guard: base title typed, but best match is
    #    title + number OR roman numeral
    #    ("the godfather" → "Part III", "halloween" → "Halloween II")
    matched_name = str(df.loc[match[2], "norm_name"])
    if (matched_name != query and matched_name.startswith(query)
            and re.search(r'(?:\d+|[ivx]+)$', matched_name)):
        return None                       # → falls through to OMDb fallback

    # 5. Word-level sanity check on SPACED titles:
    #    "the godfather" must never become "The Good Father"
    #    (spaceless strings differ by one letter → ~96 similarity)
    raw_name = str(df.loc[match[2], "name"]).lower()
    if fuzz.token_sort_ratio(raw_query, raw_name) < 80:
        return None                       # → falls through to OMDb fallback

    return match[2]


def recommend(idx, top_n=5):
    """Given a row index, find its top_n most similar movies by plot embedding."""
    query_vec = embeddings[idx].reshape(1, -1)
    sims = cosine_similarity(query_vec, embeddings)[0]
    results = df.copy()
    results['similarity'] = sims
    results['bonus'] = 0.0
    results.loc[results['director'] == df.iloc[idx]['director'], 'bonus'] += 0.05
    results.loc[results['lead_actor'] == df.iloc[idx]['lead_actor'], 'bonus'] += 0.03
    if "genre" in df.columns:
        query_genres = set(str(df.iloc[idx]['genre']).lower().split(", "))
        for movie_idx in results.index:
            movie_genres = set(str(results.loc[movie_idx]['genre']).lower().split(", "))
            shared_genres = query_genres & movie_genres
            results.loc[movie_idx, "bonus"] += min(0.02 * len(shared_genres), 0.04)

    results['final_score'] = results['similarity'] + results['bonus']
    results = results.drop(index=idx)
    results = results.sort_values(by='final_score', ascending=False).head(top_n)
    return results[['name', 'year', 'lead_actor', 'director', 'imdb_rating',
                    'plot', 'similarity', 'bonus', 'final_score']]


# --------------------------------------------------
# OMDb FALLBACK (movies not in our dataset)
# --------------------------------------------------
def _omdb_lookup(title):
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        return None
    try:
        r = requests.get(
            "https://www.omdbapi.com/",
            params={"apikey": api_key, "t": title},
            timeout=10,
        )
        data = r.json()
        if data.get("Response") == "True":
            return data
    except requests.RequestException:
        pass
    return None


def get_recommendations_by_plot(plot_text, top_n=5):
    """Recommend local movies whose plots are closest to plot_text."""
    vec = _get_model().encode([plot_text])[0].reshape(1, -1)
    sims = cosine_similarity(vec, embeddings)[0]

    top = np.argsort(sims)[::-1][:top_n]
    results = df.iloc[top][
        ["name", "year", "lead_actor", "director", "imdb_rating", "plot"]
    ].copy()
    results["similarity"] = sims[top]
    results["bonus"] = 0.0
    results["final_score"] = results["similarity"]
    results["year"] = pd.to_numeric(results["year"], errors="coerce").astype("Int64")
    return results.reset_index(drop=True)


def get_recommendations(title, top_n=5):
    idx = find_local(title)
    if idx is not None:
        return recommend(idx, top_n)

    # ---- FALLBACK: not in dataset → embed its OMDb plot ----
    lookup_title = title.strip()
    details = _omdb_lookup(lookup_title)
    if details is None:
        cleaned = re.sub(r'\((19|20)\d{2}\)|\bmovie\s+(19|20)\d{2}\b',
                         '', lookup_title).strip()
        if cleaned and cleaned != lookup_title:
            lookup_title = cleaned
            details = _omdb_lookup(lookup_title)
    if details and details.get("Plot") not in (None, "", "N/A"):
        query_text = (
            f'{details["Plot"]} '
            f'Genre: {details.get("Genre", "")}. '
            f'Director: {details.get("Director", "")}. '
            f'Starring: {details.get("Actors", "")}.'
        )
        return get_recommendations_by_plot(query_text, top_n)
    return None


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
        ["name", "year", "lead_actor", "director", "imdb_rating", "genre"]
    ]
