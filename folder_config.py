"""Single place for ClickUp folder labels, report tags, and planned hours."""

# Raw ClickUp folder name -> internal name (synced with database / webhooks)
FOLDER_MAP = {
    "Games / PS5": "ComputerGames",
    "Love life / Tinder ": "LoveLifeTinder",
    "Job looking / CV": "JobLookingCV",
    "Master's degree ": "MastersDegree",
    "Programming / Projects": "ProgrammingProjects",
    "Cooking": "Cooking",
    "Comarch": "Comarch",
    "Comarch Actual Work": "ComarchActualWork",
    "Guitar": "Guitar",
    "Gym/Sports": "GymSports",
    "Improvement": "Improvement",
    "Audiobook": "Audiobook",
    "Family Social Life": "FamilySocialLife",
    "Book": "Book",
    "Watching Serials / Movies / Football games": "TvShows",
    "Social life": "SocialLife",
}


def map_folder_name_from_task(task):
    raw = task.get("folder", {}).get("name", "") or "N_A"
    return FOLDER_MAP.get(raw, raw)


# Lowercase internal folder key -> planned hours per month (Excel summary)
PLANNED_HOURS = {
    "comarchactualwork": 60,
    "programmingprojects": 20,
    "improvement": 15,
    "cooking": 20,
    "guitar": 15,
    "audiobook": 10,
    "book": 10,
    "joblookingcv": 15,
    "fitual": 10,
    "finance": 10,
    "gymsports": 20,
    "mastersdegree": 15,
    "lovelifetinder": 10,
    "tvshows": 10,
    "computergames": 30,
    "sociallife": 50,
    "familysociallife": 30,
    "painting": 10,
    "carpentering": 10,
}

# Lowercase internal folder key -> tags for Excel row coloring / subtotals
FOLDER_TAGS = {
    "comarchactualwork": {"productivity"},
    "programmingprojects": {"productivity"},
    "improvement": {"productivity"},
    "cooking": {"productivity"},
    "guitar": {"productivity"},
    "audiobook": {"productivity"},
    "book": {"productivity"},
    "joblookingcv": {"productivity"},
    "fitual": {"productivity"},
    "finance": {"productivity"},
    "gymsports": {"productivity"},
    "mastersdegree": {"productivity"},
    "lovelifetinder": {"enjoyment"},
    "tvshows": {"enjoyment"},
    "computergames": {"enjoyment"},
    "sociallife": {"enjoyment"},
    "familysociallife": {"enjoyment"},
    "painting": {"productivity"},
    "carpentering": {"productivity"},
}
