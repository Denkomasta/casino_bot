from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState
from database import Database

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
    showable: bool
    ascii: list[list[str]]
    

    def __init__(self, suit: int, value: int, show: bool= True):
        self.suit = suit
        self.value = value
        self.showable = show
        self.ascii = [
            ["┌","─","─","─","─","─","┐"],
            ["│","V"," "," "," "," ","│"],
            ["│"," "," ","S"," "," ","│"],
            ["│"," "," "," "," ","V","│"],
            ["└","─","─","─","─","─","┘"]
        ]
    
    def fill_ascii(self) -> None:
        suit = self.suit
        value = self.value

        if (not self.showable):
            suit = -1
            value = -1

        suits = {0: "♥", 1: "♦", 2: "♣", 3: "♠", -1: "?"}
        values = {1: "A", 10: "1", 11: "J", 12: "Q", 13: "K", -1: "?"}

        if (value == 10):
            self.ascii[1][1] = "1"
            self.ascii[1][2] = "0"
            self.ascii[3][4] = "1"
            self.ascii[3][5] = "0"
            self.ascii[2][3] = suits.get(suit, "?")
            return

        self.ascii[1][1] = values.get(value, str(value))
        self.ascii[2][3] = suits.get(suit, "?")
        self.ascii[3][5] = values.get(value, str(value))
        

    def show_card(self) ->str:
        self.fill_ascii()
        show: str = ""
        for lst in self.ascii:
            show += "`"
            show += "".join(lst)
            show += "`"
            show += "\n"
        return show

class Player:
    name: str
    id: int
    cards: list[Card]
    bet: int
    state: PlayerState
    result: tuple[int, int]
    def __init__(self, id: int, name: str, bet: int=0):
        self.name = name
        self.id = id
        self.bet = bet
        self.cards = []
        self.result = (-1, -1)
        self.state = PlayerState.NOT_READY
    
    def count_cards(self) -> int:
        count_a1: int = 0
        count_a11: int = 0
        for card in self.cards:
            if (card.showable):
                count_a1 += card.value if card.value <= 10 else 10
                count_a11 += 10 if card.value > 10 else 11 if card.value == 1 else card.value
        if (count_a11 > 21):
            return count_a1
        return count_a11
    
    def show_cards(self) -> str:
        show = f"{self.name} |{self.count_cards()}|:\n"
        for card in self.cards:
            card.fill_ascii()
        for index in range(5):
            show += "`"
            for card in self.cards:
                show += "".join(card.ascii[index])
            show += "`"
            show += "\n"
        return show



