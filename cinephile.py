from datetime import date

FACTS = [
    "The blood in Psycho's shower scene was chocolate syrup — and the film is widely credited as the first major American movie to show a toilet flush.",
    "Jaws' mechanical shark was nicknamed Bruce, kept breaking down, and its failures forced Spielberg to suggest the shark — the greatest suspense decision in cinema.",
    "The cat in The Godfather's opening scene was a stray found on the Paramount lot — and its purring accidentally ruined the first take's sound.",
    "Parasite (2019) became the first non-English-language film to win Best Picture in Oscar history.",
    "The Return of the King won all 11 Academy Awards it was nominated for — a perfect score.",
    "The very first Academy Awards ceremony (1929) was a 15-minute dinner event — winners had been announced three months earlier.",
    "\"You're gonna need a bigger boat\" in Jaws was improvised by Roy Scheider from a crew in-joke about the tiny support barge.",
    "The Wilhelm Scream — heard in Star Wars, Indiana Jones and 400+ films — was recorded in 1951 for Distant Drums.",
    "Robert De Niro gained about 60 pounds to play Jake LaMotta in Raging Bull.",
    "Heath Ledger's Joker won the second posthumous acting Oscar ever, after Peter Finch in 1976.",
    "Whiplash was shot in just 19 days.",
    "In the 2022 Sight & Sound poll, critics crowned Jeanne Dielman the greatest film ever made, dethroning Vertigo after 40 years.",
]

QUOTES = [
    ("Here's looking at you, kid.", "Casablanca", 1942),
    ("I'm gonna make him an offer he can't refuse.", "The Godfather", 1972),
    ("You talkin' to me?", "Taxi Driver", 1976),
    ("May the Force be with you.", "Star Wars", 1977),
    ("I'll be back.", "The Terminator", 1984),
    ("Rosebud.", "Citizen Kane", 1941),
    ("There's no place like home.", "The Wizard of Oz", 1939),
    ("I see dead people.", "The Sixth Sense", 1999),
    ("Why so serious?", "The Dark Knight", 2008),
    ("To infinity, and beyond!", "Toy Story", 1995),
]

ON_THIS_DAY = {  # (month, day): (year, event) — label the event type precisely
    (12, 28): (1895, "the Lumière brothers held the first paid public film screening, in Paris"),
    (5, 25):  (1977, "Star Wars opened in theaters"),
    (5, 16):  (1929, "the first Academy Awards ceremony was held"),
    (12, 15): (1939, "Gone with the Wind premiered in Atlanta"),
    (3, 2):   (1933, "King Kong premiered at Radio City Music Hall"),
    (11, 13): (1940, "Fantasia premiered in New York"),
    (6, 16):  (1960, "Psycho premiered in New York"),
    (7, 15):  (1988, "Die Hard opened in U.S. theaters"),
    (6, 11):  (1982, "E.T. the Extra-Terrestrial opened in theaters"),
    (11, 18): (1928, "Steamboat Willie debuted — Mickey Mouse's first synchronized-sound cartoon"),
}

def daily_content():
    day = date.today().timetuple().tm_yday
    fact = FACTS[day % len(FACTS)]
    quote = QUOTES[(day + 3) % len(QUOTES)]          # offset so quote ≠ fact index
    today = ON_THIS_DAY.get((date.today().month, date.today().day))
    return {"fact": fact, "quote": quote, "today": today,
            "fallback_fact": FACTS[(day + 7) % len(FACTS)]}

