# 🎬 CineMatch

> **Find something worth watching.** A semantic movie-recommendation engine that understands *plots*, not just genres — wrapped in a cinematic web experience for people who love films.

**🔗 Live demo:** [https://cinematch-sanyam.onrender.com](https://cinematch-sanyam.onrender.com) <!-- ← replace with your final Render URL -->

<!-- Optional: add a screenshot, commit it as docs/screenshot.png, then uncomment:
![CineMatch homepage](docs/screenshot.png)
-->

---

## ✨ What it does

- **🔎 Semantic recommendations** — type any movie and get films *whose stories feel similar*, powered by sentence-level plot embeddings and cosine similarity — not shallow genre matching
- **🧠 Smart title matching** — typos, sequel numbering (`godfather part 2`), and year hints (`heat of 95`) all resolve correctly, with fuzzy matching and a strict no-wrong-sequel guard
- **🌍 Explore** — browse the library filtered by genre, sorted by rating, year, or A–Z
- **🎞️ The Cinephile's Corner** — the homepage serves daily-rotated film lore: behind-the-scenes facts, iconic lines, and "on this day" cinema history
- **🛟 Out-of-library fallback** — movies missing from the dataset are fetched from OMDb and recommended *by plot meaning* in real time (local installs; see limitations)
- **⚡ Fast** — recommendations are pure vector math on precomputed embeddings; OMDb calls are cached

## ⚙️ How the recommender works

```
"heat of 95" ──▶ title matcher ──▶ Heat (1995)
                                    │
                     plot embedding (384-dim vector)
                                    │
                 cosine similarity vs. every film ──▶ + director bonus
                                    │              + lead-actor bonus
                                    │              + shared-genre bonus
                                    ▼
                     top 5 ranked by final score ──▶ results page
```

1. **Offline (Step_2.ipynb):** every movie's plot is embedded with `all-MiniLM-L6-v2` (SentenceTransformers) and saved to `movie_embeddings.npy` — row *i* matches row *i* of `Clean_Data.csv`
2. **At request time:** the input title is normalized (roman numerals, spacing, year hints) and matched exactly, then fuzzily (RapidFuzz `token_sort_ratio`, threshold-guarded)
3. **Scoring:** `final_score = plot_similarity + 0.05·same_director + 0.03·same_lead + 0.04·max shared genres`
4. **Fallback:** if the title isn't in the library, its OMDb plot is embedded on the fly and compared against the whole matrix — the same semantic space, so it just works

## 🧰 Tech stack

| Layer | Tools |
|---|---|
| Backend | Python · Flask · Gunicorn |
| ML / Data | SentenceTransformers (`all-MiniLM-L6-v2`) · NumPy · scikit-learn · pandas |
| Matching | RapidFuzz |
| Metadata | OMDb API (posters, plots, ratings — LRU-cached) |
| Frontend | Jinja2 templates · custom CSS (dark cinematic theme) |
| Hosting | Render (free tier) |

## 📁 Project structure

```
├── App.py                  # Flask routes: home, explore, recommend, details
├── recommendation.py       # matching + embedding-based recommender + OMDb fallback
├── cinephile.py            # daily film facts, quotes & history for the homepage
├── Clean_Data.csv          # the movie library (titles, years, cast, plots…)
├── movie_embeddings.npy    # precomputed plot embeddings (aligned with the CSV)
├── Step_2.ipynb            # notebook that generates the embeddings
├── templates/              # Jinja2 pages
└── Static/                 # CSS & assets
```

## 🚀 Run it locally

```bash
git clone https://github.com/sanyam410/cinematch.git
cd cinematch
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
OMDB_API_KEY=your_key_here      # free key: https://www.omdbapi.com/apikey.aspx
SECRET_KEY=any_long_random_string
```

```bash
python App.py
```

Open **http://127.0.0.1:5000** — try `Inception`, `godfather part 2`, or `heat of 95`.

> 💡 The OMDb-plot fallback uses `sentence-transformers`, which isn't in `requirements.txt` by default (it's heavy). To enable it locally: `pip install sentence-transformers`.

## 🌐 Deployment notes (Render free tier)

- Build: `pip install -r requirements.txt` · Start: `gunicorn App:app --workers 1 --threads 2 --timeout 120`
- The dataset and embeddings live in the repo, so deploys are self-contained
- **Known free-tier limits:** 512 MB RAM means the on-the-fly embedding fallback is disabled in production (local searches all work), and the service sleeps after 15 min idle — the first visit afterwards takes ~1 min to wake up

## 🔮 Roadmap

- [ ] Title autocomplete while typing
- [ ] "More like this" from every movie details page
- [ ] User watchlists
- [ ] Cinephile quiz mode (guess the film from hints)

## 🙏 Credits

- Metadata & posters: [OMDb API](https://www.omdbapi.com/)
- Embeddings: [SentenceTransformers](https://www.sbert.net/)
- Dataset built from IMDb data

---

*Built with 🍿 and an unhealthy knowledge of the Wilhelm Scream by [sanyam410](https://github.com/sanyam410).*
