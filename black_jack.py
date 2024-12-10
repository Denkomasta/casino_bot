HEARTS = 0
DIAMONDS = 1
CLUBS = 2
SPADES = 3

class BlackJack:
    deck: dict[tuple[int, int], bool]
    crupier_cards: set[tuple[int, int, bool]] = set()
    players_cards: dict[str, set[tuple[int, int]]] = {}


    def __init__(self):
        self.deck = dict([((symbol, value), False) for symbol in range(4) for value in range(13)])
        self.crupier_cards = set()
        self.players_cards = {}
    
    def add_player(self, player_name: str) -> str:
        if (self.players_cards.get(player_name) is None):
            return "Player " + player_name + " is already in the game!"
        
        self.players_cards[player_name] = set()
        return "Player " + player_name + " added to the game!"



    