"""
This file contains code for the game "Legendary Creature Hunter at Mithoter Planet".
Author: DtjiSoftwareDeveloper
"""

# Game version: 1


# Importing necessary libraries

import sys
import uuid
import pickle
import copy
import random
from datetime import datetime
import os
from mpmath import *

mp.pretty = True


# Creating static functions to be used throughout the game


def is_number(string: str) -> bool:
    try:
        mpf(string)
        return True
    except ValueError:
        return False


def triangular(n: int) -> int:
    return int(n * (n - 1) / 2)


def mpf_sum_of_list(a_list: list) -> mpf:
    return mpf(str(sum(mpf(str(elem)) for elem in a_list if is_number(str(elem)))))


def load_game_data(file_name):
    # type: (str) -> Game
    return pickle.load(open(file_name, "rb"))


def save_game_data(game_data, file_name):
    # type: (Game, str) -> None
    pickle.dump(game_data, open(file_name, "wb"))


def clear():
    # type: () -> None
    if sys.platform.startswith('win'):
        os.system('cls')  # For Windows System
    else:
        os.system('clear')  # For Linux System


# Creating necessary classes


class Action:
    """
    This class contains attributes of an action which can be carried out during battles.
    """

    POSSIBLE_NAMES: list = ["NORMAL ATTACK", "NORMAL HEAL", "USE SKILL"]

    def __init__(self, name):
        # type: (str) -> None
        self.name: str = name if name in self.POSSIBLE_NAMES else self.POSSIBLE_NAMES[0]

    def __str__(self):
        # type: () -> str
        return str(self.name) + "\n"

    def execute(self, user, target, skill_to_use=None):
        # type: (LegendaryCreature, LegendaryCreature, Skill or None) -> bool
        if self.name == "NORMAL ATTACK":
            if user == target:
                return False

            raw_damage: mpf = user.attack_power * (1 + user.attack_power_percentage_up / 100 -
                                                   user.attack_power_percentage_down / 100) - target.defense * \
                              (1 + target.defense_percentage_up / 100 - target.defense_percentage_down / 100)
            damage: mpf = raw_damage if raw_damage > 0 else 0
            target.curr_hp -= damage
            return True

        elif self.name == "NORMAL HEAL":
            if user != target:
                return False

            heal_amount: mpf = 0.05 * user.max_hp
            user.curr_hp += heal_amount
            return True

        elif self.name == "USE SKILL":
            if isinstance(skill_to_use, Skill):
                # Checking whether the skill to be used is an attacking skill or a healing skill
                if isinstance(skill_to_use, AttackSkill):
                    if user == target:
                        return False

                    # Calculate the amount of damage
                    raw_damage: mpf = skill_to_use.damage_multiplier. \
                        calculate_raw_damage_without_enemy_defense(user, target) if \
                        skill_to_use.does_ignore_enemies_defense else \
                        skill_to_use.damage_multiplier.calculate_raw_damage(user, target)
                    damage: mpf = raw_damage if raw_damage > 0 else 0
                    target.curr_hp -= damage

                elif isinstance(skill_to_use, HealSkill):
                    if user != target:
                        return False

                    user.curr_hp += skill_to_use.heal_amount

                elif isinstance(skill_to_use, StrengthenSkill):
                    if user != target:
                        return False

                    user.attack_power_percentage_up += skill_to_use.self_attack_percentage_up
                    user.defense_percentage_up += skill_to_use.self_defense_percentage_up

                elif isinstance(skill_to_use, WeakeningSkill):
                    if user == target:
                        return False

                    # Checking whether the effect is resisted or not
                    resisted_chance: float = 0.15 if user.accuracy > target.resistance or \
                        target.resistance - user.accuracy <= 0.15 else target.resistance - user.accuracy
                    if random.random() >= resisted_chance:
                        target.attack_power_percentage_down += skill_to_use.enemy_attack_percentage_down
                        target.defense_percentage_down += skill_to_use.enemy_defense_percentage_down

                return True
            return False

        else:
            return False

    def clone(self):
        # type: () -> Action
        return copy.deepcopy(self)


class Battle:
    """
    This class contains attributes of a battle in this game.
    """

    def __init__(self, team1):
        # type: (Team) -> None
        self.team1: Team = team1
        self.team2: Team = Team([])
        self.reward: Reward = Reward(mpf("10") ** sum(legendary_creature.level for legendary_creature
                                                      in self.team2.get_legendary_creatures()),
                                     mpf("10") ** sum(legendary_creature.level for legendary_creature
                                                      in self.team2.get_legendary_creatures()),
                                     mpf("10") ** sum(legendary_creature.level for legendary_creature
                                                      in self.team2.get_legendary_creatures()))
        self.winner: Team or None = None
        self.whose_turn: LegendaryCreature or None = None

    def __str__(self):
        # type: () -> str
        res: str = "Below is a list of legendary creatures in team 1.\n"
        for legendary_creature in self.team1.get_legendary_creatures():
            res += str(legendary_creature) + "\n"

        res += "Below is a list of legendary creatures in team 2.\n"
        for legendary_creature in self.team2.get_legendary_creatures():
            res += str(legendary_creature) + "\n"

        res += "Rewards for winning the battle:\n" + str(self.reward) + "\n"
        res += "Winner of the battle: " + str(self.winner) + "\n"
        res += "Moving legendary creature: " + str(self.whose_turn) + "\n"
        return res

    def get_someone_to_move(self):
        # type: () -> None
        """
        Getting a legendary creature to move and have its turn.
        :return: None
        """

        # Finding out which legendary creature moves
        full_attack_gauge_list: list = []  # initial value
        while len(full_attack_gauge_list) == 0:
            for legendary_creature in self.team1.get_legendary_creatures():
                if legendary_creature.attack_gauge >= legendary_creature.FULL_ATTACK_GAUGE and legendary_creature not \
                        in full_attack_gauge_list:
                    full_attack_gauge_list.append(legendary_creature)

            for legendary_creature in self.team2.get_legendary_creatures():
                if legendary_creature.attack_gauge >= legendary_creature.FULL_ATTACK_GAUGE and legendary_creature not \
                        in full_attack_gauge_list:
                    full_attack_gauge_list.append(legendary_creature)

            self.tick()

        max_attack_gauge: mpf = max(legendary_creature.attack_gauge for legendary_creature in full_attack_gauge_list)
        for legendary_creature in full_attack_gauge_list:
            if legendary_creature.attack_gauge == max_attack_gauge:
                self.whose_turn = legendary_creature

    def tick(self):
        # type: () -> None
        """
        The clock ticks when battles are carried out.
        :return: None
        """

        for legendary_creature in self.team1.get_legendary_creatures():
            legendary_creature.attack_gauge += legendary_creature.attack_speed * 0.07

        for legendary_creature in self.team2.get_legendary_creatures():
            legendary_creature.attack_gauge += legendary_creature.attack_speed * 0.07

    def clone(self):
        # type: () -> Battle
        return copy.deepcopy(self)


class TrainerBattle(Battle):
    """
    This class contains attributes of battles between trainers in this game.
    """

    def __init__(self, team1, team2):
        # type: (Team, Team) -> None
        Battle.__init__(self, team1)
        self.team2: Team = team2


class WildBattle(Battle):
    """
    This class contains attributes of a wild battle in this game.
    """

    def __init__(self, team1, wild_legendary_creature):
        # type: (Team, LegendaryCreature) -> None
        Battle.__init__(self, team1)
        self.team2: Team = Team([wild_legendary_creature])
        self.wild_legendary_creature_caught: bool = False  # initial value

    def __str__(self):
        # type: () -> str
        res: str = Battle.__str__(self)
        res += "Has the wild legendary creature been caught? " + str(self.wild_legendary_creature_caught) + "\n"
        return res


class Location:
    """
    This class contains attributes of a location in this game.
    """

    def __init__(self, city, x, y):
        # type: (City, int, int) -> None
        self.city: City = city
        self.x: int = x
        self.y: int = y

    def __str__(self):
        # type: () -> str
        return str(self.city.name) + ", (" + str(self.x) + ", " + str(self.y) + ")"

    def get_tile(self):
        # type: () -> Tile or None
        if self.x < 0 or self.x >= self.city.CITY_WIDTH or self.y < 0 or self.y >= self.city.CITY_HEIGHT:
            return None

        return self.city.get_tiles()[self.y][self.x]

    def clone(self):
        # type: () -> Location
        return copy.deepcopy(self)


class City:
    """
    This class contains attributes of a city in Mithoter Planet.
    """

    def __init__(self, name, city_height, city_width, tiles):
        # type: (str, int, int, list) -> None
        self.name: str = name
        self.CITY_HEIGHT: int = city_height
        self.CITY_WIDTH: int = city_width
        self.__tiles: list = tiles
        assert len(self.__tiles) == self.CITY_HEIGHT and len(self.__tiles[0]) == self.CITY_WIDTH, "Dimension mismatch!"

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        for row in range(self.CITY_HEIGHT):
            curr: str = "|"  # initial value
            for col in range(self.CITY_WIDTH):
                curr += str(self.__tiles[row][col]) + "|"

            res += str(curr) + "\n"

        return res

    def get_tiles(self):
        # type: () -> list
        return self.__tiles

    def clone(self):
        # type: () -> City
        return copy.deepcopy(self)


class Portal:
    """
    This class contains attributes of a portal from one city to another.
    """

    def __init__(self, location_from, location_to):
        # type: (Location, Location) -> None
        self.location_from: Location = location_from
        self.location_to: Location = location_to

    def __str__(self):
        # type: () -> str
        return str(self.location_from) + " -> " + str(self.location_to)

    def get_tile_from(self):
        # type: () -> Tile or None
        return self.location_from.get_tile()

    def get_tile_to(self):
        # type: () -> Tile or None
        return self.location_to.get_tile()

    def clone(self):
        # type: () -> Portal
        return copy.deepcopy(self)


class Tile:
    """
    This class contains attributes of a tile in this game.
    """

    def __init__(self, portal=None):
        # type: (Portal or None) -> None
        self.name: str = ""
        self.__game_characters: list = []
        self.portal: Portal or None = portal

    def get_game_characters(self):
        # type: () -> list
        return self.__game_characters

    def add_game_character(self, game_character):
        # type: (GameCharacter) -> None
        self.__game_characters.append(game_character)

    def remove_game_character(self, game_character):
        # type: (GameCharacter) -> bool
        if game_character not in self.__game_characters:
            return False
        self.__game_characters.remove(game_character)
        return True

    def __str__(self):
        # type: () -> str
        if len(self.__game_characters) == 0:
            return str(self.name)
        else:
            res: str = ""  # initial value
            for i in range(len(self.__game_characters)):
                if i == len(self.__game_characters) - 1:
                    res += str(self.__game_characters[i].name)
                else:
                    res += str(self.__game_characters[i].name) + ", "

            return res

    def clone(self):
        # type: () -> Tile
        return copy.deepcopy(self)


class LandTile(Tile):
    """
    This class contains attributes of a tile representing land.
    """

    def __init__(self, portal=None):
        # type: (Portal or None) -> None
        Tile.__init__(self, portal)


class TrainingCenterTile(LandTile):
    """
    This class contains attributes of a training center tile where a training center used for levelling up legendary
    creatures exists.
    """

    MIN_LEGENDARY_CREATURES: int = 0
    MAX_LEGENDARY_CREATURES: int = 20

    def __init__(self, legendary_creature_exp_per_second, portal=None):
        # type: (mpf, Portal or None) -> None
        Tile.__init__(self, portal)
        self.name = "TRAINING CENTER"
        self.__legendary_creatures_trained: list = []  # initial value
        self.legendary_creature_exp_per_second: mpf = legendary_creature_exp_per_second

    def get_legendary_creatures_trained(self):
        # type: () -> list
        return self.__legendary_creatures_trained

    def add_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if len(self.__legendary_creatures_trained) < self.MAX_LEGENDARY_CREATURES:
            self.__legendary_creatures_trained.append(legendary_creature)
            return True
        return False

    def remove_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if legendary_creature in self.__legendary_creatures_trained:
            self.__legendary_creatures_trained.remove(legendary_creature)
            return True
        return False


class SandTile(LandTile):
    """
    This class contains attributes of a tile representing sand.
    """

    def __init__(self, portal=None):
        # type: (Portal or None) -> None
        Tile.__init__(self, portal)
        self.name = "SAND"


class GrassTile(LandTile):
    """
    This class contains attributes of a tile representing grass.
    """

    def __init__(self, portal=None):
        # type: (Portal or None) -> None
        Tile.__init__(self, portal)
        self.name = "GRASS"


class ShopTile(LandTile):
    """
    This class contains attributes of a tile representing shop.
    """

    def __init__(self, items_sold, portal=None):
        # type: (list, Portal or None) -> None
        Tile.__init__(self, portal)
        self.name = "SHOP"
        self.__items_sold: list = items_sold

    def get_items_sold(self):
        # type: () -> list
        return self.__items_sold


class WaterTile(Tile):
    """
    This class contains attributes of a tile representing water.
    """

    def __init__(self, portal=None):
        # type: (Portal or None) -> None
        Tile.__init__(self, portal)
        self.name = "WATER"


class GameCharacter:
    """
    This class contains attributes of a character in this game.
    """

    def __init__(self, name, location):
        # type: (str, Location) -> None
        self.game_character_id: str = str(uuid.uuid1())  # Generating random game character ID
        self.name: str = name
        self.location: Location = location
        self.location.get_tile().add_game_character(self)

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Game Character ID: " + str(self.game_character_id) + "\n"
        res += "Name: " + str(self.name) + "\n"
        res += "Location: " + str(self.location) + "\n"
        return res

    def interact_with_npc(self, npc):
        # type: (NPC) -> str
        return str(npc.message)

    def enter_portal(self):
        # type: () -> bool
        if isinstance(self.location.get_tile().portal, Portal):
            portal: Portal = self.location.get_tile().portal
            self.location = portal.location_to
            return True
        return False

    def clone(self):
        # type: () -> GameCharacter
        return copy.deepcopy(self)


