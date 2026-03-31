import requests
import os

CLICKUP_TOKEN = os.getenv("CLICKUP_API_KEY")
if not CLICKUP_TOKEN:
    raise ValueError("Missing required env var: CLICKUP_API_KEY")
TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
if not TEAM_ID:
    raise ValueError("Missing required env var: CLICKUP_TEAM_ID")
HEADERS = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}

def get_spaces(team_id):
    url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("spaces", [])

def get_lists_in_space(space_id):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/list"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("lists", [])

def get_tasks_from_list(list_id):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("tasks", [])

def main():
    spaces = get_spaces(TEAM_ID)
    if not spaces:
        print("No spaces found")
        return

    lists = []
    # Loop over spaces until we find a space with lists
    for space in spaces:
        lists = get_lists_in_space(space["id"])
        if lists:
            print(f"Found lists in space: {space['name']} ({space['id']})")
            break
    else:
        print("No lists found in any space")
        return

    first_list = lists[0]
    tasks = get_tasks_from_list(first_list["id"])
    if not tasks:
        print("No tasks found in first list")
        return

    # Print out date_created, start_date, due_date and their types for the first task
    task = tasks[0]
    for field in ["date_created", "start_date", "due_date"]:
        value = task.get(field)
        print(f"{field}: {value} (type: {type(value)})")

if __name__ == "__main__":
    main()
