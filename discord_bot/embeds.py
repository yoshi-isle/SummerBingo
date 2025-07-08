from datetime import datetime, timedelta, timezone
from constants import Emojis
import discord
from constants import WORLD_NAMES
from dateutil import parser

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
    embed.set_footer(text="Use /trial in your team channel to submit your trial completion.", icon_url=Emojis.SKW_LOGO)
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

    def format_submission(counter):
        if counter <= 0:
            return f"`Complete!`"
        else:
            return f"{counter} submission(s) needed"

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
            key_emojis.append(Emojis.KEY)
        else:
            key_emojis.append(Emojis.KEY_NOT_OBTAINED)
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
        value="Complete the challenge to clear the world.",
        inline=False
    )
    embed.set_footer(text="Use /boss in your team channel to submit your boss tile completion.", icon_url=Emojis.SKW_LOGO)
    return embed

def build_storyline_embed(storyline):
    embed = discord.Embed(title = storyline["title"])
    embed.description = storyline["dialogue"]
    embed.set_footer(text="Use /board to see your team's progress!", icon_url=Emojis.SKW_LOGO)
    return embed
    

key_tile_names = {
    1: "Mystic Cove Trial",
    2: "Scarab's Labrynth",
    3: "Icy Path",
    4: "4-T: Drakan's Shade"
}