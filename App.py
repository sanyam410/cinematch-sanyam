from flask import Flask, render_template, request, send_from_directory
from recommendation import (
    get_recommendations,
    get_genres,
    get_movies_by_genre
)
from dotenv import load_dotenv
import requests
import os
import pandas as pd
load_dotenv()

app = Flask(__name__, static_folder="Static")


OMDB_API_KEY = os.getenv("OMDB_API_KEY")


# --------------------------------------------------
# OMDb MOVIE DETAILS
# --------------------------------------------------

def get_movie_details(movie_title):

    url = "https://www.omdbapi.com/"

    params = {
        "apikey": OMDB_API_KEY,
        "t": movie_title
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("Response") == "True":
            return data

    except requests.RequestException:
        pass

    return None


# --------------------------------------------------
# SERVE IMAGES
# --------------------------------------------------

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('Static/images', filename)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route('/')
def home():
    return render_template('index.html')

# --------------------------------------------------
# EXPLORE
# --------------------------------------------------

# --------------------------------------------------
# EXPLORE
# --------------------------------------------------

@app.route("/explore")
def explore():

    selected_genre = request.args.get("genre", "All")
    selected_sort = request.args.get("sort", "rating")

    genres = get_genres()


    # Get a larger pool first so sorting
    # happens BEFORE we select the 12 movies
    movies_df = get_movies_by_genre(
        selected_genre,
        limit=1000
    )


    # ----------------------------------------------
    # SORT MOVIES
    # ----------------------------------------------

    if selected_sort == "rating":

        movies_df["sort_rating"] = pd.to_numeric(
            movies_df["imdb_rating"],
            errors="coerce"
        )

        movies_df = movies_df.sort_values(
            by="sort_rating",
            ascending=False,
            na_position="last"
        )


    elif selected_sort == "newest":

        movies_df["sort_year"] = pd.to_numeric(
            movies_df["year"],
            errors="coerce"
        )

        movies_df = movies_df.sort_values(
            by="sort_year",
            ascending=False,
            na_position="last"
        )


    elif selected_sort == "oldest":

        movies_df["sort_year"] = pd.to_numeric(
            movies_df["year"],
            errors="coerce"
        )

        movies_df = movies_df.sort_values(
            by="sort_year",
            ascending=True,
            na_position="last"
        )


    elif selected_sort == "az":

        movies_df = movies_df.sort_values(
            by="name",
            ascending=True,
            na_position="last"
        )


    # Only display 12 movies
    movies_df = movies_df.head(12)


    movies = movies_df.to_dict("records")


    # ----------------------------------------------
    # GET OMDb DETAILS
    # ----------------------------------------------

    for movie in movies:

        details = get_movie_details(movie["name"])

        if details:

            movie["poster"] = details.get("Poster")
            movie["plot"] = details.get("Plot")
            movie["omdb_rating"] = details.get("imdbRating")

        else:

            movie["poster"] = None
            movie["plot"] = None
            movie["omdb_rating"] = None


    return render_template(
        "explore.html",
        genres=genres,
        movies=movies,
        selected_genre=selected_genre,
        selected_sort=selected_sort
    )
# --------------------------------------------------
# RECOMMENDATIONS
# --------------------------------------------------

@app.route("/recommend", methods=["POST"])
def recommend():

    # Get movie name safely
    movie = request.form.get("movie", "").strip()

    # Empty search
    if not movie:
        return render_template(
            "results.html",
            movie="",
            recommendations=None,
            error="Please enter a movie name."
        )

    # Get recommendations
    try:
        results = get_recommendations(movie)

    except Exception:
        return render_template(
            "results.html",
            movie=movie,
            recommendations=None,
            error="Something went wrong while finding recommendations."
        )

    # Movie not found
    if results is None:
        return render_template(
            "results.html",
            movie=movie,
            recommendations=None,
            error=f"We couldn't find '{movie}'. Try another movie."
        )

    # No recommendations
    if results.empty:
        return render_template(
            "results.html",
            movie=movie,
            recommendations=None,
            error=f"We couldn't find any recommendations for '{movie}'."
        )

    # Convert dataframe to dictionaries
    recommendations = results.to_dict("records")


    # --------------------------------------------------
    # GET OMDb DETAILS FOR EACH RECOMMENDATION
    # --------------------------------------------------

    for recommendation in recommendations:

        details = get_movie_details(recommendation["name"])

        if details:

            recommendation["poster"] = details.get("Poster")
            recommendation["plot"] = details.get("Plot")
            recommendation["genre"] = details.get("Genre")
            recommendation["runtime"] = details.get("Runtime")
            recommendation["actors"] = details.get("Actors")
            recommendation["imdb_rating"] = details.get("imdbRating")
            recommendation["director"] = details.get("Director")

        else:

            recommendation["poster"] = None
            recommendation["plot"] = None
            recommendation["genre"] = None
            recommendation["runtime"] = None
            recommendation["actors"] = None
            recommendation["imdb_rating"] = None
            recommendation["director"] = None


    # Send recommendations to results page
    return render_template(
        "results.html",
        movie=movie,
        recommendations=recommendations,
        error=None
    )


# --------------------------------------------------
# MOVIE DETAILS PAGE
# --------------------------------------------------

@app.route("/movie/<title>")
def movie_details(title):

    details = get_movie_details(title)

    if details is None:
        return "Movie not found", 404

    return render_template(
        "movie.html",
        movie=details
    )


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)

