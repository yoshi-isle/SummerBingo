class DiscordIDs:
    PENDING_SUBMISSIONS_CHANNEL_ID = 1379165881518522408
    APPROVED_SUBMISSIONS_CHANNEL_ID = 1379165982391533588
    GUILD_ID = 1367922296764891246
    TANGY_DISCORD_ID = 726237123857874975

class ApiUrls:
    BASE_URL = "http://game_service_api:5000"

    # Teams
    TEAM = f"{BASE_URL}/teams"
    TEAM_BY_ID = f"{BASE_URL}/teams/discord/{{id}}"
    TEAM_BY_ID_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}"
    TEAM_CURRENT_TILE = f"{BASE_URL}/teams/discord/{{id}}/current_tile"
    TEAM_CURRENT_TILE_WITHOUT_DISCORD = f"{BASE_URL}/teams/{{id}}/current_tile"
    TEAM_ADVANCE_TILE = f"{BASE_URL}/teams/{{id}}/advance_tile"
    TEAM_LEVEL_NUMBER = f"{BASE_URL}/teams/{{id}}/world_level"
    TEAM_LEVEL_NUMBER_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}/world_level"
    TEAM_BOARD_INFORMATION = f"{BASE_URL}/teams/discord/{{id}}/board_information"
    TEAM_BOARD_INFORMATION_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}/board_information"

    # Submissions
    SUBMISSION = f"{BASE_URL}/submission/{{id}}"
    CREATE_SUBMISSION = f"{BASE_URL}/submission"
    APPROVE_SUBMISSION = f"{BASE_URL}/submission/approve/{{id}}"
    DENY_SUBMISSION = f"{BASE_URL}/submission/deny/{{id}}"

    # Images
    IMAGE_BOARD = f"{BASE_URL}/image/user/{{id}}"
    IMAGE_BOARD_BY_TEAM_ID = f"{BASE_URL}/image/team/{{id}}"
    IMAGE_GET = f"{BASE_URL}/images/{{url}}"

WORLD_NAMES = {
    1: "Twisted Plains",
    2: "Cozy Caverns",
    3: "Tumeken's Oasis",
    4: "Castle Drakan",
}