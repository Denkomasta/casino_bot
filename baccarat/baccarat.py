from base_classes import CardGame, Bet, Card, Player, CardPlayer
from enums import BaccaratBetType, CardSuits, GameType, GameState, PlayerResult, PlayerState, E
from random import randrange
import discord


class BaccaratBet(Bet):
    type: int

    def __init__(self, value: int, type: int):
        super().__init__(value)
        self.type = type

class BaccaratPlayer(Player):

    def __init__(self, player_info: discord.Member | discord.User):
        super().__init__(player_info)
        self.bet = BaccaratBet(0, BaccaratBetType.UNDEFINED)

class BaccaratFigure(CardPlayer):
    count: int

    def __init__(self):
        self.cards = []
        self.count = 0

    def draw_card(self, game: CardGame):
        self.cards.append(game.draw_card())
        self.update_count()

    def update_count(self):
        count = 0
        for card in self.cards:
            count += card.value if card.value < 10 else 0
        self.count = count % 10

class Baccarat(CardGame):

    banker: BaccaratFigure
    player: BaccaratFigure

    def __init__(self,channel: discord.TextChannel):
        super().__init__(channel, GameType.BACCARAT)
        self.banker = BaccaratFigure()
        self.player = BaccaratFigure()
    
    def game_start(self):
        self.state = GameState.RUNNING
        for _ in range(2):
            self.player.draw_card(self)
            self.banker.draw_card(self)
        if (8 <= self.player.count <= 9 or 8 <= self.banker.count <= 9):
            return
        
        if (6 <= self.player.count <= 7 and self.banker.count <= 5):
            self.banker.draw_card(self)
            return
        self.player.draw_card(self)

        if (self.banker.count <= 6):
            if (self.banker.count <= 2 or self.player.cards[2].value != 8):
                self.banker.draw_card(self)
        return
    
    def evaluate_bets(self) -> None:
        result: int
        if self.banker.count > self.player.count:
            result = BaccaratBetType.BANKER
        elif self.player.count > self.banker.count:
            result = BaccaratBetType.PLAYER
        else:
            result = BaccaratBetType.TIE
        
        for player in self.players.values():
            if player.bet.type != result:
                player.bet.result = PlayerResult.DEFEAT
                player.bet.winning = 0
                continue
            player.bet.result = PlayerResult.VICTORY
            match result:
                case BaccaratBetType.PLAYER:
                    player.bet.winning = player.bet.value * 2
                case BaccaratBetType.BANKER:
                    player.bet.winning = round(player.bet.value * 2 * 0.95)
                case BaccaratBetType.TIE:
                    player.bet.winning = player.bet.value * 9

    def show_game(self) -> str:
        show = f"Banker: |{self.banker.count}|\n"
        show += self.banker.show_cards()
        show += "\n"
        show += f"Player: |{self.player.count}|\n"
        show += self.player.show_cards()
        show += "\n"
        return show
    
    def show_results(self) -> str:
        show: str = ""
        for player in self.players.values():
            result = player.bet.result
            income = player.bet.winning
            match result:
                case PlayerResult.VICTORY:
                    show += f"{player.player_info.name}: You won! Your bet was {player.bet.value}, you won {income}.\n"
                case PlayerResult.DEFEAT:
                    show += f"{player.player_info.name}: You lost. Your lost your bet of {player.bet.value}.\n"
                case PlayerResult.DRAW:
                    show += f"{player.player_info.name}: Draw. Your bet of {player.bet.value} has been returned.\n"
        return show

    def change_bet(self, player_info: discord.User | discord.Member, bet: int, type: int) -> E:
        if super().change_bet(player_info, bet) == E.INSUFFICIENT_FUNDS:
            return E.INSUFFICIENT_FUNDS
        self.players[player_info.id].bet.type = type
        return E.SUCCESS

    def round_restart(self):
        self.deck = self.get_new_deck()
        self.banker.cards = []
        self.banker.count = 0
        self.player.cards = []
        self.player.count = 0
        self.state = GameState.WAITING_FOR_PLAYERS
        for player in self.players.values():
            player.state = PlayerState.NOT_READY
            player.bet.result = PlayerResult.UNDEFINED
            player.bet.winning = 0
        self.collect_bets()


    def show_betlist(self) -> None:
        if len(self.players) == 0:
            return "No bets are placed currently"
        
        show = "Current bets are as follows:\n"
        show += "-------------------------\n"
        for player in self.players.values():
            show += f"{player.player_info.name}: {player.bet.value} on {BaccaratBetType(player.bet.type).name}\n"
        return show
