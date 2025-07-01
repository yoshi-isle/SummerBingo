def build_team_board_embed(team_data, tile_info, team_level_string):
    import discord
    from constants import WORLD_NAMES
    embed = discord.Embed(
        title=f"Team Board: {team_data['team_name']}",
        color=discord.Color.blue()
    )
    # The image should be set by the caller using set_image(url="attachment://team_board.png")
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/abobo/images/4/4e/Goomba.png/revision/latest?cb=20200706184805")
    embed.set_footer(text="Use `/submit` in your team channel to submit your tile completion.")
    embed.add_field(
        name="🗺️ Current Level",
        value=f"{WORLD_NAMES[team_data['current_world']]} {team_level_string}\n**{tile_info['tile_name']}**",
        inline=False
    )
    embed.add_field(
        name="🔗 Links",
        value=f"[Eligible Drops]({tile_info['pastebin_url']})\n[OSRS Wiki]({tile_info['wiki_url']})",
        inline=True
    )
    embed.add_field(
        name="Submissions Needed",
        value=f"{team_data['completion_counter']}",
        inline=True
    )
    embed.add_field(
        name="Skip Tokens",
        value=f"You have **0** skip tokens. Next one at: <t:1751316173:R>",
        inline=False
    )
    return embed

def build_key_board_embed(team_data):
    import discord
    from constants import WORLD_NAMES
    embed = discord.Embed(
        title=f"Team Board: {team_data['team_name']}",
        color=discord.Color.blue()
    )
    # The image should be set by the caller using set_image(url="attachment://team_board.png")
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/abobo/images/4/4e/Goomba.png/revision/latest?cb=20200706184805")
    embed.set_footer(text="Use `/key` in your team channel to submit your key tile completion.")
    embed.add_field(
        name="🔑 Unlock The Boss Key",
        value=f"{key_tile_names[team_data['current_world']]}",
        inline=False
    )

    key_count = 0
    for counter in [team_data["w1key1_completion_counter"], 
                    team_data["w1key2_completion_counter"],
                    team_data["w1key3_completion_counter"],
                    team_data["w1key4_completion_counter"],
                    team_data["w1key5_completion_counter"]]:
        key_count += counter == 0

    submissions_needed_text = f'''
        Key 1: You need {team_data["w1key1_completion_counter"] if team_data["w1key1_completion_counter"] != 0 else ""} submissions
        Key 2: You need {team_data["w1key2_completion_counter"] if team_data["w1key2_completion_counter"] != 0 else ""} submissions
        Key 3: You need {team_data["w1key3_completion_counter"] if team_data["w1key3_completion_counter"] != 0 else ""} submissions
        Key 4: You need {team_data["w1key4_completion_counter"] if team_data["w1key4_completion_counter"] != 0 else ""} submissions
        Key 5: You need {team_data["w1key5_completion_counter"] if team_data["w1key5_completion_counter"] != 0 else ""} submissions'''

    embed.add_field(
        name="Keys Aquired",
        value=key_count,
        inline=True
    )
    embed.add_field(
        name="Submissions Needed",
        value=submissions_needed_text,
        inline=True
    )
    embed.add_field(
        name="Skip Tokens",
        value=f"You cannot skip a challenge tile.",
        inline=False
    )
    return embed

key_tile_names = {
    1: "1-T: Twisted Trial",
    2: "2-T: Icy Path",
    3: "3-T: Scarab's Labrynth",
    4: "4-T: Drakan's Shade"
}