class NPC(GameCharacter):
    """
    This class contains attributes of a non-playing character in this game.
    """

    def __init__(self, name, location, message):
        # type: (str, Location, str) -> None
        GameCharacter.__init__(self, name, location)
        self.message: str = message

    def __str__(self):
        # type: () -> str
        res: str = GameCharacter.__str__(self)
        res += "Message: " + str(self.message)
        return res


class Trainer(GameCharacter):
    """
    This class contains attributes of a trainer in this game.
    """

    def __init__(self, name, location, battle_team):
        # type: (str, Location, Team) -> None
        GameCharacter.__init__(self, name, location)
        self.battle_team: Team = battle_team
        self.item_inventory: ItemInventory = ItemInventory()
        self.legendary_creature_inventory: LegendaryCreatureInventory = LegendaryCreatureInventory()
        self.level: int = 1
        self.exp: mpf = mpf("0")
        self.required_exp: mpf = mpf("1e6")
        self.coins: mpf = mpf("0")

    def __str__(self):
        # type: () -> str
        res: str = GameCharacter.__str__(self)
        res += "Below is the team brought by this player for battles.\n" + str(self.battle_team) + "\n"
        res += "ITEM INVENTORY\n" + str(self.item_inventory) + "\n"
        res += "LEGENDARY CREATURE INVENTORY\n" + \
               str(self.legendary_creature_inventory) + "\n"
        res += "Level: " + str(self.level) + "\n"
        res += "EXP: " + str(self.exp) + "\n"
        res += "EXP needed to have in order to reach next level: " + str(self.required_exp) + "\n"
        res += "Coins: " + str(self.coins) + "\n"
        return res

    def place_rune_on_legendary_creature(self, legendary_creature, rune):
        # type: (LegendaryCreature, Rune) -> bool
        if legendary_creature in self.legendary_creature_inventory.get_legendary_creatures() and rune in \
                self.item_inventory.get_items():
            legendary_creature.place_rune(rune)
            return True
        return False

    def remove_rune_from_legendary_creature(self, legendary_creature, slot_number):
        # type: (LegendaryCreature, int) -> bool
        if legendary_creature in self.legendary_creature_inventory.get_legendary_creatures():
            if slot_number in legendary_creature.get_runes().keys():
                legendary_creature.remove_rune(slot_number)
            return False
        return False

    def level_up(self):
        # type: () -> None
        while self.exp >= self.required_exp:
            self.level += 1
            self.required_exp *= mpf("10") ** self.level

    def purchase_item(self, item):
        # type: (Item) -> bool
        if self.coins >= item.coin_cost:
            self.coins -= item.coin_cost
            self.add_item_to_inventory(item)
            return True
        return False

    def sell_item(self, item):
        # type: (Item) -> bool
        if item in self.item_inventory.get_items():
            self.remove_item_from_inventory(item)
            self.coins += item.sell_coin_gain
            return True
        return False

    def level_up_rune(self, rune):
        # type: (Rune) -> bool
        if rune not in self.item_inventory.get_items():
            return False

        if self.coins >= rune.level_up_coin_cost:
            self.coins -= rune.level_up_coin_cost
            rune.level_up()
            return True
        return False

    def add_item_to_inventory(self, item):
        # type: (Item) -> None
        self.item_inventory.add_item(item)

    def remove_item_from_inventory(self, item):
        # type: (Item) -> bool
        return self.item_inventory.remove_item(item)

    def add_legendary_creature_to_training_center(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if legendary_creature not in self.legendary_creature_inventory.get_legendary_creatures():
            return False

        curr_tile: Tile or None = self.location.get_tile()
        if isinstance(curr_tile, Tile):
            if isinstance(curr_tile, TrainingCenterTile):
                training_center_tile: TrainingCenterTile = curr_tile
                return training_center_tile.add_legendary_creature(legendary_creature)

            return False
        return False

    def remove_legendary_creature_from_training_center(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        curr_tile: Tile or None = self.location.get_tile()
        if isinstance(curr_tile, Tile):
            if isinstance(curr_tile, TrainingCenterTile):
                training_center_tile: TrainingCenterTile = curr_tile
                return training_center_tile.remove_legendary_creature(legendary_creature)

            return False
        return False

    def catch_legendary_creature(self, legendary_creature, ball):
        # type: (LegendaryCreature, Ball) -> bool
        if ball not in self.item_inventory.get_items():
            return False
        else:
            legendary_creature_hp_percentage_loss: float = 100 - ((legendary_creature.curr_hp /
                                                                   legendary_creature.max_hp) * 100)
            catch: bool = random.random() <= ball.catch_success_rate + (legendary_creature_hp_percentage_loss / 100)
            if catch:
                self.add_legendary_creature(legendary_creature)
                self.add_legendary_creature_to_team(legendary_creature)
                return True
            return False

    def add_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> None
        self.legendary_creature_inventory.add_legendary_creature(legendary_creature)

    def remove_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        return self.legendary_creature_inventory.remove_legendary_creature(legendary_creature)

    def add_legendary_creature_to_team(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if legendary_creature in self.legendary_creature_inventory.get_legendary_creatures():
            return self.battle_team.add_legendary_creature(legendary_creature)
        return False

    def remove_legendary_creature_from_team(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        return self.battle_team.remove_legendary_creature(legendary_creature)


class Player(Trainer):
    """
    This class contains attributes of the player in this game.
    """

    def __init__(self, name, location):
        # type: (str, Location) -> None
        Trainer.__init__(self, name, location, Team())


class CPUTrainer(Trainer):
    """
    This class contains attributes of a CPU-controlled trainer.
    """

    def __init__(self, name, location, battle_team):
        # type: (str, Location, Team) -> None
        Trainer.__init__(self, name, location, battle_team)
        self.times_beaten: int = 0  # initial value

    def __str__(self):
        # type: () -> str
        res: str = Trainer.__str__(self)
        res += "Times beaten: " + str(self.times_beaten) + "\n"
        return res

    def get_beaten(self):
        # type: () -> None
        self.times_beaten += 1
        for legendary_creature in self.legendary_creature_inventory.get_legendary_creatures():
            for i in range(2 ** self.times_beaten):
                legendary_creature.level_up()


class LegendaryCreatureInventory:
    """
    This class contains attributes of a legendary creature inventory to store legendary creatures.
    """

    def __init__(self):
        # type: () -> None
        self.__legendary_creatures: list = []

    def __str__(self):
        # type: () -> str
        res: str = "Below is a list of legendary creatures in this inventory.\n"  # initial value
        for legendary_creature in self.__legendary_creatures:
            res += str(legendary_creature) + "\n"

        return res

    def add_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> None
        self.__legendary_creatures.append(legendary_creature)

    def remove_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if legendary_creature in self.__legendary_creatures:
            self.__legendary_creatures.remove(legendary_creature)
            return True
        return False

    def get_legendary_creatures(self):
        # type: () -> list
        return self.__legendary_creatures

    def clone(self):
        # type: () -> LegendaryCreatureInventory
        return copy.deepcopy(self)


class ItemInventory:
    """
    This class contains attributes of an inventory to store items.
    """

    def __init__(self):
        # type: () -> None
        self.__items: list = []

    def __str__(self):
        # type: () -> str
        res: str = "Below is a list of items in this inventory.\n"
        for item in self.__items:
            res += str(item) + "\n"

        return res

    def add_item(self, item):
        # type: (Item) -> None
        self.__items.append(item)

    def remove_item(self, item):
        # type: (Item) -> bool
        if item in self.__items:
            self.__items.remove(item)
            return True
        return False

    def get_items(self):
        # type: () -> list
        return self.__items

    def clone(self):
        # type: () -> ItemInventory
        return copy.deepcopy(self)


class Team:
    """
    This class contains attributes of a team brought to battles.
    """

    MIN_LEGENDARY_CREATURES: int = 0
    MAX_LEGENDARY_CREATURES: int = 5
    __legendary_creatures: list = []

    def __init__(self, legendary_creatures=None):
        # type: (list) -> None
        if legendary_creatures is None:
            legendary_creatures = []
        if self.MIN_LEGENDARY_CREATURES <= len(legendary_creatures) <= self.MAX_LEGENDARY_CREATURES:
            self.__legendary_creatures = legendary_creatures
        else:
            self.__legendary_creatures = []

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        for legendary_creature in self.__legendary_creatures:
            res += str(legendary_creature) + "\n"

        return res

    def add_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if len(self.__legendary_creatures) < self.MAX_LEGENDARY_CREATURES:
            self.__legendary_creatures.append(legendary_creature)
            return True
        return False

    def remove_legendary_creature(self, legendary_creature):
        # type: (LegendaryCreature) -> bool
        if legendary_creature in self.__legendary_creatures:
            self.__legendary_creatures.remove(legendary_creature)
            return True
        return False

    def get_legendary_creatures(self):
        # type: () -> list
        return self.__legendary_creatures

    def clone(self):
        # type: () -> Team
        return copy.deepcopy(self)


class Item:
    """
    This class contains attributes of an item in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        self.name: str = name
        self.description: str = description
        self.coin_cost: mpf = coin_cost
        self.sell_coin_gain: mpf = coin_cost / 5

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Name: " + str(self.name) + "\n"
        res += "Description: " + str(self.description) + "\n"
        res += "Coin Cost: " + str(self.coin_cost) + "\n"
        res += "Sell Coin Gain: " + str(self.sell_coin_gain) + "\n"
        return res

    def clone(self):
        # type: () -> Item
        return copy.deepcopy(self)


class StatIncrease:
    """
    This class contains attributes of increase in stats of a rune.
    """

    def __init__(self, max_hp_up, max_hp_percentage_up, max_magic_points_up, max_magic_points_percentage_up,
                 attack_up, attack_percentage_up, defense_up, defense_percentage_up, attack_speed_up, crit_rate_up,
                 crit_damage_up, resistance_up, accuracy_up):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf) -> None
        self.max_hp_up: mpf = max_hp_up
        self.max_hp_percentage_up: mpf = max_hp_percentage_up
        self.max_magic_points_up: mpf = max_magic_points_up
        self.max_magic_points_percentage_up: mpf = max_magic_points_percentage_up
        self.attack_up: mpf = attack_up
        self.attack_percentage_up: mpf = attack_percentage_up
        self.defense_up: mpf = defense_up
        self.defense_percentage_up: mpf = defense_percentage_up
        self.attack_speed_up: mpf = attack_speed_up
        self.crit_rate_up: mpf = crit_rate_up
        self.crit_damage_up: mpf = crit_damage_up
        self.resistance_up: mpf = resistance_up
        self.accuracy_up: mpf = accuracy_up

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Max HP Up: " + str(self.max_hp_up) + "\n"
        res += "Max HP Percentage Up: " + str(self.max_hp_percentage_up * 100) + "%\n"
        res += "Max Magic Points Up: " + str(self.max_magic_points_up) + "\n"
        res += "Max Magic Points Percentage Up: " + str(self.max_magic_points_percentage_up * 100) + "%\n"
        res += "Attack Up: " + str(self.attack_up) + "\n"
        res += "Attack Percentage Up: " + str(self.attack_percentage_up * 100) + "%\n"
        res += "Defense Up: " + str(self.defense_up) + "\n"
        res += "Defense Percentage Up: " + str(self.defense_percentage_up * 100) + "%\n"
        res += "Attack Speed Up: " + str(self.attack_speed_up) + "\n"
        res += "Crit Rate Up: " + str(self.crit_rate_up * 100) + "%\n"
        res += "Crit Damage Up: " + str(self.crit_damage_up * 100) + "%\n"
        res += "Resistance Up: " + str(self.resistance_up * 100) + "%\n"
        res += "Accuracy Up: " + str(self.accuracy_up * 100) + "%\n"
        return res

    def clone(self):
        # type: () -> StatIncrease
        return copy.deepcopy(self)


class Rune(Item):
    """
    This class contains attributes of a rune to strengthen legendary creatures in this game.
    """

    MIN_RATING: int = 1
    MAX_RATING: int = 6
    MIN_SLOT_NUMBER: int = 1
    MAX_SLOT_NUMBER: int = 8

    def __init__(self, name, description, coin_cost, rating, slot_number):
        # type: (str, str, mpf, int, int) -> None
        Item.__init__(self, name, description, coin_cost)
        self.rating: int = rating if self.MIN_RATING <= rating <= self.MAX_RATING else self.MIN_RATING
        self.slot_number: int = slot_number if self.MIN_SLOT_NUMBER <= slot_number <= self.MAX_SLOT_NUMBER else \
            self.MIN_SLOT_NUMBER
        self.stat_increase: StatIncrease = StatIncrease(mpf("10") ** (6 * self.rating), mpf(2 * self.rating),
                                                        mpf("10") ** (6 * self.rating), mpf(2 * self.rating),
                                                        mpf("10") ** (5 * self.rating), mpf(2 * self.rating),
                                                        mpf("10") ** (5 * self.rating), mpf(2 * self.rating),
                                                        mpf(2 * self.rating), mpf(0.01 * self.rating),
                                                        mpf(0.05 * self.rating), mpf(0.01 * self.rating),
                                                        mpf(0.01 * self.rating))
        self.level: int = 1
        self.level_up_coin_cost: mpf = coin_cost

    def __str__(self):
        # type: () -> str
        res: str = Item.__str__(self)
        res += "Rating: " + str(self.rating) + "\n"
        res += "Slot Number: " + str(self.slot_number) + "\n"
        res += "Stat Increase:\n" + str(self.stat_increase) + "\n"
        res += "Level: " + str(self.level) + "\n"
        res += "Level Up Coin Cost: " + str(self.level_up_coin_cost) + "\n"
        return res

    def level_up(self):
        # type: () -> None
        self.level += 1
        self.level_up_coin_cost *= mpf("10") ** self.level
        self.stat_increase.max_hp_up *= mpf("10") ** self.rating
        self.stat_increase.max_hp_percentage_up += self.rating
        self.stat_increase.max_magic_points_up *= mpf("10") ** self.rating
        self.stat_increase.max_magic_points_percentage_up += self.rating
        self.stat_increase.attack_up *= mpf("10") ** self.rating
        self.stat_increase.attack_percentage_up += self.rating
        self.stat_increase.defense_up *= mpf("10") ** self.rating
        self.stat_increase.defense_percentage_up += self.rating
        self.stat_increase.attack_speed_up += 2 * self.rating
        self.stat_increase.crit_rate_up += 0.01 * self.rating
        self.stat_increase.crit_damage_up += 0.05 * self.rating
        self.stat_increase.resistance_up += 0.01 * self.rating
        self.stat_increase.accuracy_up += 0.01 * self.rating


class EXPShard(Item):
    """
    This class contains attributes of an EXP shard to add the EXP of legendary creatures.
    """

    def __init__(self, name, description, coin_cost, exp_granted):
        # type: (str, str, mpf, mpf) -> None
        Item.__init__(self, name, description, coin_cost)
        self.exp_granted: mpf = exp_granted

    def __str__(self):
        # type: () -> str
        res: str = Item.__str__(self)
        res += "EXP Granted: " + str(self.exp_granted) + "\n"
        return res


class LevelUpShard(Item):
    """
    This class contains attributes of a level up shared to level up legendary creatures.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Item.__init__(self, name, description, coin_cost)


class SkillLevelUpShard(Item):
    """
    This class contains attributes of a skill level up shard to level up skills owned by legendary creatures.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Item.__init__(self, name, description, coin_cost)


class EvolutionCandy(Item):
    """
    This class contains attributes of a candy to evolve a legendary creature.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Item.__init__(self, name, description, coin_cost)


class FishingRod(Item):
    """
    This class contains attributes of a fishing rod to encounter legendary creatures underwater.
    """

    def __init__(self, name, description, coin_cost, encounter_legendary_creature_chance):
        # type: (str, str, mpf, float) -> None
        Item.__init__(self, name, description, coin_cost)
        self.encounter_legendary_creature_chance: float = encounter_legendary_creature_chance


class Ball(Item):
    """
    This class contains attributes of a ball used to catch legendary creatures.
    """

    def __init__(self, name, description, coin_cost, catch_success_rate):
        # type: (str, str, mpf, float) -> None
        Item.__init__(self, name, description, coin_cost)
        self.catch_success_rate: float = catch_success_rate

    def __str__(self):
        # type: () -> str
        res: str = Item.__str__(self)
        res += "Catch Success Rate: " + str(self.catch_success_rate * 100) + "%\n"
        return res


class LegendaryCreature:
    """
    This class contains attributes of a legendary creature in this game.
    """

    MAX_CRIT_RATE: mpf = mpf("1")
    MAX_RESISTANCE: mpf = mpf("1")
    MAX_ACCURACY: mpf = mpf("1")
    MIN_ATTACK_GAUGE: mpf = mpf("0")
    FULL_ATTACK_GAUGE: mpf = mpf("1")
    POSSIBLE_TYPES: list = ["LAND", "WATER"]

    def __init__(self, name, creature_type, max_hp, max_magic_points, attack_power, defense, attack_speed, skills):
        # type: (str, str, mpf, mpf, mpf, mpf, int, list) -> None
        self.name: str = name
        self.creature_type: str = creature_type if creature_type in self.POSSIBLE_TYPES else self.POSSIBLE_TYPES[0]
        self.level: int = 1
        self.exp: mpf = mpf("0")
        self.required_exp: mpf = mpf("1e6")
        self.curr_hp: mpf = max_hp
        self.max_hp: mpf = max_hp
        self.curr_magic_points: mpf = max_magic_points
        self.max_magic_points: mpf = max_magic_points
        self.attack_power: mpf = attack_power
        self.defense: mpf = defense
        self.attack_speed: int = attack_speed
        self.__skills: list = skills
        self.__runes: dict = {}  # initial value
        self.crit_rate: mpf = mpf("0.15")
        self.crit_damage: mpf = mpf("1.5")
        self.resistance: mpf = mpf("0.15")
        self.accuracy: mpf = mpf("0")
        self.attack_power_percentage_up: mpf = mpf("0")
        self.attack_power_percentage_down: mpf = mpf("0")
        self.defense_percentage_up: mpf = mpf("0")
        self.defense_percentage_down: mpf = mpf("0")
        self.attack_gauge: mpf = mpf("0")
        self.has_evolved: bool = False

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Name: " + str(self.name) + "\n"
        res += "Creature Type: " + str(self.creature_type) + "\n"
        res += "Level: " + str(self.level) + "\n"
        res += "EXP: " + str(self.exp) + "\n"
        res += "EXP needed to have in order to reach next level: " + str(self.required_exp) + "\n"
        res += "HP: " + str(self.curr_hp) + "/" + str(self.max_hp) + "\n"
        res += "Magic Points: " + str(self.curr_magic_points) + "/" + str(self.max_magic_points) + "\n"
        res += "Attack Power: " + str(self.attack_power) + "\n"
        res += "Defense: " + str(self.defense) + "\n"
        res += "Attack Speed: " + str(self.attack_speed) + "\n"
        res += "Below is a list of skills this legendary creature has.\n"
        skill_number: int = 1
        for skill in self.__skills:
            res += "Skill #" + str(skill_number) + "\n"
            res += str(skill) + "\n"

        res += "Runes equipped to this legendary creature:\n"
        for i in range(1, 9):
            res += "Slot #" + str(i) + "\n"
            res += str(self.__runes[i]) + "\n"

        res += "Crit Rate: " + str(self.crit_rate * 100) + "%\n"
        res += "Crit Damage: " + str(self.crit_damage * 100) + "%\n"
        res += "Resistance: " + str(self.resistance * 100) + "%\n"
        res += "Accuracy: " + str(self.accuracy * 100) + "%\n"
        res += "Attack Power Percentage Up: " + str(self.attack_power_percentage_up * 100) + "%\n"
        res += "Attack Power Percentage Down: " + str(self.attack_power_percentage_down * 100) + "%\n"
        res += "Defense Percentage Up: " + str(self.defense_percentage_up * 100) + "%\n"
        res += "Defense Percentage Down: " + str(self.defense_percentage_down * 100) + "%\n"
        res += "Attack Gauge: " + str(self.attack_gauge * 100) + "%\n"
        res += "Has it evolved? " + str(self.has_evolved) + "\n"
        return res

    def evolve(self):
        # type: () -> bool
        if self.has_evolved:
            return False
        self.has_evolved = True
        self.max_hp *= mpf("1e5")
        self.max_magic_points *= mpf("1e5")
        self.attack_power *= mpf("1e5")
        self.defense *= mpf("1e5")
        self.attack_speed += 15
        self.crit_rate += 0.15
        self.crit_damage += 0.5
        self.resistance += 0.15
        self.accuracy += 0.15
        self.restore()
        return True

    def recover_magic_points(self):
        # type: () -> None
        self.curr_magic_points += self.max_magic_points / 12
        if self.curr_magic_points >= self.max_magic_points:
            self.curr_magic_points = self.max_magic_points

    def restore(self):
        # type: () -> None
        self.attack_gauge = self.MIN_ATTACK_GAUGE
        self.curr_hp = self.max_hp
        self.curr_magic_points = self.max_magic_points
        self.attack_power_percentage_up = mpf("0")
        self.attack_power_percentage_down = mpf("0")
        self.defense_percentage_up = mpf("0")
        self.defense_percentage_down = mpf("0")

    def get_runes(self):
        # type: () -> dict
        return self.__runes

    def place_rune(self, rune):
        # type: (Rune) -> None
        if rune.slot_number in self.__runes.keys():
            self.remove_rune(rune.slot_number)
        else:
            self.__runes[rune.slot_number] = rune
            self.max_hp *= 1 + (rune.stat_increase.max_hp_percentage_up / 100)
            self.max_hp += rune.stat_increase.max_hp_up
            self.max_magic_points *= 1 + (rune.stat_increase.max_magic_points_percentage_up / 100)
            self.max_magic_points += rune.stat_increase.max_magic_points_up
            self.attack_power *= 1 + (rune.stat_increase.attack_percentage_up / 100)
            self.attack_power += rune.stat_increase.attack_up
            self.defense *= 1 + (rune.stat_increase.defense_percentage_up / 100)
            self.defense += rune.stat_increase.defense_up
            self.attack_speed += rune.stat_increase.attack_speed_up
            self.crit_rate += rune.stat_increase.crit_rate_up
            self.crit_damage += rune.stat_increase.crit_damage_up
            self.resistance += rune.stat_increase.resistance_up
            self.accuracy += rune.stat_increase.accuracy_up
            self.restore()

    def remove_rune(self, slot_number):
        # type: (int) -> bool
        if slot_number in self.__runes.keys():
            # Removing the rune at current slot.
            current_rune: Rune = self.__runes[slot_number]
            self.max_hp -= current_rune.stat_increase.max_hp_up
            self.max_hp /= 1 + (current_rune.stat_increase.max_hp_percentage_up / 100)
            self.max_magic_points -= current_rune.stat_increase.max_magic_points_up
            self.max_magic_points /= 1 + (current_rune.stat_increase.max_magic_points_percentage_up / 100)
            self.attack_power -= current_rune.stat_increase.attack_up
            self.attack_power /= 1 + (current_rune.stat_increase.attack_percentage_up / 100)
            self.defense -= current_rune.stat_increase.defense_up
            self.defense /= 1 + (current_rune.stat_increase.defense_percentage_up / 100)
            self.attack_speed -= current_rune.stat_increase.attack_speed_up
            self.crit_rate -= current_rune.stat_increase.crit_rate_up
            self.crit_damage -= current_rune.stat_increase.crit_damage_up
            self.resistance -= current_rune.stat_increase.resistance_up
            self.accuracy -= current_rune.stat_increase.accuracy_up
            self.restore()
            return True
        return False

    def level_up(self):
        # type: () -> None
        while self.exp >= self.required_exp:
            self.level += 1
            self.required_exp *= mpf("10") ** self.level
            self.attack_power *= triangular(self.level)
            self.max_hp *= triangular(self.level)
            self.max_magic_points *= triangular(self.level)
            self.defense *= triangular(self.level)
            self.attack_speed += 2
            self.restore()

    def normal_attack(self, other):
        # type: (LegendaryCreature) -> None
        action: Action = Action("NORMAL ATTACK")
        action.execute(self, other)

    def normal_heal(self, other):
        # type: (LegendaryCreature) -> None
        action: Action = Action("NORMAL HEAL")
        action.execute(self, other)

    def use_skill(self, other, skill):
        # type: (LegendaryCreature, Skill) -> bool
        if skill not in self.__skills:
            return False

        if self.curr_magic_points < skill.magic_points_cost:
            return False

        action: Action = Action("USE SKILL")
        action.execute(self, other, skill)
        self.curr_magic_points -= skill.magic_points_cost
        return True

    def get_is_alive(self):
        # type: () -> bool
        return self.curr_hp > 0

    def get_skills(self):
        # type: () -> list
        return self.__skills

    def clone(self):
        # type: () -> LegendaryCreature
        return copy.deepcopy(self)


class Skill:
    """
    This class contains attributes of a skill legendary creatures have.
    """

    def __init__(self, name, description, magic_points_cost):
        # type: (str, str, mpf) -> None
        self.name: str = name
        self.description: str = description
        self.magic_points_cost: mpf = magic_points_cost
        self.level: int = 1

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Name: " + str(self.name) + "\n"
        res += "Description: " + str(self.description) + "\n"
        res += "Magic Points Cost: " + str(self.magic_points_cost) + "\n"
        res += "Level: " + str(self.level) + "\n"
        return res

    def level_up(self):
        # type: () -> None
        pass

    def clone(self):
        # type: () -> Skill
        return copy.deepcopy(self)


class AttackSkill(Skill):
    """
    This class contains attributes of a skill to attack an enemy.
    """

    def __init__(self, name, description, magic_points_cost, damage_multiplier, does_ignore_enemies_defense):
        # type: (str, str, mpf, DamageMultiplier, bool) -> None
        Skill.__init__(self, name, description, magic_points_cost)
        self.damage_multiplier: DamageMultiplier = damage_multiplier
        self.does_ignore_enemies_defense: bool = does_ignore_enemies_defense

    def __str__(self):
        # type: () -> str
        res: str = Skill.__str__(self)
        res += "Damage Multiplier:\n" + str(self.damage_multiplier) + "\n"
        res += "Does it ignore enemy's defense: " + str(self.does_ignore_enemies_defense) + "\n"
        return res

    def level_up(self):
        # type: () -> None
        self.level += 1
        self.damage_multiplier.multiplier_to_self_max_hp *= mpf("1.25")
        self.damage_multiplier.multiplier_to_enemy_max_hp *= mpf("1.25")
        self.damage_multiplier.multiplier_to_self_attack_power *= mpf("1.25")
        self.damage_multiplier.multiplier_to_enemy_attack_power *= mpf("1.25")
        self.damage_multiplier.multiplier_to_self_defense *= mpf("1.25")
        self.damage_multiplier.multiplier_to_enemy_defense *= mpf("1.25")
        self.damage_multiplier.multiplier_to_self_max_magic_points *= mpf("1.25")
        self.damage_multiplier.multiplier_to_enemy_max_magic_points *= mpf("1.25")


class HealSkill(Skill):
    """
    This class contains attributes of a skill to heal self.
    """

    def __init__(self, name, description, magic_points_cost, heal_amount):
        # type: (str, str, mpf, mpf) -> None
        Skill.__init__(self, name, description, magic_points_cost)
        self.heal_amount: mpf = heal_amount

    def __str__(self):
        # type: () -> str
        res: str = Skill.__str__(self)
        res += "Heal Amount: " + str(self.heal_amount) + "\n"
        return res

    def level_up(self):
        # type: () -> None
        self.level += 1
        self.heal_amount *= 2


class StrengthenSkill(Skill):
    """
    This class contains attributes of a skill to strengthen self.
    """

    def __init__(self, name, description, magic_points_cost, self_attack_percentage_up, self_defense_percentage_up):
        # type: (str, str, mpf, mpf, mpf) -> None
        Skill.__init__(self, name, description, magic_points_cost)
        self.self_attack_percentage_up: mpf = self_attack_percentage_up
        self.self_defense_percentage_up: mpf = self_defense_percentage_up

    def __str__(self):
        # type: () -> str
        res: str = Skill.__str__(self)
        res += "Attack Percentage Up to Self: " + str(self.self_attack_percentage_up * 100) + "%\n"
        res += "Defense Percentage Up to Self: " + str(self.self_defense_percentage_up * 100) + "%\n"
        return res


class WeakeningSkill(Skill):
    """
    This class contains attributes of a skill to weaken enemies.
    """

    def __init__(self, name, description, magic_points_cost, enemy_attack_percentage_down,
                 enemy_defense_percentage_down):
        # type: (str, str, mpf, mpf, mpf) -> None
        Skill.__init__(self, name, description, magic_points_cost)
        self.enemy_attack_percentage_down: mpf = enemy_attack_percentage_down
        self.enemy_defense_percentage_down: mpf = enemy_defense_percentage_down

    def __str__(self):
        # type: () -> str
        res: str = Skill.__str__(self)
        res += "Attack Percentage Down to Enemy: " + str(self.enemy_attack_percentage_down * 100) + "%\n"
        res += "Defense Percentage Down to Enemy: " + str(self.enemy_defense_percentage_down * 100) + "%\n"
        return res


class DamageMultiplier:
    """
    This class contains attributes of damage multiplier.
    """

    def __init__(self, multiplier_to_self_max_hp, multiplier_to_enemy_max_hp, multiplier_to_self_attack_power,
                 multiplier_to_enemy_attack_power, multiplier_to_self_defense, multiplier_to_enemy_defense,
                 multiplier_to_self_max_magic_points, multiplier_to_enemy_max_magic_points,
                 multiplier_to_self_attack_speed, multiplier_to_enemy_attack_speed):
        # type: (float, float, float, float, float, float, float, float, float, float) -> None
        self.multiplier_to_self_max_hp: float = multiplier_to_self_max_hp
        self.multiplier_to_enemy_max_hp: float = multiplier_to_enemy_max_hp
        self.multiplier_to_self_attack_power: float = multiplier_to_self_attack_power
        self.multiplier_to_enemy_attack_power: float = multiplier_to_enemy_attack_power
        self.multiplier_to_self_defense: float = multiplier_to_self_defense
        self.multiplier_to_enemy_defense: float = multiplier_to_enemy_defense
        self.multiplier_to_self_max_magic_points: float = multiplier_to_self_max_magic_points
        self.multiplier_to_enemy_max_magic_points: float = multiplier_to_enemy_max_magic_points
        self.multiplier_to_self_attack_speed: float = multiplier_to_self_attack_speed
        self.multiplier_to_enemy_attack_speed: float = multiplier_to_enemy_attack_speed

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Damage Multiplier to Self Max HP: " + str(self.multiplier_to_self_max_hp) + "\n"
        res += "Damage Multiplier to Enemy's Max HP: " + str(self.multiplier_to_enemy_max_hp) + "\n"
        res += "Damage Multiplier to Self Attack Power: " + str(self.multiplier_to_self_attack_power) + "\n"
        res += "Damage Multiplier to Enemy's Attack Power: " + str(self.multiplier_to_enemy_attack_power) + "\n"
        res += "Damage Multiplier to Self Defense: " + str(self.multiplier_to_self_defense) + "\n"
        res += "Damage Multiplier to Enemy's Defense: " + str(self.multiplier_to_enemy_defense) + "\n"
        res += "Damage Multiplier to Self Max Magic Points: " + str(self.multiplier_to_self_max_magic_points) + "\n"
        res += "Damage Multiplier to Enemy's Max Magic Points: " + str(self.multiplier_to_enemy_max_magic_points) + "\n"
        res += "Damage Multiplier to Self Attack Speed: " + str(self.multiplier_to_self_attack_speed) + "\n"
        res += "Damage Multiplier to Enemy's Attack Speed: " + str(self.multiplier_to_enemy_attack_speed) + "\n"
        return res

    def calculate_raw_damage_without_enemy_defense(self, user, target):
        # type: (LegendaryCreature, LegendaryCreature) -> mpf
        return user.max_hp * self.multiplier_to_self_max_hp + target.max_hp * self.multiplier_to_enemy_max_hp + \
               user.attack_power * (1 + user.attack_power_percentage_up / 100 -
                                    user.attack_power_percentage_down / 100) * \
               (self.multiplier_to_self_attack_speed * user.attack_speed) \
               * self.multiplier_to_self_attack_power + target.attack_power * (
                       1 + target.attack_power_percentage_up / 100
                       - target.attack_power_percentage_down / 100) * \
               (self.multiplier_to_enemy_attack_speed * target.attack_speed) * \
               self.multiplier_to_enemy_attack_power + user.defense * (1 + user.defense_percentage_up / 100 -
                                        user.defense_percentage_down / 100) * self.multiplier_to_self_defense + \
               target.defense * (1 + target.defense_percentage_up / 100 - target.defense_percentage_down / 100) * \
               self.multiplier_to_enemy_defense + user.max_magic_points * \
               self.multiplier_to_self_max_magic_points + target.max_magic_points * \
               self.multiplier_to_enemy_max_magic_points

    def calculate_raw_damage(self, user, target):
        # type: (LegendaryCreature, LegendaryCreature) -> mpf
        return self.calculate_raw_damage_without_enemy_defense(user, target) - target.defense

    def clone(self):
        # type: () -> DamageMultiplier
        return copy.deepcopy(self)


class Reward:
    """
    This class contains attributes of the reward for doing something in this game.
    """

    def __init__(self, player_coin_gain, player_exp_gain, legendary_creature_exp_gain):
        # type: (mpf, mpf, mpf) -> None
        self.player_coin_gain: mpf = player_coin_gain
        self.player_exp_gain: mpf = player_exp_gain
        self.legendary_creature_exp_gain: mpf = legendary_creature_exp_gain

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Player Coin Gain: " + str(self.player_coin_gain) + "\n"
        res += "Player EXP Gain: " + str(self.player_exp_gain) + "\n"
        res += "Legendary Creature EXP Gain: " + str(self.legendary_creature_exp_gain) + "\n"
        return res

    def clone(self):
        # type: () -> Reward
        return copy.deepcopy(self)


class Game:
    """
    This class contains attributes of the saved game data.
    """

    def __init__(self, player, opponent_trainers, cities, potential_legendary_creatures):
        # type: (Player, list, list, list) -> None
        self.player: Player = player
        self.__opponent_trainers: list = opponent_trainers
        self.__cities: list = cities
        self.__potential_legendary_creatures: list = potential_legendary_creatures

    def __str__(self):
        # type: () -> str
        res: str = "Player in the game:\n" + str(self.player) + "\n"
        res += "Below is a list of opponent trainers in the game:\n"
        for opponent_trainer in self.__opponent_trainers:
            res += str(opponent_trainer) + "\n"

        res += "Maps of cities in the game:\n"
        for city in self.__cities:
            res += str(city) + "\n"

        res += "Below is a list of potential legendary creatures in this game:\n"
        for legendary_creature in self.__potential_legendary_creatures:
            res += str(legendary_creature) + "\n"

        return res

    def get_opponent_trainers(self):
        # type: () -> list
        return self.__opponent_trainers

    def get_cities(self):
        # type: () -> list
        return self.__cities

    def get_potential_legendary_creatures(self):
        # type: () -> list
        return self.__potential_legendary_creatures

    def clone(self):
        # type: () -> Game
        return copy.deepcopy(self)


# Creating main function used to run the game


def main():
    """
    This main function is used to run the game.
    :return: None
    """

    print("Welcome to 'Legendary Creature Hunter at Mithoter Planet' by 'DtjiSoftwareDeveloper'.")
    print("This game is a turn based strategy game like Pokemon where you will hunt for legendary ")
    print("creatures around Mithoter Planet and battle against other trainers.")

    # Initialising important variables to be used throughout the game.

    items_sold_in_shop: list = [
        Rune("1-STAR RUNE SLOT 1", "Rune with rating of 1 with slot number 1.", mpf("1e5"), 1, 1),
        Rune("1-STAR RUNE SLOT 2", "Rune with rating of 1 with slot number 2.", mpf("1e5"), 1, 2),
        Rune("1-STAR RUNE SLOT 3", "Rune with rating of 1 with slot number 3.", mpf("1e5"), 1, 3),
        Rune("1-STAR RUNE SLOT 4", "Rune with rating of 1 with slot number 4.", mpf("1e5"), 1, 4),
        Rune("1-STAR RUNE SLOT 5", "Rune with rating of 1 with slot number 5.", mpf("1e5"), 1, 5),
        Rune("1-STAR RUNE SLOT 6", "Rune with rating of 1 with slot number 6.", mpf("1e5"), 1, 6),
        Rune("1-STAR RUNE SLOT 7", "Rune with rating of 1 with slot number 7.", mpf("1e5"), 1, 7),
        Rune("2-STAR RUNE SLOT 8", "Rune with rating of 2 with slot number 8.", mpf("1e5"), 1, 8),
        Rune("2-STAR RUNE SLOT 1", "Rune with rating of 2 with slot number 1.", mpf("1e10"), 2, 1),
        Rune("2-STAR RUNE SLOT 2", "Rune with rating of 2 with slot number 2.", mpf("1e10"), 2, 2),
        Rune("2-STAR RUNE SLOT 3", "Rune with rating of 2 with slot number 3.", mpf("1e10"), 2, 3),
        Rune("2-STAR RUNE SLOT 4", "Rune with rating of 2 with slot number 4.", mpf("1e10"), 2, 4),
        Rune("2-STAR RUNE SLOT 5", "Rune with rating of 2 with slot number 5.", mpf("1e10"), 2, 5),
        Rune("2-STAR RUNE SLOT 6", "Rune with rating of 2 with slot number 6.", mpf("1e10"), 2, 6),
        Rune("2-STAR RUNE SLOT 7", "Rune with rating of 2 with slot number 7.", mpf("1e10"), 2, 7),
        Rune("2-STAR RUNE SLOT 8", "Rune with rating of 2 with slot number 8.", mpf("1e10"), 2, 8),
        Rune("3-STAR RUNE SLOT 1", "Rune with rating of 3 with slot number 1.", mpf("1e20"), 3, 1),
        Rune("3-STAR RUNE SLOT 2", "Rune with rating of 3 with slot number 2.", mpf("1e20"), 3, 2),
        Rune("3-STAR RUNE SLOT 3", "Rune with rating of 3 with slot number 3.", mpf("1e20"), 3, 3),
        Rune("3-STAR RUNE SLOT 4", "Rune with rating of 3 with slot number 4.", mpf("1e20"), 3, 4),
        Rune("3-STAR RUNE SLOT 5", "Rune with rating of 3 with slot number 5.", mpf("1e20"), 3, 5),
        Rune("3-STAR RUNE SLOT 6", "Rune with rating of 3 with slot number 6.", mpf("1e20"), 3, 6),
        Rune("3-STAR RUNE SLOT 7", "Rune with rating of 3 with slot number 7.", mpf("1e20"), 3, 7),
        Rune("3-STAR RUNE SLOT 8", "Rune with rating of 3 with slot number 8.", mpf("1e20"), 3, 8),
        Rune("4-STAR RUNE SLOT 1", "Rune with rating of 4 with slot number 1.", mpf("1e40"), 4, 1),
        Rune("4-STAR RUNE SLOT 2", "Rune with rating of 4 with slot number 2.", mpf("1e40"), 4, 2),
        Rune("4-STAR RUNE SLOT 3", "Rune with rating of 4 with slot number 3.", mpf("1e40"), 4, 3),
        Rune("4-STAR RUNE SLOT 4", "Rune with rating of 4 with slot number 4.", mpf("1e40"), 4, 4),
        Rune("4-STAR RUNE SLOT 5", "Rune with rating of 4 with slot number 5.", mpf("1e40"), 4, 5),
        Rune("4-STAR RUNE SLOT 6", "Rune with rating of 4 with slot number 6.", mpf("1e40"), 4, 6),
        Rune("4-STAR RUNE SLOT 7", "Rune with rating of 4 with slot number 7.", mpf("1e40"), 4, 7),
        Rune("4-STAR RUNE SLOT 8", "Rune with rating of 4 with slot number 8.", mpf("1e40"), 4, 8),
        Rune("5-STAR RUNE SLOT 1", "Rune with rating of 5 with slot number 1.", mpf("1e80"), 5, 1),
        Rune("5-STAR RUNE SLOT 2", "Rune with rating of 5 with slot number 2.", mpf("1e80"), 5, 2),
        Rune("5-STAR RUNE SLOT 3", "Rune with rating of 5 with slot number 3.", mpf("1e80"), 5, 3),
        Rune("5-STAR RUNE SLOT 4", "Rune with rating of 5 with slot number 4.", mpf("1e80"), 5, 4),
        Rune("5-STAR RUNE SLOT 5", "Rune with rating of 5 with slot number 5.", mpf("1e80"), 5, 5),
        Rune("5-STAR RUNE SLOT 6", "Rune with rating of 5 with slot number 6.", mpf("1e80"), 5, 6),
        Rune("5-STAR RUNE SLOT 7", "Rune with rating of 5 with slot number 7.", mpf("1e80"), 5, 7),
        Rune("5-STAR RUNE SLOT 8", "Rune with rating of 5 with slot number 8.", mpf("1e80"), 5, 8),
        Rune("6-STAR RUNE SLOT 1", "Rune with rating of 6 with slot number 1.", mpf("1e160"), 6, 1),
        Rune("6-STAR RUNE SLOT 2", "Rune with rating of 6 with slot number 2.", mpf("1e160"), 6, 2),
        Rune("6-STAR RUNE SLOT 3", "Rune with rating of 6 with slot number 3.", mpf("1e160"), 6, 3),
        Rune("6-STAR RUNE SLOT 4", "Rune with rating of 6 with slot number 4.", mpf("1e160"), 6, 4),
        Rune("6-STAR RUNE SLOT 5", "Rune with rating of 6 with slot number 5.", mpf("1e160"), 6, 5),
        Rune("6-STAR RUNE SLOT 6", "Rune with rating of 6 with slot number 6.", mpf("1e160"), 6, 6),
        Rune("6-STAR RUNE SLOT 7", "Rune with rating of 6 with slot number 7.", mpf("1e160"), 6, 7),
        Rune("6-STAR RUNE SLOT 8", "Rune with rating of 6 with slot number 8.", mpf("1e160"), 6, 8),
        EXPShard("EXP SHARD #1", "EXP Shard #1.", mpf("1e10"), mpf("1e9")),
        EXPShard("EXP SHARD #2", "EXP Shard #2.", mpf("1e20"), mpf("1e19")),
        EXPShard("EXP SHARD #3", "EXP Shard #3.", mpf("1e40"), mpf("1e39")),
        EXPShard("EXP SHARD #4", "EXP Shard #4.", mpf("1e80"), mpf("1e79")),
        EXPShard("EXP SHARD #5", "EXP Shard #5.", mpf("1e160"), mpf("1e159")),
        EXPShard("EXP SHARD #6", "EXP Shard #6.", mpf("1e320"), mpf("1e319")),
        LevelUpShard("LEVEL UP SHARD", "A shard to immediately level up a legendary creature.", mpf("1e35")),
        SkillLevelUpShard("SKILL LEVEL UP SHARD", "A shard to level up a skill owned by a legendary creature.",
                          mpf("1e35")),
        EvolutionCandy("EVOLUTION CANDY", "An evolution candy to immediately evolve a legendary creature.",
                       mpf("1e35")),
        FishingRod("FISHING ROD #1", "Fishing Rod #1", mpf("1e10"), 0.1),
        FishingRod("FISHING ROD #2", "Fishing Rod #2", mpf("1e20"), 0.2),
        FishingRod("FISHING ROD #3", "Fishing Rod #3", mpf("1e40"), 0.3),
        FishingRod("FISHING ROD #4", "Fishing Rod #4", mpf("1e80"), 0.4),
        FishingRod("FISHING ROD #5", "Fishing Rod #5", mpf("1e160"), 0.5),
        Ball("BALL #1", "Ball #1", mpf("1e10"), 0.1),
        Ball("BALL #2", "Ball #2", mpf("1e20"), 0.2),
        Ball("BALL #3", "Ball #3", mpf("1e40"), 0.3),
        Ball("BALL #4", "Ball #4", mpf("1e80"), 0.4),
        Ball("BALL #5", "Ball #5", mpf("1e160"), 0.5)
    ]

    cities: list = [
        City("Timberhallow", 5, 5,
             [
                 [WaterTile(), SandTile(), SandTile(), GrassTile(), WaterTile()],
                 [SandTile(), GrassTile(), ShopTile(items_sold_in_shop), GrassTile(), WaterTile()],
                 [TrainingCenterTile(mpf("1e5")), GrassTile(), SandTile(), SandTile(), SandTile()],
                 [SandTile(), SandTile(), GrassTile(), GrassTile(), GrassTile()],
                 [GrassTile(), GrassTile(), TrainingCenterTile(mpf("1e5")), GrassTile(), GrassTile()]
             ]),
        City("Loststar", 5, 5,
             [
                 [WaterTile(), SandTile(), SandTile(), GrassTile(), WaterTile()],
                 [SandTile(), GrassTile(), ShopTile(items_sold_in_shop), GrassTile(), WaterTile()],
                 [TrainingCenterTile(mpf("1e10")), GrassTile(), SandTile(), SandTile(), SandTile()],
                 [SandTile(), SandTile(), GrassTile(), GrassTile(), GrassTile()],
                 [GrassTile(), GrassTile(), TrainingCenterTile(mpf("1e10")), GrassTile(), GrassTile()]
             ]),
        City("Mageborough", 5, 5,
             [
                 [WaterTile(), SandTile(), SandTile(), GrassTile(), WaterTile()],
                 [SandTile(), GrassTile(), ShopTile(items_sold_in_shop), GrassTile(), WaterTile()],
                 [TrainingCenterTile(mpf("1e20")), GrassTile(), SandTile(), SandTile(), SandTile()],
                 [SandTile(), SandTile(), GrassTile(), GrassTile(), GrassTile()],
                 [GrassTile(), GrassTile(), TrainingCenterTile(mpf("1e20")), GrassTile(), GrassTile()]
             ]),
        City("Coldpass", 5, 5,
             [
                 [WaterTile(), SandTile(), SandTile(), GrassTile(), WaterTile()],
                 [SandTile(), GrassTile(), ShopTile(items_sold_in_shop), GrassTile(), WaterTile()],
                 [TrainingCenterTile(mpf("1e20")), GrassTile(), SandTile(), SandTile(), SandTile()],
                 [SandTile(), SandTile(), GrassTile(), GrassTile(), GrassTile()],
                 [GrassTile(), GrassTile(), TrainingCenterTile(mpf("1e20")), GrassTile(), GrassTile()]
             ]),
        City("Whithollow", 5, 5,
             [
                 [WaterTile(), SandTile(), SandTile(), GrassTile(), WaterTile()],
                 [SandTile(), GrassTile(), ShopTile(items_sold_in_shop), GrassTile(), WaterTile()],
                 [TrainingCenterTile(mpf("1e20")), GrassTile(), SandTile(), SandTile(), SandTile()],
                 [SandTile(), SandTile(), GrassTile(), GrassTile(), GrassTile()],
                 [GrassTile(), GrassTile(), TrainingCenterTile(mpf("1e20")), GrassTile(), GrassTile()]
             ])
    ]

    # Adding portals to the cities
    timberhallow_city: City = cities[0]
    loststar_city: City = cities[1]
    mageborough_city: City = cities[2]
    coldpass_city: City = cities[3]
    whithollow_city: City = cities[4]

    timberhallow_city.get_tiles()[4][3].portal = Portal(Location(timberhallow_city, 3, 4),
                                                        Location(loststar_city, 3, 0))
    loststar_city.get_tiles()[0][3].portal = Portal(Location(loststar_city, 3, 0), Location(timberhallow_city, 3, 4))
    loststar_city.get_tiles()[4][3].portal = Portal(Location(loststar_city, 3, 4), Location(mageborough_city, 3, 0))
    mageborough_city.get_tiles()[0][3].portal = Portal(Location(mageborough_city, 3, 0), Location(loststar_city, 3, 4))
    mageborough_city.get_tiles()[4][3].portal = Portal(Location(mageborough_city, 3, 4), Location(coldpass_city, 3, 0))
    coldpass_city.get_tiles()[0][3].portal = Portal(Location(coldpass_city, 3, 0), Location(mageborough_city, 3, 4))
    coldpass_city.get_tiles()[4][3].portal = Portal(Location(coldpass_city, 3, 4), Location(whithollow_city, 3, 0))
    whithollow_city.get_tiles()[0][3].portal = Portal(Location(whithollow_city, 3, 0), Location(coldpass_city, 3, 4))

    # Creating a list of skills that all legendary creatures have.
    skills_list: list = [
        AttackSkill("ATTACK SKILL #1", "Normal Attack Skill", mpf("1e3"), mpf("3.5"), False),
        AttackSkill("ATTACK SKILL #2", "Strong Attack Skill", mpf("1e10"), mpf("10.5"), False),
        AttackSkill("ATTACK SKILL #3", "Ultimate Attack Skill", mpf("1e30"), mpf("31.5"), True),
        HealSkill("HEAL SKILL #1", "First Heal Skill", mpf("1e3"), mpf("2e4")),
        HealSkill("HEAL SKILL #2", "Better Heal Skill", mpf("1e10"), mpf("2e12")),
        HealSkill("HEAL SKILL #3", "Ultimate Heal Skill", mpf("1e30"), mpf("2e36")),
        WeakeningSkill("WEAKENING SKILL #1", "First Weakening Skill", mpf("1e3"), mpf("0.05"), mpf("0.05")),
        WeakeningSkill("WEAKENING SKILL #2", "Better Weakening Skill", mpf("1e10"), mpf("0.15"), mpf("0.15")),
        WeakeningSkill("WEAKENING SKILL #3", "Ultimate Weakening Skill", mpf("1e30"), mpf("0.45"), mpf("0.45")),
        StrengthenSkill("STRENGTHENING SKILL #1", "First Strengthening Skill", mpf("1e3"), mpf("0.05"), mpf("0.05")),
        StrengthenSkill("STRENGTHENING SKILL #2", "Better Strengthening Skill", mpf("1e10"), mpf("0.15"), mpf("0.15")),
        StrengthenSkill("STRENGTHENING SKILL #3", "Ultimate Strengthening Skill", mpf("1e30"), mpf("0.45"), mpf("0.45"))
    ]

    potential_legendary_creatures: list = [
        LegendaryCreature("Crondiff", "LAND", mpf("5e4"), mpf("4.75e4"), mpf("9e3"), mpf("8.8e3"), mpf("109"),
                          skills_list),
        LegendaryCreature("Grifngu", "WATER", mpf("4.85e4"), mpf("4.93e4"), mpf("9.5e3"), mpf("8.77e3"), mpf("112"),
                          skills_list),
        LegendaryCreature("Silechnou", "LAND", mpf("4.63e4"), mpf("5.12e4"), mpf("9.7e3"), mpf("8.9e3"), mpf("111"),
                          skills_list),
        LegendaryCreature("Icculsoz", "WATER", mpf("4.92e4"), mpf("5.08e4"), mpf("9.6e3"), mpf("9e3"), mpf("108"),
                          skills_list),
        LegendaryCreature("Ourezarm", "LAND", mpf("5.01e4"), mpf("4.96e4"), mpf("8.7e3"), mpf("9.2e3"), mpf("106"),
                          skills_list),
        LegendaryCreature("Braoclops", "WATER", mpf("4.75e4"), mpf("5.11e4"), mpf("9.36e3"), mpf("9e3"), mpf("114"),
                          skills_list),
        LegendaryCreature("Chielope", "LAND", mpf("4.9e4"), mpf("4.8e4"), mpf("9.45e3"), mpf("9.12e3"), mpf("115"),
                          skills_list),
        LegendaryCreature("Skaisena", "WATER", mpf("5.22e4"), mpf("5.12e4"), mpf("8.9e3"), mpf("9.4e3"), mpf("111"),
                          skills_list),
        LegendaryCreature("Weepe", "LAND", mpf("5.13e4"), mpf("5.07e4"), mpf("9.02e3"), mpf("8.86e3"), mpf("109"),
                          skills_list),
        LegendaryCreature("Skaucamx", "WATER", mpf("4.89e4"), mpf("4.96e4"), mpf("9.8e3"), mpf("9.5e3"), mpf("113"),
                          skills_list)
    ]

    # Initialising opponent trainers
    opponent_trainers: list = [
        CPUTrainer("CPU #1", Location(timberhallow_city, 0, 4), Team(potential_legendary_creatures[0:5])),
        CPUTrainer("CPU #2", Location(timberhallow_city, 0, 4), Team(potential_legendary_creatures[5:10])),
        CPUTrainer("CPU #3", Location(loststar_city, 0, 4), Team(potential_legendary_creatures[0:5])),
        CPUTrainer("CPU #4", Location(loststar_city, 0, 4), Team(potential_legendary_creatures[5:10])),
        CPUTrainer("CPU #5", Location(mageborough_city, 0, 4), Team(potential_legendary_creatures[0:5])),
        CPUTrainer("CPU #6", Location(mageborough_city, 0, 4), Team(potential_legendary_creatures[5:10])),
        CPUTrainer("CPU #7", Location(coldpass_city, 0, 4), Team(potential_legendary_creatures[0:5])),
        CPUTrainer("CPU #8", Location(coldpass_city, 0, 4), Team(potential_legendary_creatures[5:10])),
        CPUTrainer("CPU #9", Location(whithollow_city, 0, 4), Team(potential_legendary_creatures[0:5])),
        CPUTrainer("CPU #10", Location(whithollow_city, 0, 4), Team(potential_legendary_creatures[5:10]))
    ]

    # Automatically load saved game data
    file_name: str = "SAVED LEGENDARY CREATURE HUNTER AT MITHOTER PLANET GAME DATA"
    new_game: Game
    try:
        new_game = load_game_data(file_name)

        # Clearing up the command line window
        clear()

        print("Current game progress:\n", str(new_game))
    except FileNotFoundError:
        name: str = input("Please enter your name: ")
        player: Player = Player(name, Location(cities[0], 2, 2))
        new_game = Game(player, opponent_trainers, cities, potential_legendary_creatures)

    old_now = datetime.now()
    print("Enter 'Y' for yes.")
    print("Enter anything else for no.")
    continue_playing: str = input("Do you want to continue playing 'Legendary Creature Hunter at Mithoter Planet'? ")
    while continue_playing == "Y":
        # Clearing up the command line window
        clear()

        # Updating the old time and granting EXP to all the legendary creatures placed in training centers.
        new_now = datetime.now()
        time_difference = new_now - old_now
        seconds: int = time_difference.seconds
        old_now = new_now
        for city in new_game.get_cities():
            for row in range(city.CITY_HEIGHT):
                for col in range(city.CITY_WIDTH):
                    curr_location: Location = Location(city, col, row)
                    curr_tile: Tile = curr_location.get_tile()
                    if isinstance(curr_tile, TrainingCenterTile):
                        for legendary_creature in curr_tile.get_legendary_creatures_trained():
                            legendary_creature.exp += curr_tile.legendary_creature_exp_per_second * seconds
                            legendary_creature.level_up()

        # Asking the player what he/she wants to do inside the game.
        allowed: list = ["PLAY ADVENTURE MODE", "MANAGE BATTLE TEAM", "MANAGE LEGENDARY CREATURE INVENTORY",
                         "MANAGE ITEM INVENTORY", "GIVE ITEM", "PLACE RUNE", "REMOVE RUNE", "VIEW STATS"]
        print("Enter 'PLAY ADVENTURE MODE' to play adventure mode.")
        print("Enter 'MANAGE BATTLE TEAM' to manage your battle team.")
        print("Enter 'MANAGE LEGENDARY CREATURE INVENTORY' to manage your legendary creature inventory.")
        print("Enter 'MANAGE ITEM INVENTORY' to manage your item inventory.")
        print("Enter 'GIVE ITEM' to give an item to your legendary creatures.")
        print("Enter 'PLACE RUNE' to place a rune to a legendary creature you have.")
        print("Enter 'REMOVE RUNE' to remove a rune from a legendary creature you have.")
        print("Enter 'VIEW STATS' to view your stats.")
        print("Enter anything else to save game data and quit the game.")
        action: str = input("What do you want to do? ")
        if action not in allowed:
            # Saving game data and quitting the game
            save_game_data(new_game, file_name)
            sys.exit()
        else:
            if action == "VIEW STATS":
                # Clearing up the command line window
                clear()

                # Display player's stats
                print(str(new_game.player))

            elif action == "GIVE ITEM":
                # Clearing up the command line window
                clear()
                if len(new_game.player.item_inventory.get_items()) > 0:
                    if len(new_game.player.legendary_creature_inventory.get_legendary_creatures()) > 0:
                        print("Below is a list of legendary creatures you have.\n")
                        for legendary_creature in new_game.player.legendary_creature_inventory.get_legendary_creatures():
                            print(str(legendary_creature) + "\n")

                        legendary_creature_index: int = int(input("Please enter the index of the legendary creature "
                                                                  "you want to give items to: "))
                        while legendary_creature_index < 0 or legendary_creature_index >= \
                            len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                            legendary_creature_index = int(
                                input("Sorry, invalid input! Please enter the index of the legendary creature "
                                      "you want to give items to: "))

                        chosen_legendary_creature: LegendaryCreature = \
                            new_game.player.legendary_creature_inventory.get_legendary_creatures() \
                        [legendary_creature_index]
                        exp_shards: list = []  # initial value
                        for item in new_game.player.item_inventory.get_items():
                            if isinstance(item, EXPShard):
                                exp_shards.append(item)

                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        give_exp_shard: str = input("Do you want to give an EXP shard to this legendary creature? ")
                        if give_exp_shard == "Y" and len(exp_shards) > 0:
                            print("Below is a list of EXP shards you have.\n")
                            for exp_shard in exp_shards:
                                print(str(exp_shard) + "\n")

                            exp_shard_index: int = int(input("Please enter the index of the EXP shard you want to give: "))
                            while exp_shard_index < 0 or exp_shard_index >= len(exp_shards):
                                exp_shard_index = int(
                                    input("Sorry, invalid input! Please enter the index of the EXP shard you want to give: "))

                            chosen_exp_shard: EXPShard = exp_shards[exp_shard_index]
                            chosen_legendary_creature.exp += chosen_exp_shard.exp_granted
                            chosen_legendary_creature.level_up()
                            new_game.player.remove_item_from_inventory(chosen_exp_shard)

                        level_up_shards: list = []  # initial value
                        for item in new_game.player.item_inventory.get_items():
                            if isinstance(item, LevelUpShard):
                                level_up_shards.append(item)

                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        give_level_up_shard: str = input("Do you want to give a level up shard to this legendary creature? ")
                        if give_level_up_shard == "Y" and len(level_up_shards) > 0:
                            print("Below is a list of level up shards you have.\n")
                            for level_up_shard in level_up_shards:
                                print(str(level_up_shard) + "\n")

                            level_up_shard_index: int = int(input("Please enter the index of the level up shard you want to give: "))
                            while level_up_shard_index < 0 or level_up_shard_index >= len(level_up_shards):
                                level_up_shard_index = int(
                                    input("Sorry, invalid input! Please enter the index of the level up shard you want to give: "))

                            chosen_level_up_shard: LevelUpShard = level_up_shards[level_up_shard_index]
                            chosen_legendary_creature.exp = chosen_legendary_creature.required_exp
                            chosen_legendary_creature.level_up()
                            new_game.player.remove_item_from_inventory(chosen_level_up_shard)

                        skill_level_up_shards: list = []  # initial value
                        for item in new_game.player.item_inventory.get_items():
                            if isinstance(item, SkillLevelUpShard):
                                skill_level_up_shards.append(item)

                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        give_skill_level_up_shard: str = input(
                            "Do you want to give a skill level up shard to this legendary creature? ")
                        if give_skill_level_up_shard == "Y" and len(skill_level_up_shards) > 0:
                            chosen_skill_level_up_shard: SkillLevelUpShard = skill_level_up_shards[random.randint(0,
                                                                                len(skill_level_up_shards) - 1)]
                            skill_to_be_levelled_up: Skill = chosen_legendary_creature.get_skills()[random.randint(0, len(chosen_legendary_creature.get_skills()) - 1)]
                            skill_to_be_levelled_up.level_up()
                            new_game.player.remove_item_from_inventory(chosen_skill_level_up_shard)

                        evolution_candies: list = []  # initial value
                        for item in new_game.player.item_inventory.get_items():
                            if isinstance(item, EvolutionCandy):
                                evolution_candies.append(item)

                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        give_evolution_candy: str = input("Do you want to give an "
                                                          "evolution candy to this legendary craeture? ")
                        if give_evolution_candy == "Y" and len(evolution_candies) > 0:
                            chosen_evolution_candy: EvolutionCandy = evolution_candies[random.randint
                            (0, len(evolution_candies) - 1)]
                            if not chosen_legendary_creature.has_evolved:
                                chosen_legendary_creature.evolve()
                                new_game.player.remove_item_from_inventory(chosen_evolution_candy)

            elif action == "PLACE RUNE":
                # Clearing up the command line window
                clear()
                if len(new_game.player.legendary_creature_inventory.get_legendary_creatures()) > 0:
                    print("Below is a list of legendary creatures you have.\n")
                    for legendary_creature in new_game.player.legendary_creature_inventory.get_legendary_creatures():
                        print(str(legendary_creature) + "\n")

                    legendary_creature_index: int = int(input("Please enter the index of the legendary creature "
                                                              "you want to place a rune to: "))
                    while legendary_creature_index < 0 or legendary_creature_index >= \
                            len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                        legendary_creature_index = int(input("Sorry, invalid input! Please enter the index of the legendary creature "
                                                                  "you want to place a rune to: "))

                    chosen_legendary_creature: LegendaryCreature = \
                        new_game.player.legendary_creature_inventory.get_legendary_creatures() \
                            [legendary_creature_index]

                    runes: list = []  # initial value
                    for item in new_game.player.item_inventory.get_items():
                        if isinstance(item, Rune):
                            runes.append(item)

                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    place_rune: str = input("Do you want to place a rune to " + str(chosen_legendary_creature.name) + "? ")
                    if place_rune == "Y":
                        if len(runes) > 0:
                            print("Below is a list of runes you have.\n")
                            for rune in runes:
                                print(str(rune) + "\n")

                            rune_index: int = int(input("Please enter the index of the rune you want to place to "
                                                        "this legendary creature: "))
                            while rune_index < 0 or rune_index >= len(runes):
                                rune_index = int(input("Sorry, invalid input! Please enter the index of the rune you want to place to "
                                                            "this legendary creature: "))

                            chosen_rune: Rune = runes[rune_index]
                            chosen_legendary_creature.place_rune(chosen_rune)

            elif action == "REMOVE RUNE":
                # Clearing up the command line window
                clear()
                if len(new_game.player.legendary_creature_inventory.get_legendary_creatures()) > 0:
                    print("Below is a list of legendary creatures you have.\n")
                    for legendary_creature in new_game.player.legendary_creature_inventory.get_legendary_creatures():
                        print(str(legendary_creature) + "\n")

                    legendary_creature_index: int = int(input("Please enter the index of the legendary creature "
                                                              "you want to remove a rune from: "))
                    while legendary_creature_index < 0 or legendary_creature_index >= \
                            len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                        legendary_creature_index = int(input("Sorry, invalid input! Please enter the index of the legendary creature "
                                                              "you want to remove a rune from: "))

                    chosen_legendary_creature: LegendaryCreature = \
                        new_game.player.legendary_creature_inventory.get_legendary_creatures() \
                            [legendary_creature_index]

                    slot_number: int = int(input("Please enter the slot number of the rune you want to remove: "))
                    chosen_legendary_creature.remove_rune(slot_number)

            elif action == "MANAGE BATTLE TEAM":
                # Clearing up the command line window
                clear()
                if len(new_game.player.battle_team.get_legendary_creatures()) == 0:
                    print("Below is a list of legendary creatures in your battle team.\n")
                    for legendary_creature in new_game.player.battle_team.get_legendary_creatures():
                        print(str(legendary_creature) + "\n")

                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    remove_legendary_creature: str = input("Do you want to remove a legendary creature from "
                                                           "your team? ")
                    if remove_legendary_creature == "Y":
                        legendary_creature_index: int = int(input("Please enter the index of the legendary "
                                                                "creature you want to remove from your battle team: "))
                        while legendary_creature_index < 0 or legendary_creature_index >= \
                            len(new_game.player.battle_team.get_legendary_creatures()):
                            legendary_creature_index = int(input("Sorry, invalid input! Please enter the index "
                                            "of the legendary creature you want to remove from your battle team: "))

                        to_be_removed: LegendaryCreature = new_game.player.battle_team.get_legendary_creatures() \
                        [legendary_creature_index]
                        new_game.player.battle_team.remove_legendary_creature(to_be_removed)

                if len(new_game.player.battle_team.get_legendary_creatures()) < Team.MAX_LEGENDARY_CREATURES:
                    print("Below is a list of legendary creatures you have.\n")
                    for legendary_creature in new_game.player.legendary_creature_inventory.get_legendary_creatures():
                        print(str(legendary_creature) + "\n")

                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    add_legendary_creature: str = input("Do you want to add a legendary creature to your team? ")
                    if add_legendary_creature == "Y":
                        legendary_creature_index: int = int(input("Please enter the index of the legendary "
                                                        "creature you want to add to your battle team: "))
                        while legendary_creature_index < 0 or legendary_creature_index >= \
                            len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                            legendary_creature_index = int(input("Sorry, invalid input! Please enter the "
                                        "index of the legendary creature you want to add to your battle team: "))

                        to_be_added: LegendaryCreature = \
                            new_game.player.legendary_creature_inventory.get_legendary_creatures() \
                            [legendary_creature_index]
                        new_game.player.legendary_creature_inventory.add_legendary_creature(to_be_added)

            elif action == "MANAGE LEGENDARY CREATURE INVENTORY":
                # Clearing up the command line window
                clear()
                if len(new_game.player.legendary_creature_inventory.get_legendary_creatures()) > 0:
                    print("Below is a list of legendary creatures in your legendary creature inventory.\n")
                    for legendary_creature in new_game.player.legendary_creature_inventory.get_legendary_creatures():
                        print(str(legendary_creature) + "\n")

                    legendary_creature_index: int = int(input("Please enter the index of the legendary creature "
                                                              "you want to remove: "))
                    while legendary_creature_index < 0 or legendary_creature_index >= \
                        len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                        legendary_creature_index = int(input("Sorry, invalid input! Please enter the index of the legendary creature "
                                                                  "you want to remove: "))

                    to_be_removed: LegendaryCreature = new_game.player.legendary_creature_inventory.get_legendary_creatures()[legendary_creature_index]
                    new_game.player.legendary_creature_inventory.remove_legendary_creature(to_be_removed)

            elif action == "MANAGE ITEM INVENTORY":
                # Clearing up the command line window
                clear()
                if len(new_game.player.item_inventory.get_items()) > 0:
                    print("Below is a list of items in your item inventory.\n")
                    for item in new_game.player.item_inventory.get_items():
                        print(str(item) + "\n")

                    item_index: int = int(input("Please enter the index of the item you want to sell: "))
                    while item_index < 0 or item_index >= len(new_game.player.item_inventory.get_items()):
                        item_index = int(input("Sorry, invalid input! "
                                               "Please enter the index of the item you want to sell: "))

                    to_be_sold: Item = new_game.player.item_inventory.get_items()[item_index]
                    new_game.player.sell_item(to_be_sold)

            elif action == "PLAY ADVENTURE MODE":
                # Clearing up the command line window
                clear()

                print("You are at " + str(new_game.player.location.city.name) + " city.")
                print("Map of the city:\n" + str(new_game.player.location.city))

                print("Enter 'Y' for yes.")
                print("Enter anything else for no.")
                move: str = input("Do you want to move? ")
                if move == "Y":
                    print("Enter 'UP' to move up.")
                    print("Enter 'DOWN' to move down.")
                    print("Enter 'LEFT' to move left.")
                    print("Enter 'RIGHT' to move right.")
                    directions: list = ["UP", "DOWN", "LEFT", "RIGHT"]
                    direction: str = input("Where do you want to go? ")
                    while direction not in directions:
                        print("Enter 'UP' to move up.")
                        print("Enter 'DOWN' to move down.")
                        print("Enter 'LEFT' to move left.")
                        print("Enter 'RIGHT' to move right.")
                        direction = input("Sorry, invalid direction! Where do you want to go? ")

                    if direction == "UP":
                        if new_game.player.location.y > 0:
                            new_location: Location = Location(new_game.player.location.city,
                                                              new_game.player.location.x,
                                                              new_game.player.location.y - 1)
                            if not isinstance(new_location.get_tile(), WaterTile):
                                new_game.player.location.get_tile().remove_game_character(new_game.player)
                                new_location.get_tile().add_game_character(new_game.player)
                                new_game.player.location = new_location

                    elif direction == "DOWN":
                        if new_game.player.location.y < new_game.player.location.city.CITY_HEIGHT - 1:
                            new_location: Location = Location(new_game.player.location.city,
                                                              new_game.player.location.x,
                                                              new_game.player.location.y + 1)
                            if not isinstance(new_location.get_tile(), WaterTile):
                                new_game.player.location.get_tile().remove_game_character(new_game.player)
                                new_location.get_tile().add_game_character(new_game.player)
                                new_game.player.location = new_location

                    elif direction == "LEFT":
                        if new_game.player.location.x > 0:
                            new_location: Location = Location(new_game.player.location.city,
                                                              new_game.player.location.x - 1,
                                                              new_game.player.location.y)
                            if not isinstance(new_location.get_tile(), WaterTile):
                                new_game.player.location.get_tile().remove_game_character(new_game.player)
                                new_location.get_tile().add_game_character(new_game.player)
                                new_game.player.location = new_location

                    elif direction == "RIGHT":
                        if new_game.player.location.x < new_game.player.location.city.CITY_WIDTH - 1:
                            new_location: Location = Location(new_game.player.location.city,
                                                              new_game.player.location.x + 1,
                                                              new_game.player.location.y)
                            if not isinstance(new_location.get_tile(), WaterTile):
                                new_game.player.location.get_tile().remove_game_character(new_game.player)
                                new_location.get_tile().add_game_character(new_game.player)
                                new_game.player.location = new_location

                # Checking the destination tile
                if isinstance(new_game.player.location.get_tile().portal, Portal):
                    # Asking whether the player wants to enter the portal or not.
                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    enter_portal: str = input("Do you want to enter the portal? ")
                    if enter_portal == "Y":
                        new_game.player.enter_portal()

                elif isinstance(new_game.player.location.get_tile(), TrainingCenterTile):
                    training_center_tile: TrainingCenterTile = new_game.player.location.get_tile()

                    # Asking whether the player wants to place a legendary creature to the training center or not.
                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    place_legendary_creature: str = input("Do you want to place a legendary creature to "
                                                              "the training center? ")
                    if place_legendary_creature == "Y":
                        # Clearing up the command line window
                        clear()
                        # Printing a list of legendary creatures the player has.
                        print("Below is a list of legendary creatures you have.\n")
                        for curr_legendary_creature in \
                                new_game.player.legendary_creature_inventory.get_legendary_creatures():
                            print(str(curr_legendary_creature) + "\n")

                        legendary_creature_index: int = int(input("Please enter the index of the "
                                                                      "legendary creature you want to place: "))
                        while legendary_creature_index < 0 or legendary_creature_index >= \
                                len(new_game.player.legendary_creature_inventory.get_legendary_creatures()):
                            legendary_creature_index = int(input("Sorry, invalid input! Please enter the "
                                            "index of the legendary creature you want to place: "))

                        to_be_placed: LegendaryCreature = \
                            new_game.player.legendary_creature_inventory.get_legendary_creatures() \
                                [legendary_creature_index]
                        training_center_tile.add_legendary_creature(to_be_placed)

                    # Asking whether the player wants to take a legendary creature from the training center or not.
                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    take_legendary_creature: str = input("Do you want to take a legendary creature from "
                                                             "the training center? ")
                    if take_legendary_creature == "Y":
                        # Clearing up the command line window
                        clear()
                        # Printing a list of legendary creatures in the training center
                        print("Below is a list of legendary creatures in the training center.\n")
                        for legendary_creature in training_center_tile.get_legendary_creatures_trained():
                            print(str(legendary_creature) + "\n")

                        legendary_creature_index: int = int(input("Please enter the index of the "
                                                                      "legendary creature you want to take: "))
                        while legendary_creature_index < 0 or legendary_creature_index >= \
                                len(training_center_tile.get_legendary_creatures_trained()):
                            legendary_creature_index = int(input("Sorry, invalid input! "
                                        "Please enter the index of the legendary creature you want to take: "))

                        to_be_taken: LegendaryCreature = training_center_tile.get_legendary_creatures_trained() \
                            [legendary_creature_index]
                        training_center_tile.remove_legendary_creature(to_be_taken)

                elif isinstance(new_game.player.location.get_tile(), SandTile):
                    pass  # do nothing

                elif isinstance(new_game.player.location.get_tile(), ShopTile):
                    shop_tile: ShopTile = new_game.player.location.get_tile()
                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    buy_item: str = input("Do you want to buy an item from the shop? ")
                    if buy_item == "Y":
                        # Clearing up the command line window
                        clear()
                        print("Below is a list of items sold in this shop.\n")
                        for item in shop_tile.get_items_sold():
                            print(str(item) + "\n")

                        item_index: int = int(input("Please enter the index of the item you want to buy: "))
                        while item_index < 0 or item_index >= len(shop_tile.get_items_sold()):
                            item_index = int(input("Sorry, invalid input! "
                                                    "Please enter the index of the item you want to buy: "))

                        to_buy: Item = shop_tile.get_items_sold()[item_index]
                        if new_game.player.purchase_item(to_buy):
                            print("Congratulations! You have successfully bought " + str(to_buy.name))
                        else:
                            print("Sorry, insufficient coins!")

                elif isinstance(new_game.player.location.get_tile(), GrassTile):
                    # Determining whether the player encounters a wild battle or not
                    encounter_wild_battle: bool = random.random() <= 0.5
                    if encounter_wild_battle:
                        # Clearing up the command line window
                        clear()
                        wild_legendary_creature: LegendaryCreature = \
                            new_game.get_potential_legendary_creatures()[random.randint(0,
                                len(new_game.get_potential_legendary_creatures()) - 1)]
                        print("A wild " + str(wild_legendary_creature.name) + " appears!")

                        # Start a wild battle
                        wild_battle: WildBattle = WildBattle(new_game.player.battle_team, wild_legendary_creature)
                        flee: bool = False
                        while wild_battle.winner is None and not flee and not \
                                wild_battle.wild_legendary_creature_caught:
                            # Printing out the stats of legendary creatures in both teams
                            print("Below are the stats of all legendary creatures in player's team.\n")
                            for legendary_creature in wild_battle.team1.get_legendary_creatures():
                                print(str(legendary_creature) + "\n")

                            print("Below are the stats of all legendary creatures in enemy's team.\n")
                            for legendary_creature in wild_battle.team2.get_legendary_creatures():
                                print(str(legendary_creature) + "\n")

                            # Make a legendary creature move.
                            wild_battle.get_someone_to_move()

                            # Checking which legendary creature moves
                            if wild_battle.whose_turn in new_game.player.battle_team.get_legendary_creatures():
                                # Asking the player what he/she wants to do
                                print("Enter 'CATCH WILD LEGENDARY CREATURE' to catch the wild legendary creature.")
                                print("Enter 'NORMAL ATTACK' for normal attack.")
                                print("Enter 'NORMAL HEAL' for normal heal.")
                                print("Enter 'USE SKILL' to use a skill.")
                                print("Enter anything else to flee.")
                                possible_actions: list = ["CATCH WILD LEGENDARY CREATURE", "NORMAL ATTACK",
                                                            "NORMAL HEAL", "USE SKILL"]
                                wild_battle_action: str = input("What do you want to do? ")
                                if wild_battle_action not in possible_actions:
                                    flee = True  # the player flees from the battle

                                if wild_battle_action == "CATCH WILD LEGENDARY CREATURE":
                                    balls_list: list = [item for item in
                                                        new_game.player.item_inventory.get_items()
                                                        if isinstance(item, Ball)]
                                    print("Below is a list of balls you have.\n")
                                    for ball in balls_list:
                                        print(str(ball) + "\n")

                                    ball_index: int = int(input("Please enter the index of the ball you "
                                                                "want to use: "))
                                    while ball_index < 0 or ball_index >= len(balls_list):
                                        ball_index = int(input("Sorry, invalid input! Please enter the index of "
                                                                "the ball you want to use: "))

                                    chosen_ball: Ball = balls_list[ball_index]
                                    if new_game.player.catch_legendary_creature(wild_legendary_creature,
                                                                                chosen_ball):
                                        wild_battle.wild_legendary_creature_caught = True

                                elif wild_battle_action == "NORMAL ATTACK":
                                    moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                    moving_legendary_creature.normal_attack(wild_legendary_creature)

                                elif wild_battle_action == "NORMAL HEAL":
                                    moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                    moving_legendary_creature.normal_heal(moving_legendary_creature)

                                elif wild_battle_action == "USE SKILL":
                                    # Checking whether there are usable skills or not
                                    usable_skills: list = []  # initial value
                                    for skill in wild_battle.whose_turn.get_skills():
                                        if wild_battle.whose_turn.curr_magic_points >= skill.magic_points_cost:
                                            usable_skills.append(skill)

                                    if len(usable_skills) > 0:
                                        print("Below is a list of skills you can use.\n")
                                        for skill in usable_skills:
                                            print(str(skill) + "\n")

                                        skill_index: int = int(input("Please enter the index of the skill you "
                                                                        "want to use: "))
                                        while skill_index < 0 or skill_index >= len(usable_skills):
                                            skill_index = int(input("Sorry, invalid input! Please enter the index "
                                                                    "of the skill you want to use: "))

                                        skill_to_use: Skill = usable_skills[skill_index]
                                        if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use,
                                                                                               WeakeningSkill):
                                            moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                            moving_legendary_creature.use_skill(wild_legendary_creature, skill_to_use)
                                        else:
                                            moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                            moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)
                                    else:
                                        # Normal attack is carried out instead
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        moving_legendary_creature.normal_attack(wild_legendary_creature)

                            else:
                                chance: float = random.random()
                                if chance <= 1/3:
                                    moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                    target: LegendaryCreature = \
                                        new_game.player.battle_team.get_legendary_creatures() \
                                    [random.randint(0, len(new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                    moving_legendary_creature.normal_attack(target)
                                elif 1/3 < chance <= 2/3:
                                    moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                    moving_legendary_creature.normal_heal(moving_legendary_creature)
                                else:
                                    skill_to_use: Skill = wild_legendary_creature.get_skills() \
                                        [random.randint(0, len(wild_legendary_creature.get_skills()) - 1)]
                                    if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use,
                                                                                           WeakeningSkill):
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        target: LegendaryCreature = \
                                            new_game.player.battle_team.get_legendary_creatures() \
                                                [random.randint(0, len(
                                                new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                        moving_legendary_creature.use_skill(target, skill_to_use)
                                    else:
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)

                            # Recovering magic points
                            wild_battle.whose_turn.recover_magic_points()

                        if wild_battle.winner == new_game.player.battle_team:
                            print("Congratulations! You won the battle!")
                            new_game.player.coins += wild_battle.reward.player_coin_gain
                            new_game.player.exp += wild_battle.reward.player_exp_gain
                            new_game.player.level_up()
                            for legendary_creature in new_game.player.battle_team.get_legendary_creatures():
                                legendary_creature.exp += wild_battle.reward.legendary_creature_exp_gain
                                legendary_creature.level_up()
                        elif wild_battle.winner == wild_battle.team2:
                            print("You lost the battle")
                        else:
                            if wild_battle.wild_legendary_creature_caught:
                                print("You have successfully caught " + str(wild_legendary_creature.name))
                            elif flee:
                                print("You successfully fled!")
                            else:
                                pass  # Do nothing

                        for legendary_creature in wild_battle.team1.get_legendary_creatures():
                            legendary_creature.restore()

                        for legendary_creature in wild_battle.team2.get_legendary_creatures():
                            legendary_creature.restore()

                else:
                    pass  # Do nothing

                # Checking whether the player is near a water tile or not
                near_water_tile: bool = False  # initial value
                above: Location = Location(new_game.player.location.city,
                                           new_game.player.location.x, new_game.player.location.y - 1)
                below: Location = Location(new_game.player.location.city,
                                           new_game.player.location.x, new_game.player.location.y + 1)
                left: Location = Location(new_game.player.location.city,
                                           new_game.player.location.x - 1, new_game.player.location.y)
                right: Location = Location(new_game.player.location.city,
                                          new_game.player.location.x + 1, new_game.player.location.y)
                if isinstance(above, WaterTile) or isinstance(below, WaterTile) or isinstance(left, WaterTile) \
                        or isinstance(right, WaterTile):
                    near_water_tile = True

                if near_water_tile:
                    # Checking whether the player has a fishing rod or not
                    fishing_rods: list = []  # initial value
                    for item in new_game.player.item_inventory.get_items():
                        if isinstance(item, FishingRod):
                            fishing_rods.append(item)

                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    go_fishing: str = input("Do you want to go fishing? ")
                    if go_fishing == "Y":
                        # Clearing up the command line window
                        clear()
                        fishing_rod_index: int = int(input("Please enter the index of the fishing rod you want to "
                                                           "use: "))
                        while fishing_rod_index < 0 or fishing_rod_index >= len(fishing_rods):
                            fishing_rod_index = int(input("Sorry, invalid input! "
                                                        "Please enter the index of the fishing rod you want to use: "))

                        chosen_fishing_rod: FishingRod = fishing_rods[fishing_rod_index]
                        encounter_wild_battle: bool = random.random() <= \
                                                      chosen_fishing_rod.encounter_legendary_creature_chance
                        if encounter_wild_battle:
                            potential_legendary_creatures: list = []  # initial value
                            for legendary_creature in potential_legendary_creatures:
                                if legendary_creature.creature_type == "WATER":
                                    potential_legendary_creatures.append(legendary_creature)

                            wild_legendary_creature: LegendaryCreature = potential_legendary_creatures \
                                [random.randint(0, len(potential_legendary_creatures) - 1)]

                            print("A wild " + str(wild_legendary_creature.name) + " appears!")

                            # Start a wild battle
                            wild_battle: WildBattle = WildBattle(new_game.player.battle_team, wild_legendary_creature)
                            flee: bool = False
                            while wild_battle.winner is None and not flee and not \
                                    wild_battle.wild_legendary_creature_caught:
                                # Printing out the stats of legendary creatures in both teams
                                print("Below are the stats of all legendary creatures in player's team.\n")
                                for legendary_creature in wild_battle.team1.get_legendary_creatures():
                                    print(str(legendary_creature) + "\n")

                                print("Below are the stats of all legendary creatures in enemy's team.\n")
                                for legendary_creature in wild_battle.team2.get_legendary_creatures():
                                    print(str(legendary_creature) + "\n")

                                # Make a legendary creature move.
                                wild_battle.get_someone_to_move()

                                # Checking which legendary creature moves
                                if wild_battle.whose_turn in new_game.player.battle_team.get_legendary_creatures():
                                    # Asking the player what he/she wants to do
                                    print("Enter 'CATCH WILD LEGENDARY CREATURE' to catch the wild legendary creature.")
                                    print("Enter 'NORMAL ATTACK' for normal attack.")
                                    print("Enter 'NORMAL HEAL' for normal heal.")
                                    print("Enter 'USE SKILL' to use a skill.")
                                    print("Enter anything else to flee.")
                                    possible_actions: list = ["CATCH WILD LEGENDARY CREATURE", "NORMAL ATTACK",
                                                              "NORMAL HEAL", "USE SKILL"]
                                    wild_battle_action: str = input("What do you want to do? ")
                                    if wild_battle_action not in possible_actions:
                                        flee = True  # the player flees from the battle

                                    if wild_battle_action == "CATCH WILD LEGENDARY CREATURE":
                                        balls_list: list = [item for item in
                                                            new_game.player.item_inventory.get_items()
                                                            if isinstance(item, Ball)]
                                        print("Below is a list of balls you have.\n")
                                        for ball in balls_list:
                                            print(str(ball) + "\n")

                                        ball_index: int = int(input("Please enter the index of the ball you "
                                                                    "want to use: "))
                                        while ball_index < 0 or ball_index >= len(balls_list):
                                            ball_index = int(input("Sorry, invalid input! Please enter the index of "
                                                                   "the ball you want to use: "))

                                        chosen_ball: Ball = balls_list[ball_index]
                                        if new_game.player.catch_legendary_creature(wild_legendary_creature,
                                                                                    chosen_ball):
                                            wild_battle.wild_legendary_creature_caught = True

                                    elif wild_battle_action == "NORMAL ATTACK":
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        moving_legendary_creature.normal_attack(wild_legendary_creature)

                                    elif wild_battle_action == "NORMAL HEAL":
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        moving_legendary_creature.normal_heal(moving_legendary_creature)

                                    elif wild_battle_action == "USE SKILL":
                                        # Checking whether there are usable skills or not
                                        usable_skills: list = []  # initial value
                                        for skill in wild_battle.whose_turn.get_skills():
                                            if wild_battle.whose_turn.curr_magic_points >= skill.magic_points_cost:
                                                usable_skills.append(skill)

                                        if len(usable_skills) > 0:
                                            print("Below is a list of skills you can use.\n")
                                            for skill in usable_skills:
                                                print(str(skill) + "\n")

                                            skill_index: int = int(input("Please enter the index of the skill you "
                                                                         "want to use: "))
                                            while skill_index < 0 or skill_index >= len(usable_skills):
                                                skill_index = int(input("Sorry, invalid input! Please enter the index "
                                                                        "of the skill you want to use: "))

                                            skill_to_use: Skill = usable_skills[skill_index]
                                            if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use,
                                                                                                   WeakeningSkill):
                                                moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                                moving_legendary_creature.use_skill(wild_legendary_creature, skill_to_use)
                                            else:
                                                moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                                moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)
                                        else:
                                            # Normal attack is carried out instead
                                            moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                            moving_legendary_creature.normal_attack(wild_legendary_creature)

                                else:
                                    chance: float = random.random()
                                    if chance <= 1 / 3:
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        target: LegendaryCreature = \
                                            new_game.player.battle_team.get_legendary_creatures() \
                                                [random.randint(0, len(
                                                new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                        moving_legendary_creature.normal_attack(target)
                                    elif 1 / 3 < chance <= 2 / 3:
                                        moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                        moving_legendary_creature.normal_heal(moving_legendary_creature)
                                    else:
                                        skill_to_use: Skill = wild_legendary_creature.get_skills() \
                                            [random.randint(0, len(wild_legendary_creature.get_skills()) - 1)]
                                        if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use, WeakeningSkill):
                                            moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                            target: LegendaryCreature = \
                                                new_game.player.battle_team.get_legendary_creatures() \
                                                    [random.randint(0, len(
                                                    new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                            moving_legendary_creature.use_skill(target, skill_to_use)
                                        else:
                                            moving_legendary_creature: LegendaryCreature = wild_battle.whose_turn
                                            moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)

                                # Recovering magic points
                                wild_battle.whose_turn.recover_magic_points()

                            if wild_battle.winner == new_game.player.battle_team:
                                print("Congratulations! You won the battle!")
                                new_game.player.coins += wild_battle.reward.player_coin_gain
                                new_game.player.exp += wild_battle.reward.player_exp_gain
                                new_game.player.level_up()
                                for legendary_creature in new_game.player.battle_team.get_legendary_creatures():
                                    legendary_creature.exp += wild_battle.reward.legendary_creature_exp_gain
                                    legendary_creature.level_up()
                            elif wild_battle.winner == wild_battle.team2:
                                print("You lost the battle")
                            else:
                                if wild_battle.wild_legendary_creature_caught:
                                    print("You have successfully caught " + str(wild_legendary_creature.name))
                                elif flee:
                                    print("You successfully fled!")
                                else:
                                    pass  # Do nothing

                            for legendary_creature in wild_battle.team1.get_legendary_creatures():
                                legendary_creature.restore()

                            for legendary_creature in wild_battle.team2.get_legendary_creatures():
                                legendary_creature.restore()

                # Checking whether the player is at the same tile as an NPC or not.
                curr_player_tile: Tile = new_game.player.location.get_tile()
                npcs: list = []  # initial value
                for game_character in curr_player_tile.get_game_characters():
                    if isinstance(game_character, NPC):
                        npcs.append(game_character)

                for npc in npcs:
                    print(new_game.player.interact_with_npc(npc))

                # Checking whether the player is at the same tile as another trainer or not.
                player_tile: Tile = new_game.player.location.get_tile()
                other_trainers: list = []  # initial value
                for game_character in player_tile.get_game_characters():
                    if isinstance(game_character, Trainer) and game_character != new_game.player:
                        other_trainers.append(game_character)

                if len(other_trainers) > 0:
                    encounter_trainer_battle: bool = random.random() <= 0.5
                    if encounter_trainer_battle:
                        # Clearing up the command line window
                        clear()
                        chosen_trainer: CPUTrainer = other_trainers[random.randint(0, len(other_trainers) - 1)]
                        print("A battle between " + str(new_game.player.name) + " and " +
                              str(chosen_trainer.name) + " starts!")
                        trainer_battle: TrainerBattle = TrainerBattle(new_game.player.battle_team,
                                                                      chosen_trainer.battle_team)
                        while trainer_battle.winner is not None:
                            # Printing out the stats of legendary creatures in both teams
                            print("Below are the stats of all legendary creatures in player's team.\n")
                            for legendary_creature in trainer_battle.team1.get_legendary_creatures():
                                print(str(legendary_creature) + "\n")

                            print("Below are the stats of all legendary creatures in enemy's team.\n")
                            for legendary_creature in trainer_battle.team2.get_legendary_creatures():
                                print(str(legendary_creature) + "\n")

                            # Make a legendary creature move
                            trainer_battle.get_someone_to_move()

                            # Checking which legendary creature moves
                            if trainer_battle.whose_turn in trainer_battle.team1.get_legendary_creatures():
                                # Asking the player what he/she wants to do
                                print("Enter 'NORMAL ATTACK' for normal attack.")
                                print("Enter 'NORMAL HEAL' for normal heal.")
                                print("Enter anything else to use a skill.")
                                possible_actions: list = ["NORMAL ATTACK", "NORMAL HEAL"]
                                trainer_battle_action: str = input("What do you want to do? ")
                                if trainer_battle_action not in possible_actions:
                                    # Checking whether there are usable skills or not
                                    usable_skills: list = []  # initial value
                                    for skill in trainer_battle.whose_turn.get_skills():
                                        if trainer_battle.whose_turn.curr_magic_points >= skill.magic_points_cost:
                                            usable_skills.append(skill)

                                    if len(usable_skills) > 0:
                                        print("Below is a list of skills you can use.\n")
                                        for skill in usable_skills:
                                            print(str(skill) + "\n")

                                        skill_index: int = int(input("Please enter the index of the skill you "
                                                                     "want to use: "))
                                        while skill_index < 0 or skill_index >= len(usable_skills):
                                            skill_index = int(input("Sorry, invalid input! Please enter the index "
                                                                    "of the skill you want to use: "))

                                        skill_to_use: Skill = usable_skills[skill_index]
                                        if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use,
                                                                                               WeakeningSkill):
                                            print("Below is a list of legendary creatures in your enemy's team.\n")
                                            for legendary_creature in trainer_battle.team2.get_legendary_creatures():
                                                print(str(legendary_creature) + "\n")

                                            target_index: int = int(input("Please enter the index of the "
                                                    "legendary creature you want to use as the target of your skill:"))
                                            while target_index < 0 or target_index >= \
                                                len(trainer_battle.team2.get_legendary_creatures()):
                                                target_index = int(input("Sorry, invalid input! Please enter the index of the "
                                                    "legendary creature you want to use as the target of your skill:"))

                                            moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                            target: LegendaryCreature = trainer_battle.team2.get_legendary_creatures() \
                                                [target_index]
                                            moving_legendary_creature.use_skill(target, skill_to_use)
                                        else:
                                            moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                            moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)
                                    else:
                                        # Normal attack is carried out instead
                                        print("Below is a list of legendary creatures in your enemy's team.\n")
                                        for legendary_creature in trainer_battle.team2.get_legendary_creatures():
                                            print(str(legendary_creature) + "\n")

                                        target_index: int = int(input("Please enter the index of the "
                                                                      "legendary creature you want to use as the target of your skill:"))
                                        while target_index < 0 or target_index >= \
                                                len(trainer_battle.team2.get_legendary_creatures()):
                                            target_index = int(
                                                input("Sorry, invalid input! Please enter the index of the "
                                                      "legendary creature you want to use as the target of your skill:"))

                                        target: LegendaryCreature = trainer_battle.team2.get_legendary_creatures() \
                                            [target_index]
                                        moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                        moving_legendary_creature.normal_attack(target)

                                elif trainer_battle_action == "NORMAL ATTACK":
                                    print("Below is a list of legendary creatures in your enemy's team.\n")
                                    for legendary_creature in trainer_battle.team2.get_legendary_creatures():
                                        print(str(legendary_creature) + "\n")

                                    target_index: int = int(input("Please enter the index of the "
                                                                  "legendary creature you want to use as the target of your skill:"))
                                    while target_index < 0 or target_index >= \
                                            len(trainer_battle.team2.get_legendary_creatures()):
                                        target_index = int(
                                            input("Sorry, invalid input! Please enter the index of the "
                                                  "legendary creature you want to use as the target of your skill:"))

                                    moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                    target: LegendaryCreature = trainer_battle.team2.get_legendary_creatures() \
                                        [target_index]
                                    moving_legendary_creature.normal_attack(target)
                                elif trainer_battle_action == "NORMAL HEAL":
                                    moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                    moving_legendary_creature.normal_heal(moving_legendary_creature)
                                else:
                                    pass  # Do nothing

                            elif trainer_battle.whose_turn in trainer_battle.team2.get_legendary_creatures():
                                chance: float = random.random()
                                if chance <= 1 / 3:
                                    moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                    target: LegendaryCreature = \
                                        new_game.player.battle_team.get_legendary_creatures() \
                                            [random.randint(0, len(
                                            new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                    moving_legendary_creature.normal_attack(target)
                                elif 1 / 3 < chance <= 2 / 3:
                                    moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                    moving_legendary_creature.normal_heal(moving_legendary_creature)
                                else:
                                    skill_to_use: Skill = trainer_battle.whose_turn.get_skills() \
                                        [random.randint(0, len(trainer_battle.whose_turn.get_skills()) - 1)]
                                    if isinstance(skill_to_use, AttackSkill) or isinstance(skill_to_use,
                                                                                           WeakeningSkill):
                                        moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                        target: LegendaryCreature = \
                                            new_game.player.battle_team.get_legendary_creatures() \
                                                [random.randint(0, len(
                                                new_game.player.battle_team.get_legendary_creatures()) - 1)]
                                        moving_legendary_creature.use_skill(target, skill_to_use)
                                    else:
                                        moving_legendary_creature: LegendaryCreature = trainer_battle.whose_turn
                                        moving_legendary_creature.use_skill(moving_legendary_creature, skill_to_use)

                            # Recovering magic points
                            trainer_battle.whose_turn.recover_magic_points()

                        if trainer_battle.winner == new_game.player.battle_team:
                            print("Congratulations! You won the battle!")
                            new_game.player.coins += trainer_battle.reward.player_coin_gain
                            new_game.player.exp += trainer_battle.reward.player_exp_gain
                            new_game.player.level_up()
                            for legendary_creature in new_game.player.battle_team.get_legendary_creatures():
                                legendary_creature.exp += trainer_battle.reward.legendary_creature_exp_gain
                                legendary_creature.level_up()

                            chosen_trainer.get_beaten()
                        elif trainer_battle.winner == trainer_battle.team2:
                            print("You lost the battle")

                        for legendary_creature in trainer_battle.team1.get_legendary_creatures():
                            legendary_creature.restore()

                        for legendary_creature in trainer_battle.team2.get_legendary_creatures():
                            legendary_creature.restore()

            else:
                pass  # Do nothing

        print("Enter 'Y' for yes.")
        print("Enter anything else for no.")
        continue_playing = input("Do you want to continue playing 'Legendary Creature Hunter at Mithoter Planet'? ")

    # Saving game data and quitting the game
    save_game_data(new_game, file_name)
    sys.exit()


if __name__ == '__main__':
    main()
