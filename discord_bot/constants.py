class Emojis:
    KEY="<:key:1389645693941190666>"
    KEY_NOT_OBTAINED="<:not_obtained:1389646593074139166>"
    DUNGEON="<:dungeon:1389648812355748051>"
    OLMLET="<:Olmlet:1389757224963801229>"

class DiscordIDs:
    PENDING_SUBMISSIONS_CHANNEL_ID = 1379165881518522408
    APPROVED_SUBMISSIONS_CHANNEL_ID = 1379165982391533588
    GUILD_ID = 1367922296764891246
    TANGY_DISCORD_ID = 726237123857874975

class ApiUrls:
    BASE_URL = "http://game_service_api:5000"

    # Game state
    GAME_IS_RUNNING = f"{BASE_URL}/game_started"
    # Teams
    TEAM = f"{BASE_URL}/teams"
    TEAM_BY_ID = f"{BASE_URL}/teams/discord/{{id}}"
    TEAM_BY_ID_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}"
    TEAM_CURRENT_TILE = f"{BASE_URL}/teams/{{id}}/current_tile"
    TEAM_ADVANCE_TILE = f"{BASE_URL}/teams/{{id}}/advance_tile"
    TEAM_LEVEL_NUMBER = f"{BASE_URL}/teams/{{id}}/world_level"
    TEAM_LEVEL_NUMBER_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}/world_level"
    TEAM_BOARD_INFORMATION = f"{BASE_URL}/teams/id/{{id}}/board_information"
    ADVANCE_TO_BOSS_TILE = f"{BASE_URL}/teams/{{id}}/boss_tile"
    ADVANCE_TO_NEXT_WORLD = f"{BASE_URL}/teams/{{id}}/next_world"

    # Submissions
    SUBMISSION = f"{BASE_URL}/submission/{{id}}"
    KEY_SUBMISSION = f"{BASE_URL}/key_submission/{{id}}"
    BOSS_SUBMISSION = f"{BASE_URL}/boss_submission/{{id}}"
    CREATE_SUBMISSION = f"{BASE_URL}/submission"
    CREATE_KEY_SUBMISSION = f"{BASE_URL}/key_submission"
    CREATE_BOSS_SUBMISSION = f"{BASE_URL}/boss_submission"
    APPROVE_SUBMISSION = f"{BASE_URL}/submission/approve/{{id}}"
    APPROVE_KEY_SUBMISSION = f"{BASE_URL}/submission/approve_key/{{key_id}}/{{id}}"
    APPROVE_BOSS_SUBMISSION = f"{BASE_URL}/submission/approve_boss/{{id}}"
    DENY_SUBMISSION = f"{BASE_URL}/submission/deny/{{id}}"

    # Images
    IMAGE_BOARD = f"{BASE_URL}/image/team/{{id}}"
    IMAGE_GET = f"{BASE_URL}/images/{{url}}"

WORLD_NAMES = {
    1: "Mystic Cove",
    2: "Zaros Plateau",
    3: "Tumeken's Oasis",
    4: "Drakan's Void",
}