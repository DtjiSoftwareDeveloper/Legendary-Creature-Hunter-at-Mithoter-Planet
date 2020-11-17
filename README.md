# Legendary-Creature-Hunter-at-Mithoter-Planet
"Legendary Creature Hunter at Mithoter Planet" is a turn based strategy RPG like Pokemon 
(https://en.wikipedia.org/wiki/Pok%C3%A9mon_(video_game_series)) which involves legendary creatures instead of Pokemon where 
the player will battle against other trainers around Mithoter planet and also go around the planet to catch legendary creatures. 
This game runs on command line interface, is offline, and allows single player mode only.

### Executable File

The executable file "legendary_creature_hunter_at_mithoter_planet.exe" is used to run the game application. It is downloadable
from https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/executable/legendary_creature_hunter_at_mithoter_planet.exe.

### Source Code

Python code used to create the game application is available in 
https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/code/legendary_creature_hunter_at_mithoter_planet.py.

### Getting Started

Once you run the application, you will either be asked to enter your name if no saved data exists in the same folder as where you put the executable file
"legendary_creature_hunter_at_mithoter_planet.exe". Else, you will be immediately asked whether you want to continue playing the game or not. Entering 'Y' 
will clear the command line window and make you asked what you want to do next. Entering anything else will make you save and quit the game. Saved game 
data is saved into the file named "SAVED LEGENDARY CREATURE HUNTER AT MITHOTER PLANET GAME DATA".

Below shows the case when you run the application with no existing saved game data.

![Getting Started 1](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/Getting%20Started%201.png)

Below shows the case when you run the application with existing saved data.

![Getting Started 2](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/Getting%20Started%202.png)

### Select Action

You can choose whether you want to play adventure mode, manage your battle team, manage your legendary creature inventory, manage your item inventory, 
give an item to any of your legendary creatures, place a rune on any of your legendary creatures, remove a rune from any of your legendary creatures, 
or view your stats.

![Select Action](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/Select%20Action.png)

### Playing Adventure Mode

Once you decided to play adventure mode, you will be shown your location and the current representation of the city where you are currently at. You will also 
be asked whether you want to move or not. If you want to move, you will be asked which direction you want to move to and your location will become the destination 
tile's location. Else, you will remain at the same tile.

![Adventure Mode 1](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/Adventure%20Mode%201.png)

The game will then check the type of tile you are at after moving/staying. If there are other trainers in the tile, you might have a trainer battle with one of the
trainers. If you land on a grass tile, you might have a wild battle with a wild legendary creature which you can either catch it, battle against it, or flee from it.
Landing on a training center tile will make you asked whether you want to place any of your legendary creatures in the training center or not. Also, if there are
legendary creatures placed in the training center, you will be asked whether you want to take one of them or not. If there is a portal in the tile, you will be asked
whether you want to enter the portal or just stay on the tile. Landing on a shop tile will make you asked whether you want to buy an item from the shop or not and
if you want to, you will need to enter the index of the item you want to buy and the purchase will be successful if you have sufficient coins. If you land on a sand tile,
nothing happens.

Next, the game will check the tiles next to the tile you are at. You can go fishing if you are next to a water tile. Also, if you successfully 
encounter a wild legendary creature when fishing, a wild battle with same fashion as on grass tiles will happen.

The screenshot below shows what happens after the player decided to move to the left of the tile the player was at in the previous screenshot.

![Adventure Mode 2](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/Adventure%20Mode%202.png)

### Managing Battle Team

You can discard a legendary creature from your battle team or add a legendary creature from your legendary creature inventory to your battle team if you decide
to manage your battle team.

### Managing Legendary Creature Inventory

You will be shown a list of legendary creatures you have if you choose to manage your legendary creature inventory. If you have, you can remove a legendary 
creature from your legendary creature inventory if you want to.

### Managing Item Inventory

You will be shown a list of items you have if you choose to manage your item inventory. If you have, you can sell an item from your item inventory if you want to.
Besides, if you have runes in your item inventory, you can level up a rune.

### Give Item

You will be shown a list of items you have for each type (i.e. EXP shard, level up shard, evolution candy, and skill level up shard) which you can give to your 
legendary creatures. EXP shard adds EXP of a legendary creature which might help with levelling it up. A level up shard automatically levels up a legendary creature.
An evolution candy immediately evolves a legendary creature. A skill level up will randomly choose a skill from a chosen legendary creature where that skill is to be
levelled up.

### Place Rune

If you have runes in your item inventory, you can place a rune on any of your legendary creatures. Runes strengthen legendary creatures.

### Remove Rune

If you have legendary creatures in your legendary creature inventory, you can remove a rune from any of the legendary creatures there.

### Viewing Your Stats

Below shows a cropped view of how your stats look like if you want to view them.

![View Stats](https://github.com/DtjiSoftwareDeveloper/Legendary-Creature-Hunter-at-Mithoter-Planet/blob/main/images/View%20Stats.png)