class BlackJack:
    deck: list[Card]
    crupier: Player
    players: dict[str, Player]
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] #dict of str/functions
    is_playing: bool
    state: GameState
    data: Database

    def __init__(self, data: Database):
        self.deck = [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]
        self.crupier = Player(0, "Dealer", 0)
        self.players = {}
        self.is_playing = False
        self.data = data
        self.state = GameState.WAITING_FOR_PLAYERS
        self.commands_dict = {
            "restart": self.cmd_restart,
            "join": self.cmd_join,
            "leave": self.cmd_leave,
            "start": self.cmd_start,
            "ready": self.cmd_ready,
            "unready": self.cmd_unready,
            "hit": self.cmd_hit,
            "stand": self.cmd_stand,
            "bet": self.cmd_bet,
            "status": self.cmd_status,
            "help": self.cmd_help
        } 

    async def cmd_run(self, ctx: commands.Context, args: list[str]) -> None:
        if (len(args) == 0):
            await ctx.send("There is no argument, use \"!blackjack help\" to see the options")
        if (args[0] not in self.commands_dict):
            await ctx.send("Invalid argument, use \"!blackjack help\" to see the options")
        await self.commands_dict[args[0]](ctx, args)

    async def cmd_restart(self, ctx: commands.Context, args: list[str]):
        """Handles the 'restart' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (self.state == GameState.RUNNING):
            await ctx.send(f"Game is running right now, wait until is ends or use 'exit'")
            return
        self.game_restart()
        await ctx.send("Game was succesfully reseted, you can change your bet using \"!blackjack bet -bet-\" or leave the game using \"!blackjack leave\"")

    async def cmd_join(self, ctx: commands.Context, args: list[str]):
        """Handles the 'join' command."""
        if (len(args) > 2):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be < 2")
            return
        if (self.state == GameState.RUNNING):
            await ctx.send(f"Game is running, wait for till the end")
            return
        bet = 0
        if (len(args) == 2):
            try:
                bet = int(args[1])
            except Exception as _:
                await ctx.send(f"Argument [bet] has to be number, try again")
                return
        if (self.add_player(ctx.author.id, ctx.author.name, bet) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is already in the game!")
             return
        await ctx.send(f"Player {ctx.author.name} joined the game! {('Your bet is set to 0, use !bj bet [number] to change it.' if bet == 0 else f' Bet set to {bet}.')}")

    async def cmd_leave(self, ctx: commands.Context, args: list[str]):
        """Handles the 'leave' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (self.remove_player(ctx.author.name) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is not in the game!")
             return
        await ctx.send(f"Player {ctx.author.name} was removed from the game!")

    async def cmd_start(self, ctx: commands.Context, args: list[str]):
        """Handles the 'start' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (not self.are_players_ready()):
            await ctx.send(f"Waiting for players:\n{self.show_players_by_state(PlayerState.NOT_READY)}")
            return
        self.game_start()
        await ctx.send(f"{self.show_game()}")
        if (self.is_crupiers_turn()):
            self.crupiers_turn()
            self.give_winnings()
            self.state = GameState.ENDED
            await ctx.send(f"{self.show_game()}\n{self.show_results()}")

    async def cmd_ready(self, ctx: commands.Context, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (self.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        self.players[ctx.author.name].state = PlayerState.READY
        await ctx.send(f"{ctx.author.name} is READY")
    
    async def cmd_unready(self, ctx: commands.Context, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (self.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        self.players[ctx.author.name].state = PlayerState.NOT_READY
        await ctx.send(f"{ctx.author.name} is UNREADY")

    async def cmd_hit(self, ctx: commands.Context, args: list[str]):
        """Handles the 'hit' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        can_play: E = self.player_hit(ctx.author.name)
        await ctx.send(f"{self.players[ctx.author.name].show_cards()}")
        if (self.is_crupiers_turn()):
            self.crupiers_turn()
            self.give_winnings()
            self.state = GameState.ENDED
            await ctx.send(f"{self.show_game()}\n{self.show_results()}")
            return
        if (can_play == E.INV_STATE):
            await ctx.send(f"{ctx.author.name} cannot hit anymore")
        
        
    async def cmd_stand(self, ctx: commands.Context, args: list[str]):
        """Handles the 'stand' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (self.player_stand(ctx.author.name) == E.INV_STATE):
            await ctx.send(f"{ctx.author.name} already stands")
            return
        if (self.is_crupiers_turn()):
            self.crupiers_turn()
            self.give_winnings()
            self.state = GameState.ENDED
            await ctx.send(f"{self.show_game()}\n{self.show_results()}")
            return
        await ctx.send(f"{ctx.author.name} now stands")
        

    async def cmd_bet(self, ctx: commands.Context, args: list[str]):
        """Handles the 'bet' command."""
        if (len(args) != 2):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 2")
            return
        try:
            bet = int(args[1])
        except Exception as _:
            await ctx.send(f"Argument [bet] has to be number, try again")
            return
        self.change_bet(ctx.author.name, bet)
        await ctx.send(f"{ctx.author.name}'s bet changed to {bet}")

    async def cmd_status(self, ctx: commands.Context, args: list[str]):
        """Handles the 'status' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        match (self.state):
            case GameState.WAITING_FOR_PLAYERS:
                await ctx.send(f"GAME IS WAITING TO START:\n\nPlayer that are not ready:\n{self.show_players_by_state(PlayerState.NOT_READY)}")
                return
            case GameState.RUNNING:
                await ctx.send(f"GAME IS RUNNING:\n\nTable:\n{self.show_game()}\n\nStill active players:\n{self.show_players_by_state(PlayerState.PLAYING)}")
                return
            case GameState.ENDED:
                await ctx.send(f"GAME ENDED:\n\nResults:\n{self.show_results()}")
                return
        await ctx.send("Command 'status' invoked.")

    async def cmd_help(self, ctx: commands.Context, args: list[str]):
        """Handles the 'help' command."""
        help: list[str] = [
            "create - creates a new game",
            "exit - destroys current game",
            "join [number] - adds you to current game, with instead of number use size of your bet",
            "ready - sets you READY",
            "unready - sets you UNREADY",
            "start - starts the game if all players are READY",
            "hit - get a card",
            "stand - end your turn",
            "bet [number] - changes your bet",
            "restart - restarts the game, but players and bets will stay",
        ]
        await ctx.send("\n".join(help))

    
    def add_player(self, player_id: int, player_name: str, bet: int=0) -> E:
        if (self.players.get(player_name) is not None):
            return E.INV_STATE
        
        self.players[player_name] = Player(player_id, player_name, bet)
        return E.SUCCESS

    def remove_player(self, player_name: str) -> E:
        if (self.players.get(player_name) is None):
            return E.INV_STATE
        
        self.players.pop(player_name)
        return E.SUCCESS

    def show_game(self)-> str:
        show: str = ""
        show += f"{self.crupier.show_cards()}\n"
        for player in self.players.values():
            show += f"{player.show_cards()}\n"
        return show

    def deal_cards(self) -> None:
        hidden_card: Card = self.deck.pop(randrange(len(self.deck)))
        hidden_card.showable = False
        self.crupier.cards.append(hidden_card)
        for _ in range(2):
            for player in self.players.values():
                player.cards.append(self.deck.pop(randrange(len(self.deck))))
        self.crupier.cards.append(self.deck.pop(randrange(len(self.deck))))


    def player_hit(self, name:str) -> E:
        player: Player = self.players[name]
        if (player.state != PlayerState.PLAYING):
            return E.INV_STATE
        card: Card = self.deck.pop(randrange(len(self.deck)))
        player.cards.append(card)
        if (player.count_cards() == 21):
            player.state = PlayerState.FINISHED
        if (player.count_cards() > 21):
            player.state = PlayerState.FINISHED
        return E.SUCCESS
    
    def is_crupiers_turn(self) -> bool:
        result: bool = True
        for player in self.players.values():
            result = result and player.state == PlayerState.FINISHED
        return result
    
    def player_stand(self, name: str) -> E:
        player: Player = self.players[name]
        if (player.state != PlayerState.PLAYING):
            return E.INV_STATE
        player.state = PlayerState.FINISHED
        return E.SUCCESS
    
    def crupiers_turn(self):
        for card in self.crupier.cards:
            card.showable = True
        while (self.crupier.count_cards() < 17):
            self.crupier.cards.append(self.deck.pop(randrange(len(self.deck))))
        self.evaluate()

    def evaluate(self) -> None:
        crupiers_count: int = self.crupier.count_cards()
        for player in self.players.values():
            player_count: int = player.count_cards()
            if (player_count > 21):
                player.result = (DEFEAT, 0)
                continue
            if (player_count == 21):
                player.result = (VICTORY, player.bet * 2)
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
            result, income = player.result
            match result:
                case 1:
                    show += f"{player.name}: You won! Your bet was {player.bet}, you won {income}.\n"
                case 0:
                    show += f"{player.name}: You lost. Your lost your bet of {player.bet}.\n"
                case 2:
                    show += f"{player.name}: Draw. Your bet of {player.bet} has been returned.\n"
        return show
    
    def game_restart(self):
        self.deck = [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]
        self.crupier.cards = []
        self.state = GameState.WAITING_FOR_PLAYERS
        for player in self.players.values():
            player.state = PlayerState.NOT_READY
            player.result = (-1, -1)
            player.cards = []

    def change_bet(self, name: str, bet: int) -> None:
        self.players[name].bet = bet

    def collect_bets(self) -> None:
        for player in self.players.values():
            if (player.bet > 0):
                self.data.change_player_balance(player.id, -player.bet)
    
    def give_winnings(self) -> None:
        for player in self.players.values():
            _, add = player.result
            if (add > 0):
                self.data.change_player_balance(player.id, add)

    def show_players_by_state(self, state: PlayerState) -> str:
        show: str = ""
        for player in self.players.values():
            if (player.state == state):
                show += f"{player.name}\n"
        return show
    
    def are_players_ready(self):
        for player in self.players.values():
            if (player.state != PlayerState.READY):
                return False
        return True

    def game_start(self):
        self.collect_bets()
        self.deal_cards()
        self.state = GameState.RUNNING
        for player in self.players.values():
            player.state = PlayerState.PLAYING
    




    