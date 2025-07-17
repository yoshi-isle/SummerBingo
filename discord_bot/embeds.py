from datetime import datetime, timedelta, timezone
from constants import Emojis
import discord
from constants import WORLD_NAMES
from dateutil import parser
import os

def build_team_board_embed(team_data, tile_info, team_level_string, ranking=None):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    # The image should be set by the caller using set_image(url="attachment://team_board.png")
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your tile completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{Emojis.WORLD_MAP} {WORLD_NAMES[team_data['current_world']]} {team_level_string}",
        value=f"{tile_info['tile_name']} ([Wiki]({tile_info['wiki_url']}))\n*{tile_info['description']}*",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.SUBMISSIONS} Submissions Remaining",
        value=f"{team_data['completion_counter']}",
        inline=True
    )
    rank_texts = {
        1: "1st Place",
        2: "2nd Place",
        3: "3rd Place",
        4: "4th Place",
        5: "5th Place",
        6: "6th Place",
    }
    embed.add_field(
        name=f"{Emojis.TROPHY} Ranking",
        value=rank_texts.get(ranking, "Unknown"),
        inline=True
    )

    hours_map = {
        1: 999,
        2: 16,
        3: 16,
        4: 16,
        5: 12,
        6: 12,
    }

    last_rolled_at = parser.parse(team_data['last_rolled_at'])
    next_allowed_time = last_rolled_at + timedelta(hours=hours_map[ranking])
    discord_epoch_relative = int(next_allowed_time.timestamp())

    hours_text_based_on_placement = {
        1: "You cannot skip the tile in 1st place.",
        2: f"You cannot skip the tile until <t:{discord_epoch_relative}:R>.",
        3: f"You cannot skip the tile until <t:{discord_epoch_relative}:R>.",
        4: f"You cannot skip the tile until <t:{discord_epoch_relative}:R>.",
        5: f"You cannot skip the tile until <t:{discord_epoch_relative}:R>.",
        6: f"You cannot skip the tile until <t:{discord_epoch_relative}:R>.",
    }

    can_skip = next_allowed_time < datetime.now(timezone.utc)

    embed.add_field(
        name=f"{Emojis.SKIP} Skip",
        value=hours_text_based_on_placement[ranking]
            if not can_skip else "Your team can skip this tile now!",
        inline=False
    )
    return embed

def build_w1_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion. There will be multiple selections.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{Emojis.TRIAL_COMPLETE} {key_tile_names[team_data['current_world']]}",
        value="Complete 3 out of 5 trials to unlock the boss key!",
        inline=False
    )

    trial_count = 0
    for counter in [team_data["w1key1_completion_counter"], 
                    team_data["w1key2_completion_counter"],
                    team_data["w1key3_completion_counter"],
                    team_data["w1key4_completion_counter"],
                    team_data["w1key5_completion_counter"]]:
        trial_count += counter == 0

    embed.add_field(
        name=f"{Emojis.TRIAL_W1_1} Trial 1: 2x Scrolls or Twisted Kits from CoX",
        value=f"`{format_submission(team_data['w1key1_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_2} Trial 2: Crystal Tool Seed",
        value=f"`{format_submission(team_data['w1key2_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_3} Trial 3: 4x Burning Claws or Synapses",
        value=f"`{format_submission(team_data['w1key3_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_4} Trial 4: Bryophyta's Essence OR Hill Giant Club",
        value=f"`{format_submission(team_data['w1key4_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_5} Trial 5: 10x Elite Clues from BA High Gambles",
        value=f"`{format_submission(team_data['w1key5_completion_counter'])}`",
        inline=False
    )

    # Show 5 emojis: KEY if obtained (counter == 0), KEY_NOT_OBTAINED otherwise
    key_emojis = []
    for counter in [
        team_data["w1key1_completion_counter"],
        team_data["w1key2_completion_counter"],
        team_data["w1key3_completion_counter"],
        team_data["w1key4_completion_counter"],
        team_data["w1key5_completion_counter"]
    ]:
        if counter <= 0:
            key_emojis.append(Emojis.TRIAL_COMPLETE)
        else:
            key_emojis.append(Emojis.TRIAL_INCOMPLETE)
    embed.add_field(
        name="",
        value=" ".join(key_emojis),
        inline=False
    )
    return embed

