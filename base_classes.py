from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState, PlayerResult, E, CardSuits, BaccaratBetType
from database import Database
import discord
from ascii_obj import Ascii
from random import randrange
import global_vars

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

class Bet:
    value: int
    result: int
    winning: int

    def __init__(self, value: int):
        self.value = value
        self.result = PlayerResult.UNDEFINED
        self.winning = 0

class Player(ABC):
    bet: Bet
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
    


class Game(ABC):
    type: GameType
    players: dict[int, Player]
    state: GameState
    channel: discord.TextChannel

    def __init__(self, channel: discord.TextChannel, type: GameType):
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        self.type = type
        self.channel = channel

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
            case GameType.POKER:
                from poker.poker import Poker
                assert(isinstance(self, Poker))
                if not self.first_round and not self.joinable:
                    return E.BLOCKED
                from poker.poker import PokerPlayer
                self.players[player_info.id] = PokerPlayer(player_info)
                if self.preset_bank is not None:
                    self.players[player_info.id].bet.value = self.preset_bank
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
        
    def collect_bet(self, player_info: discord.User | discord.Member, old: int, new: int) -> None:
        global_vars.Data.change_player_balance(player_info.id, old - new)

    def return_bet(self, player_info: discord.User | discord.Member) -> None:
        global_vars.Data.change_player_balance(player_info.id, self.players[player_info.id].bet.value)

    def change_bet(self, player_info: discord.User | discord.Member, bet: int) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if (bet - self.players[player_info.id].bet.value > global_vars.Data.get_player_balance(player_info.id)):
            return E.INSUFFICIENT_FUNDS
        
        self.collect_bet(player_info, self.players[player_info.id].bet.value,  bet)
        self.players[player_info.id].bet.value = bet
        return E.SUCCESS
    
    def collect_bets(self) -> None:
        for player in self.players.values():
            if (player.bet.value > 0):
                global_vars.Data.change_player_balance(player.player_info.id, -player.bet.value)
    
    def give_winnings(self) -> None:
        for player in self.players.values():
            if (player.bet.winning > 0):
                global_vars.Data.change_player_balance(player.player_info.id, player.bet.winning)
        

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

    def __init__(self, channel: discord.TextChannel, type: GameType):
        super().__init__(channel, type)
        self.deck = self.get_new_deck()

    def get_new_deck(self) -> list[Card]:
        return [Card(suit, value, True) for suit in CardSuits if suit != CardSuits.UNSHOWABLE for value in range(1, 14)]
    
    def draw_card(self) -> Card:
        return self.deck.pop(randrange(len(self.deck)))

