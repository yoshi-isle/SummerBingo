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
        name="Submissions",
        value=f"This tile requires {tile_info['completion_counter']} submissions. Your team needs {team_data['completion_counter']} more",
        inline=True
    )
    embed.add_field(
        name="⏭️ Skip",
        value=f"You cannot skip this level until: WIP",
        inline=True
    )
    return embed