def build_w1_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name=f"{Emojis.OLMLET} 1-B: Showdown at the Summit",
        value=f"{Emojis.TWISTED_BOW} Obtain 1x CoX megarare or Metamorphic Dust - Twisted Bow, Kodai Insignia, Elder Maul, or Olmlet",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.SUBMISSIONS} Submissions Remaining",
        value="1",
        inline=False
    )
    embed.add_field(
        name=f"",
        value="Complete the boss tile to advance to World 2!",
        inline=False
    )
    embed.set_footer(text="Use /submit in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_w2_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{Emojis.TRIAL_ICON_W1} Tumeken's Trial",
        value="Navigate your way through the perilous tombs...",
        inline=False
    )
    w2_path_chosen = team_data.get("w2_path_chosen", 0)
    if w2_path_chosen == 0:
        embed.add_field(
            name="Complete **one of your choice** to advance to the next room.",
            value="",
            inline=False
        )
        embed.add_field(
            name=f"**Trial 1-A: {Emojis.TRIAL_W2_1} Golden Tench**",
            value=f"`{format_submission(team_data['w2key1_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**Trial 1-B: {Emojis.TRIAL_W2_2} Golden Pheasant egg**",
            value=f"`{format_submission(team_data['w2key2_completion_counter'])}`",
            inline=False
        )
    elif w2_path_chosen == 1:
        embed.add_field(
            name=f"**Trial 2: {Emojis.TRIAL_W2_4} 3x Cerberus Crystals**",
            value=f"`{format_submission(team_data['w2key4_completion_counter'])}`",
            inline=False
        )
    elif w2_path_chosen == -1:
        embed.add_field(
            name=f"**Trial 2: {Emojis.TRIAL_W2_3} 3x Sunfire Fanatic Pieces**",
            value=f"`{format_submission(team_data['w2key3_completion_counter'])}`",
            inline=False
        )
    elif w2_path_chosen == 2:
        embed.add_field(
            name=f"**Trial 3: {Emojis.TRIAL_W2_5} 3x Weapons from CoX/ToB/ToA**\n*Ghrazi Rapier, Scythe of Vitur, Sanguinesti Staff, Osmumten's Fang, Tumeken's Shadow, Twisted Bow, Kodai Wand, Elder Maul, Dinh's Bulwark, Dragon Hunter Crossbow, Dragon Claws*",
            value=f"`{format_submission(team_data['w2key5_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"Complete this trial to obtain the desert key.",
            value=f"",
            inline=False
        )
    return embed

def build_w2_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.yellow()
    )
    embed.add_field(
        name=f"{Emojis.VARLAMORE_FLAG}  2-B: Eclipse of the Sun",
        value=f"{Emojis.RALOS} Obtain 1x Tonalztics of Ralos",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.SUBMISSIONS} Submissions Remaining",
        value=f"{team_data['w2boss_completion_counter']}",
        inline=False
    )
    embed.add_field(
        name=f"",
        value="Complete the boss tile to advance to World 3!",
        inline=False
    )
    embed.set_footer(text="Use /submit in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_w3_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{Emojis.FIRE} Ancient Brazier",
        value="Complete **one trial of your choosing** to light the brazier.",
        inline=False
    )

    w3_braziers_lit = team_data.get("w3_braziers_lit", 0)
    if w3_braziers_lit == 0:
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_1} Trial 1-A: 10x Vorkath Heads**",
            value=f"`{format_submission(team_data['w3key1_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_2} Trial 1-B: Dragon Hunter Wand**",
            value=f"`{format_submission(team_data['w3key2_completion_counter'])}`",
            inline=False
        )    
    if w3_braziers_lit == 1:
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_3} Trial 2-A: Granite Man**\nGranite helmet, body, legs, weapon, shield, ring, boots, gloves.\n*(2h counts for weapon + shield)*",
            value=f"`{format_submission(team_data['w3key3_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_4} Trial 2-B: Raid Man**\nRaid unique helmet slot, chestplate, legs, weapon, ring, and shield.\n*(2h counts for weapon + shield)*",
            value=f"`{format_submission(team_data['w3key4_completion_counter'])}`",
            inline=False
        )
    if w3_braziers_lit == 2:
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_5} Trial 3-A: Bran**",
            value=f"`{format_submission(team_data['w3key5_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**{Emojis.TRIAL_W3_6} Trial 3-B: Moxi**",
            value=f"`{format_submission(team_data['w3key6_completion_counter'])}`",
            inline=False
        )
    return embed

