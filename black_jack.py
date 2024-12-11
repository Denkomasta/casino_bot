from random import randrange

DEFEAT = 0
VICTORY = 1
DRAW = 2

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

    def show_card(self):
        if (not self.show):
            return "??"
        
        suits = {0: "♥", 1: "♦", 2: "♣", 3: "♠"}
        values = {1: "A", 11: "J", 12: "Q", 13: "K"}

        suit = suits.get(self.suit, "?")
        value = values.get(self.value, str(self.value))
        return f"{value}{suit}"

class Player:
    name: str
    cards: list[Card]
    bet: int
    state: bool
    result: tuple[int, int]
    def __init__(self, name: str, bet: int=0):
        self.name = name
        self.bet = bet
        self.cards = []
        self.state = True
        self.result = (-1, -1)
    
    def count_cards(self) -> int:
        count_a1: int = 0
        count_a11: int = 0
        for card in self.cards:
            if (card.show):
                count_a1 += card.value if card.value <= 10 else 10
                count_a11 += 10 if card.value > 10 else 11 if card.value == 1 else card.value
        if (count_a11 > 21):
            return count_a1
        return count_a11
    
    def show_cards(self) -> str:
        show = f"{self.name} |{self.count_cards()}|: "
        for card in self.cards:
            show += f"{card.show_card()} "
        return show



class BlackJack:
    deck: list[Card]
    crupier: Player = Player("DisCas", 0)
    players: dict[str, Player]


    def __init__(self):
        self.deck = [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]
        self.crupier.cards = []
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
        return "Players who wants to participate write \"!blackjack add -bet-\" after all of you are ready write \"!blackjack start\""
    

    def show_game(self)-> str:
        show: str = ""
        show += f"{self.crupier.show_cards()}\n"
        for player in self.players.values():
            show += f"{player.show_cards()}\n"
        return show

    def deal_cards(self) -> None:
        hidden_card: Card = self.deck.pop(randrange(len(self.deck)))
        hidden_card.show = False
        self.crupier.cards.append(hidden_card)
        for _ in range(2):
            for player in self.players.values():
                player.cards.append(self.deck.pop(randrange(len(self.deck))))
        self.crupier.cards.append(self.deck.pop(randrange(len(self.deck))))


    def player_hit(self, name:str) -> str:
        player: Player = self.players[name]
        if (not player.state):
            return f"{name} cannot hit anymore"
        card: Card = self.deck.pop(randrange(len(self.deck)))
        player.cards.append(card)
        if (player.count_cards() > 21):
            player.state = False
            return f"{name} has over 21 and won't be able to hit anymore"
        return "you can hit"
    
    def is_crupiers_turn(self) -> bool:
        result: bool = True
        for player in self.players.values():
            result = result and not player.state
        return result
    
    def player_stand(self, name: str) -> str:
        player: Player = self.players[name]
        if (not player.state):
            return f"{name} u already stand"
        player.state = False
        return f"{name} now stands"
    
    def crupiers_turn(self):
        for card in self.crupier.cards:
            card.show = True
        while (self.crupier.count_cards() < 17):
            self.crupier.cards.append(self.deck.pop(randrange(len(self.deck))))

    def evaluate(self) -> None:
        crupiers_count: int = self.crupier.count_cards()
        for player in self.players.values():
            player_count: int = player.count_cards()
            if (player_count > 21):
                player.result = (DEFEAT, 0)
                continue
            if (crupiers_count > 21 or player_count > crupiers_count):
                player.result = (VICTORY, player.bet * 2)
                continue
            if (crupiers_count > player_count):
                player.result = (DEFEAT, 0)
                continue
            player.result = (DRAW, player.bet)
    
    def show_results(self) -> str:
        show: str = ""
        for player in self.players.values():
            show += f"{player.name}: {player.result}\n"
        return show
    
    def game_reset(self):
        self.deck = [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]
        self.crupier.cards = []
        for player in self.players.values():
            player.state = True
            player.result = (-1, -1)
            player.cards = []

    def change_bet(self, name: str, bet: int):
        self.players[name].bet = bet

    def show_status(self) ->str:
        show: str = "Waiting to finish turns of:\n"
        for player in self.players.values():
            if (player.state):
                show += f"{player.name}\n"
        return show


        


    




    