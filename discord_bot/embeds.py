from datetime import datetime, timedelta, timezone
from constants import Emojis
import discord
from constants import WORLD_NAMES
from dateutil import parser
import os

def build_team_board_embed(team_data, tile_info, team_level_string):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    # The image should be set by the caller using set_image(url="attachment://team_board.png")
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your tile completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"🗺️ {WORLD_NAMES[team_data['current_world']]} {team_level_string}",
        value=f"{tile_info['tile_name']} ([Wiki]({tile_info['wiki_url']}))",
        inline=False
    )
    embed.add_field(
        name="📝 Submissions Remaining",
        value=f"{team_data['completion_counter']}",
        inline=False
    )
    last_rolled_at = parser.parse(team_data['last_rolled_at'])  # handles RFC 1123
    next_allowed_time = last_rolled_at + timedelta(hours=12)
    discord_epoch_relative = int(next_allowed_time.timestamp())

    # can skip if over 12 hrs
    can_skip = next_allowed_time < datetime.now(timezone.utc)

    embed.add_field(
        name="⏭️ Skip",
        value=f"You can't skip this tile until <t:{discord_epoch_relative}:R>."
            if not can_skip else "Your team can skip this tile now!",
        inline=False
    )
    return embed

def build_w1_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion. There will be multiple selections.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{key_tile_names[team_data['current_world']]}",
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
        name=f"{Emojis.TRIAL_W1_1} Trial 1: Any CoX Purple",
        value=f"`{format_submission(team_data['w1key1_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_2} Trial 2: Crystal Tool Seed",
        value=f"`{format_submission(team_data['w1key2_completion_counter'])}`",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.TRIAL_W1_3} Trial 3: 4x Burning Claws",
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
        value=f"{Emojis.TWISTED_BOW} Obtain 1x CoX megarare - Twisted Bow, Kodai Insignia, Elder Maul, or Olmlet",
        inline=False
    )
    embed.add_field(
        name="📝 Submissions Remaining",
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
            name=f"**Trial 1-B: {Emojis.TRIAL_W2_2} 5x Obsidian Armor Pieces**",
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
            name=f"**Trial 2: {Emojis.TRIAL_W2_3} Uncut Onyx**",
            value=f"`{format_submission(team_data['w2key3_completion_counter'])}`",
            inline=False
        )
    elif w2_path_chosen == 2:
        embed.add_field(
            name=f"**Trial 3: {Emojis.TRIAL_W2_5} Any ToA Purple**",
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
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name="Eclipse of the Sun",
        value="Obtain 1x Tonalztics of Ralos",
        inline=False
    )
    embed.set_footer(text="Use /boss in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_w3_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"Ancient Brazier",
        value="Complete **one trial of your choosing** to light the brazier.",
        inline=False
    )

    w3_braziers_lit = team_data.get("w3_braziers_lit", 0)
    if w3_braziers_lit == 0:
        embed.add_field(
            name=f"**Trial 1-A: 3x Chromium Ingots from Whisperer**",
            value=f"`{format_submission(team_data['w3key1_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**Trial 1-B: Moxi**",
            value=f"`{format_submission(team_data['w3key2_completion_counter'])}`",
            inline=False
        )    
    if w3_braziers_lit == 1:
        embed.add_field(
            name=f"**Trial 2-A: 10x Vorkath Heads**",
            value=f"`{format_submission(team_data['w3key3_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**Trial 2-B: Full Ancient Ceremonial Robes**",
            value=f"`{format_submission(team_data['w3key4_completion_counter'])}`",
            inline=False
        )
    if w3_braziers_lit == 2:
        embed.add_field(
            name=f"**Trial 3-A: Any Tome**",
            value=f"`{format_submission(team_data['w3key5_completion_counter'])}`",
            inline=False
        )
        embed.add_field(
            name=f"**Trial 3-B: Ice Quartz**",
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
        name="Ancient Confrontation",
        value="Build a ZCB from scratch.\n\nObtain 1x Nihil Horn and 1x Armadyl Crossbow",
        inline=False
    )
    embed.add_field(
        name="📝 Submissions Remaining",
        value=f"{team_data['w3boss_completion_counter']}",
        inline=False
    )
    embed.set_footer(text="Use /boss in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_w4_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /submit in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"Drakan's Trial",
        value="Complete **one trial of your choosing** to advance to the next room.",
        inline=False
    )

    return embed

def build_w4_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name="It's not over til...",
        value="5 Hmt kits",
        inline=False
    )
    embed.add_field(
        name="📝 Submissions Remaining",
        value=f"{team_data['w4boss_completion_counter']}",
        inline=False
    )
    embed.set_footer(text="Use /boss in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
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