from constants import Emojis
import discord
from constants import WORLD_NAMES

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
    embed.add_field(
        name="⏭️ Skip",
        value=f"You can't skip this tile until <t:1751316173:R>",
        inline=False
    )
    return embed

def build_key_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name']
    )
    embed.set_thumbnail(url=team_data["thumbnail_url"])
    embed.set_footer(text="Use /key in your team channel to submit your key tile completion.", icon_url=Emojis.SKW_LOGO)
    embed.add_field(
        name=f"{key_tile_names[team_data['current_world']]}",
        value="Collect 3 out of 5 keys to unlock the boss room.",
        inline=False
    )

    key_count = 0
    for counter in [team_data["w1key1_completion_counter"], 
                    team_data["w1key2_completion_counter"],
                    team_data["w1key3_completion_counter"],
                    team_data["w1key4_completion_counter"],
                    team_data["w1key5_completion_counter"]]:
        key_count += counter == 0

    def format_submission(counter):
        if counter == 0:
            return f"{Emojis.KEY} **Complete!**"
        else:
            return f"{counter} submission(s) needed"

    submissions_needed_text = (
        f"Key 1: {format_submission(team_data['w1key1_completion_counter'])}\n"
        f"Key 2: {format_submission(team_data['w1key2_completion_counter'])}\n"
        f"Key 3: {format_submission(team_data['w1key3_completion_counter'])}\n"
        f"Key 4: {format_submission(team_data['w1key4_completion_counter'])}\n"
        f"Key 5: {format_submission(team_data['w1key5_completion_counter'])}"
    )
    embed.add_field(
        name="Submissions Needed",
        value=submissions_needed_text,
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
        name="Keys Acquired",
        value=" ".join(key_emojis),
        inline=False
    )
    embed.add_field(
        name="Skips",
        value=f"You cannot skip this challenge.",
        inline=False
    )
    return embed

def build_boss_board_embed(team_data):
    embed = discord.Embed(
        title=team_data['team_name'],
        color=discord.Color.dark_purple()
    )
    embed.add_field(
        name=f"{Emojis.OLMLET} 1-B: Showdown at the Summit",
        value="Complete the challenge to clear the world.",
        inline=False
    )
    embed.add_field(
        name="Skips",
        value=f"You cannot skip this challenge.",
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
    2: "2-T: Icy Path",
    3: "3-T: Scarab's Labrynth",
    4: "4-T: Drakan's Shade"
}