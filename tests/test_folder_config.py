"""Lightweight tests for shared folder config."""

import unittest

from folder_config import FOLDER_MAP, PLANNED_HOURS, FOLDER_TAGS, map_folder_name_from_task


class TestFolderConfig(unittest.TestCase):
    def test_map_folder_name_from_task(self):
        task = {"folder": {"name": "Programming / Projects"}}
        self.assertEqual(map_folder_name_from_task(task), "ProgrammingProjects")

    def test_unknown_folder_passes_through(self):
        task = {"folder": {"name": "Custom Folder"}}
        self.assertEqual(map_folder_name_from_task(task), "Custom Folder")

    def test_folder_map_has_common_keys(self):
        self.assertIn("Programming / Projects", FOLDER_MAP)

    def test_planned_hours_key(self):
        self.assertEqual(PLANNED_HOURS["programmingprojects"], 20)

    def test_folder_tags(self):
        self.assertIn("productivity", FOLDER_TAGS["programmingprojects"])
        self.assertIn("enjoyment", FOLDER_TAGS["tvshows"])


if __name__ == "__main__":
    unittest.main()
