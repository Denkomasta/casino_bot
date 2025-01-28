import json
import discord
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

    def change_player_balance(self, author_id: int, value: int) -> None:
        self.data[str(author_id)]["balance"] = self.data[str(author_id)]["balance"] + value

    def get_player_name(self, author_id: int) -> str:
        return self.data[str(author_id)]["name"]
    
    def add_player(self, ctx) -> bool:
        a_id = str(ctx.author.id)
        if a_id not in self.data.keys():
            self.data[a_id] = {"name": ctx.author.global_name, "balance": 100}     # TODO What do we want to save?
            return True
        return False
    
    def is_player(self, author_id: int) -> bool:
        return (str(author_id) in self.data.keys())
    
    def delete_player(self, ctx) -> None:
        a_id = str(ctx.author.id)
        if a_id in self.data.keys():
            self.data.pop(a_id)
    
    # Returns a list of tuples (name, balance) of the top_n players
    def get_leaderboard(self, top_n: int = 10) -> list:
        sorted_players = sorted(self.data.items(), key=lambda item: item[1]["balance"], reverse=True)
        return sorted_players[:top_n]
