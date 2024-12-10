from random import randrange

HEARTS = 0
DIAMONDS = 1
CLUBS = 2
SPADES = 3

class Player:
    name: str
    cards: set[tuple[int, int]]
    bet: int
    state: bool
    result: tuple[int, int]|None = None
    def __init__(self, name: str, bet: int=0):
        self.name = name
        self.bet = bet
        self.cards = set()
        state = True


class BlackJack:
    deck: list[tuple[int, int]]
    crupier_cards: set[tuple[int, int, bool]] = set()
    players: dict[str, Player]


    def __init__(self):
        self.deck = [((symbol, value), False) for symbol in range(4) for value in range(1, 14)]
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
    
    def game_init(self) -> str:
        return "Players who wants to participate write \"TBD bet\" after all of you are ready write \"TBD start\""
    
    def format_card(self, card: tuple[int, int]):
        suits = {0: "♥", 1: "♦", 2: "♣", 3: "♠"}
        values = {1: "A", 11: "J", 12: "Q", 13: "K"}

        s, v = card
        suit = suits.get(s, "?")
        value = values.get(v, str(v))

        return f"{value}{suit}"

    def format_cards(self)-> str:
        formated: str = "Crupier: "
        for suit, value, hidden in self.crupier_cards:
            if (hidden):
                formated += "?? "
            else:
                formated += f"{self.format_card((suit, value))} "
        formated += "\n"
        for player in self.players.values():
            formated += f"{player.name}: "
            for card in player.cards:
                formated += f"{self.format_card(card)} "
            formated += "\n"
        return formated
        

    def give_cards(self) -> str:
        sym, val = self.deck.pop(randrange(len(self.deck)))
        self.crupier_cards.add((sym, val, False))
        for _ in range(2):
            for player in self.players.values():
                player.cards.add(self.deck.pop(randrange(len(self.deck))))
        sym, val = self.deck.pop(randrange(len(self.deck)))
        self.crupier_cards.add((sym, val, True))
        return self.format_cards()
        


    




    