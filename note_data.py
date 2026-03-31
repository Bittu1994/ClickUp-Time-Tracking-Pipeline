"""
Store all note data for different months in the calendar.
Each month contains a list of tuples with (day, note_type) format.
"""

from styling import get_formats

notes_june = [
    (2, "home"),
    (3, "remote"),
    (5, "work"),
    (12, "travel"),
]

notes_july = [
    (1, "work"),
    (4, "home"),
    (10, "remote"),
    (20, "travel"),
]

notes_august = [
    (2, "home"),
    (3, "remote"),
    (4, "work"),
    (15, "travel"),
    (5, "work"),
    (6, "work"),
    (7, "work"),
    (8, "work"),
]

notes_september = [
    (2, "home"),
    (3, "remote"),
    (4, "work"),
    (15, "travel"),
    (5, "work"),
    (6, "work"),
    (7, "work"),
    (8, "work"),
]

notes_october = [
    (2, "home"),
    (3, "remote"),
    (4, "work"),
    (15, "travel"),
    (5, "work"),
    (6, "work"),
    (7, "work"),
    (8, "work"),
]

notes_november = [
    (1, "home", "test"),
    (2, "home"),
    (3, "remote"),
    (4, "remote"),
    (5, "remote"),
    (6, "work"),
    (7, "work", "Hel wyjazd"),
    (8, "remote", "Hel wyjazd"),
    (9, "travel", "Hel wyjazd"),
    (10, "travel", "Hel wyjazd"),
    (11, "wroclaw"),
    (12, "wroclaw"),
    (13, "wroclaw"),
    (14, "wroclaw"),
    (15, "wroclaw"),
    (16, "wroclaw"),
    (17, "wroclaw"),
    (18, "wroclaw"),
    (19, "wroclaw"),
    (20, "wroclaw"),
    (21, "wroclaw"),
    (22, "wroclaw"),
    (23, "wroclaw"),
    (24, "wroclaw"),
    (25, "wroclaw"),
    (26, "wroclaw"),
    (27, "wroclaw"),
    (28, "wroclaw"),
    (29, "wroclaw"),
    (30, "wroclaw"),


]


notes_december = [
    (1, "home", "test"),
    (2, "home"),
    (3, "remote"),
    (4, "remote"),
    (5, "remote"),
    (6, "work"),
    (7, "work", "Hel wyjazd"),
    (8, "remote", "Hel wyjazd"),
    (9, "travel", "Hel wyjazd"),
    (10, "travel", "Hel wyjazd"),
    (11, "wroclaw"),
    (12, "wroclaw"),
    (13, "wroclaw"),
    (14, "wroclaw"),
    (15, "wroclaw"),
    (16, "wroclaw"),
    (17, "wroclaw"),
    (18, "home", "wiglija"),
    (19, "home", "wiglija"),
    (20, "home", "wiglija"),
    (21, "home", "wiglija"),
    (22, "home", "wiglija"),
    (23, "home", "wiglija"),
    (24, "home", "wiglija"),
    (25, "home", "wiglija"),
    (26, "home", "wiglija"),
    (27, "home", "wiglija"),
    (28, "home", "wiglija"),
    (29, "home", "wiglija"),
    (30, "home", "wiglija"),


]

notes_january = [
    (1, "home", "test"),
    (2, "home"),
    (3, "remote"),
    (4, "remote"),
    (5, "remote"),
    (6, "work"),
    (7, "wroclaw"),
    (8, "wroclaw"),
    (9, "wroclaw"),
    (10, "wroclaw"),

    (11, "wroclaw"),
    (12, "wroclaw"),
    (13, "wroclaw"),
    (14, "wroclaw"),
    (15, "wroclaw"),
    (16, "wroclaw"),
    (17, "wroclaw"),
    (18, "wroclaw"),
    (19, "wroclaw"),
    (20, "wroclaw"),
    (21, "wroclaw"),
    (22, "wroclaw"),
    (23, "wroclaw"),
    (24, "wroclaw"),
    (25, "wroclaw"),
    (26, "wroclaw"),
    (27, "wroclaw"),
    (28, "wroclaw"),
    (29, "wroclaw"),
    (30, "wroclaw"),

]

notes_february = [
    (1, "home", "test"),
    (2, "home"),
    (3, "remote"),
    (4, "remote"),
    (5, "remote"),
    (6, "work"),
    (7, "wroclaw"),
    (8, "wroclaw"),
    (9, "wroclaw"),
    (10, "wroclaw"),

    (11, "wroclaw"),
    (12, "wroclaw"),
    (13, "wroclaw"),
    (14, "wroclaw"),
    (15, "wroclaw"),
    (16, "wroclaw"),
    (17, "wroclaw"),
    (18, "wroclaw"),
    (19, "wroclaw"),
    (20, "wroclaw"),
    (21, "wroclaw"),
    (22, "wroclaw"),
    (23, "wroclaw"),
    (24, "wroclaw"),
    (25, "wroclaw"),
    (26, "wroclaw"),
    (27, "wroclaw"),
    (28, "wroclaw"),
    (29, "wroclaw"),
    (30, "wroclaw"),

]

# Mapping for easy access by (year, month)
notes_mapping = {
    (2025, 6): notes_june,
    (2025, 7): notes_july,
    (2025, 8): notes_august,
    (2025, 9): notes_september,
    (2025, 10): notes_october,
    (2025, 11): notes_november,
    (2025, 12): notes_december,
    (2026, 1): notes_january,
    (2026, 2): notes_february,
}