def build_w3_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name=f"{Emojis.ANCIENT_ICON} Ancient Confrontation",
        value=f"{Emojis.ZCB} **Build a ZCB from scratch.**\nObtain 1x Nihil Horn and 1x Armadyl Crossbow",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.SUBMISSIONS} Submissions Remaining",
        value=f"{team_data['w3boss_completion_counter']}",
        inline=False
    )
    embed.add_field(
        name=f"",
        value="Complete the boss tile to advance to World 3!",
        inline=False
    )
    embed.set_footer(text="Use /submit in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_w4_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )

    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
    
    w4_trial_iteration = team_data.get('w4_trial_iteration', 0)
    if w4_trial_iteration == 0:
        embed.add_field(
            name=f"{Emojis.BLOOD_RUNE} Trial of the Void",
            value="Complete **this tile** to advance to the next room.",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.TRIAL_W4_1} Trial 1: Any 3x Armor Pieces from ToB/CoX/ToA",
            value=f"`{format_submission(team_data['w4key1_completion_counter'])}`",
            inline=False
        )
    elif w4_trial_iteration == 1:
        embed.add_field(
            name=f"{Emojis.BLOOD_RUNE} Trial of the Void",
            value="Choose **one of these 3** to advance to the next room.",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.TRIAL_W4_2} Trial 2-A: 3x Oathplate Armor Pieces",
            value=f"`{format_submission(team_data['w4key2_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.TRIAL_W4_3} Trial 2-B: Enhanced Weapon Seed",
            value=f"`{format_submission(team_data['w4key3_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.TRIAL_W4_4} Trial 2-C: Nightmare Staff",
            value=f"`{format_submission(team_data['w4key4_completion_counter'])}`",
            inline=False
        )
    elif w4_trial_iteration == 2:
        embed.add_field(
            name=f"{Emojis.BLOOD_RUNE} Trial of the Void",
            value="Complete **this tile** to advance to the finale of the game!",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.TRIAL_W4_5} Trial 3: Holy Elixir",
            value=f"`{format_submission(team_data['w4key5_completion_counter'])}`",
            inline=False
        )

    return embed

def build_w4_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name=f"{Emojis.BLOOD_RUNE} It's not over til...",
        value="Obtain 5x HMT kits (Holy, Sanguine, Dust)",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.SUBMISSIONS} Submissions Remaining",
        value=f"{team_data['w4boss_completion_counter']}",
        inline=False
    )
    embed.add_field(
        name=f"",
        value="Complete the boss tile to win the event!",
        inline=False
    )
    embed.set_footer(text="Use /submit in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_storyline_embed(storyline):
    embed = discord.Embed(title = storyline["title"])
    embed.description = storyline["dialogue"]
    embed.set_footer(text="Use /board to see your team's progress!", icon_url=Emojis.SKW_LOGO)
    
    # Handle image attachment
    file = None
    if storyline.get("image"):
        image_path = os.path.join(os.path.dirname(__file__), "images", storyline["image"])
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=storyline["image"])
            embed.set_image(url=f"attachment://{storyline['image']}")
    
    return embed, file
    
def format_submission(counter):
    if counter <= 0:
        return f"`Complete!`"
    else:
        return f"{counter} submission(s) needed"

key_tile_names = {
    1: "Mystic Cove Trial",
    2: "Scarab's Labrynth",
    3: "Icy Path",
    4: "4-T: Drakan's Shade"
}