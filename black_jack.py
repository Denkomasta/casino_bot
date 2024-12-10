import random

HEARTS = 0
DIAMONDS = 1
CLUBS = 2
SPADES = 3

class Player:
    name: str
    cards: set[tuple[int, int]]
    bet: int = 0
    def __init__(self, name: str, bet: int=0):
        self.name = name
        self.bet = bet
        self.cards = set()


class BlackJack:
    deck: dict[tuple[int, int], bool]
    crupier_cards: set[tuple[int, int, bool]] = set()
    players: dict[str, Player]


    def __init__(self):
        self.deck = dict([((symbol, value), False) for symbol in range(4) for value in range(13)])
        self.crupier_cards = set()
        self.players_cards = {}
        self.players_bets = {}
    
    def add_player(self, player_name: str, bet: int=0) -> str:
        if (self.players.get(player_name) is not None):
            return "Player " + player_name + " is already in the game!"
        
        self.players[player_name] = Player(player_name, bet)
        return "Player " + player_name + " added to the game!"

    def remove_player(self, player_name: str) -> str:
        if (self.players.get(player_name) is None):
            return "Player " + player_name + " is not in the game!"
        
        self.players.pop(player_name)
        return "Player " + player_name + " was removed from the game!"
    




    