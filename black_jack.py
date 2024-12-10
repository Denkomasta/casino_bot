from random import randrange

HEARTS = 0
DIAMONDS = 1
CLUBS = 2
SPADES = 3

class Card:
    suit: int
    value: int
    show: bool

    def __init__(self, suit: int, value: int, show: bool= True):
        self.suit = suit
        self.value = value
        self.show = show

class Player:
    name: str
    cards: list[Card]
    bet: int
    state: bool
    result: tuple[int, int]|None = None
    def __init__(self, name: str, bet: int=0):
        self.name = name
        self.bet = bet
        self.cards = []
        state = True


class BlackJack:
    deck: list[Card]
    crupier_cards: list[Card] = []
    players: dict[str, Player]


    def __init__(self):
        self.deck = [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]
        self.crupier_cards = []
        self.players = {}
    
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
    
    def format_card(self, card: Card):
        if (not card.show):
            return "??"
        
        suits = {0: "♥", 1: "♦", 2: "♣", 3: "♠"}
        values = {1: "A", 11: "J", 12: "Q", 13: "K"}

        suit = suits.get(card.suit, "?")
        value = values.get(card.value, str(card.value))

        return f"{value}{suit}"

    def format_cards(self)-> str:
        formated: str = "Crupier: "
        for card in self.crupier_cards:
            formated += f"{self.format_card(card)} "
        formated += "\n"
        for player in self.players.values():
            formated += f"{player.name}: "
            for card in player.cards:
                formated += f"{self.format_card(card)} "
            formated += "\n"
        return formated
        

    def give_cards(self) -> None:
        hidden_card: Card = self.deck.pop(randrange(len(self.deck)))
        hidden_card.show = False
        self.crupier_cards.append(hidden_card)
        for _ in range(2):
            for player in self.players.values():
                player.cards.append(self.deck.pop(randrange(len(self.deck))))
        self.crupier_cards.append(self.deck.pop(randrange(len(self.deck))))
        


    




    