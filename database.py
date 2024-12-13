import json
from typing import Any

class Database:
    data: dict[str, Any]

    def __init__(self):
        self.data = self.load_stats()

    def load_stats(self):   # returns dict
        try:
            with open("player_stats.json", "r") as f:
                return json.load(f)
        except Exception as _:
            return {}

    def save_stats(self):
        try:
            with open("player_stats.json", "w") as f:
                json.dump(self.data, f, indent=4)
            print("Player stats saved successfully.")
        except Exception as e:
            print(f"Error saving stats: {e}")    # TODO add log?

    def get_player_balance(self, author_id: int) -> int:
        return self.data[str(author_id)]["balance"]

    def change_player_balance(self, author_id: int, value: int) -> None:     # TODO get and add are functioning weirdly when someone changes value
        self.data[str(author_id)]["balance"] = self.data[str(author_id)]["balance"] + value

    def get_player_name(self, author_id: int) -> str:
        return self.data[str(author_id)]["name"]
