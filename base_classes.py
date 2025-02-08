from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState, PlayerResult, E, CardSuits, BaccaratBetType
from database import Database
import discord
from ascii_obj import Ascii
from random import randrange

class Card:
    value: int
    suit: CardSuits
    showable: bool

    def __init__(self, suit: CardSuits, value: int, show: bool= True):
        self.suit = suit
        self.value = value
        self.showable = show
    
    def show_card(self) ->str:
        ascii_card = Ascii.get_card(self.suit, self.value, self.showable)
        show: str = ""
        for line in ascii_card:
            show += "`"
            show += "".join(line)
            show += "`"
            show += "\n"
        return show



class Player(ABC):
    state: PlayerState
    player_info: discord.User | discord.Member

    def __init__(self, player_info: discord.User | discord.Member):
        self.bet = Bet(0)
        self.state = PlayerState.NOT_READY
        self.player_info = player_info

class CardPlayer(Player):
    cards: list[Card]

    def __init__(self, player_info: discord.User | discord.Member):
        super().__init__(player_info)
        self.cards = []

    def show_cards(self) -> str:
        show = ""
        for index in range(5):
            #show += "`"
            for card in self.cards:
                show += "".join(Ascii.get_card(card.suit, card.value, card.showable)[index])
            #show += "`"
            show += "\n"
        return show
    

class Bet:
    value: int
    player: Player

    def __init__(self, player: Player, value: int):
        self.value = value
        self.player = player


class Game(ABC):
    type: GameType
    players: dict[int, Player]
    state: GameState
    data: Database
    channel: discord.TextChannel
    bets: dict[int, dict[int, Bet]]

    def __init__(self, data: Database, channel: discord.TextChannel, type: GameType):
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        self.type = type
        self.data = data
        self.channel = channel
        self.bets = {}

    def add_player(self,  player_info: discord.User | discord.Member) -> E:
        if (self.players.get(player_info.id) is not None):
            return E.INV_STATE
    
        match self.type:
            case GameType.BLACKJACK:
                from blackjack.black_jack import BlackJackPlayer
                self.players[player_info.id] = BlackJackPlayer(player_info)
            case GameType.BACCARAT:
                from baccarat.baccarat import BaccaratPlayer
                self.players[player_info.id] = BaccaratPlayer(player_info)
        return E.SUCCESS
    
    def remove_player(self, player_info: discord.User | discord.Member) -> E:
        if (self.players.get(player_info.id) is None):
            return E.INV_STATE
        self.return_bet(player_info)
        
        self.players.pop(player_info.id)
        return E.SUCCESS
    
    def ready_up(self, player_info: discord.User | discord.Member) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if self.players[player_info.id].state == PlayerState.READY:
            return E.INV_STATE

        self.players[player_info.id].state = PlayerState.READY
        return E.SUCCESS

    def unready(self, player_info: discord.User | discord.Member) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if self.players[player_info.id].state == PlayerState.NOT_READY:
            return E.INV_STATE

        self.players[player_info.id].state = PlayerState.NOT_READY
        return E.SUCCESS
    
    def are_players_ready(self):
        for player in self.players.values():
            if (player.state != PlayerState.READY):
                return False
        return True
        
    def give_winnings(self) -> None:
        pass

    def place_bet(self, player_info: discord.Member | discord.User, bet: Bet, type: int):
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if bet.value > self.data.get_player_balance(player_info.id):
            return E.INSUFFICIENT_FUNDS
        
        if self.bets[type].get(player_info.id) != None and self.bets[type].get(player_info.id)

        self.bets[type][player_info.id] = bet
        self.data.change_player_balance(player_info.id, -bet.value)
        return E.SUCCESS
        

    def check_valid_player(self, player_info: discord.User | discord.Member):
        return (self.players.get(player_info.id, None) is not None)
    
    def show_players_by_state(self, state: PlayerState) -> str:
        show: str = ""
        for player in self.players.values():
            if (player.state == state):
                show += f"{player.player_info.name}\n"
        return show

class CardGame(Game):
    deck: list[Card]

    def __init__(self, data: Database, channel: discord.TextChannel, type: GameType):
        super().__init__(data, channel, type)
        self.deck = self.get_new_deck()

    def get_new_deck(self) -> list[Card]:
        return [Card(suit, value, True) for suit in CardSuits if suit != CardSuits.UNSHOWABLE for value in range(1, 14)]
    
    def draw_card(self) -> Card:
        return self.deck.pop(randrange(len(self.deck)))

