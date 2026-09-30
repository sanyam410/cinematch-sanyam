import recommendation as r

# 1. What OMDb actually returned
d = r._omdb_lookup("The Godfather")
print("OMDb thinks:", d.get("Title"), "|", d.get("Year"))

# 2. What the fallback ranks — in the SAME process that just verified the code
recs = r.get_recommendations("The Godfather", 10)
print(recs[["name", "year", "similarity"]].to_string(index=False))

# 3. Where Part II landed
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as cs

def clean(v):
    v = str(v).strip()
    return "" if v.lower() in ("", "nan", "n/a") else v

rich = (f'{d["Plot"]} Genre: {d.get("Genre")}. Director: {d.get("Director")}. '
        f'Starring: {d.get("Actors")}.')
vec = r._get_model().encode([rich])
sims = cs(vec, r.embeddings)[0]
p2 = r.df.index[r.df["norm_name"] == "thegodfatherpart2"][0]
print(f"\nThe Godfather Part II: sim={sims[p2]:.4f}, rank={int((sims > sims[p2]).sum()) + 1}")
