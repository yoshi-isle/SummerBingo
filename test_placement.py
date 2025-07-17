#!/usr/bin/env python3
"""
Vigorous test suite for the placement logic to ensure ties are handled correctly.
Tests include world progression, level progression, game state tie-breaking, and world 3 special cases.
"""

def get_effective_game_state(game_state, world):
    """
    Adjust game state for world 3 (exclude game state 1 checks)
    For world 3, treat game state 1 as 0, but keep game state 2 as 2
    """
    if world == 3 and game_state == 1:
        return 0  # Treat game state 1 as 0 for world 3
    return game_state

def get_placement(target_team, all_teams):
    """Calculate placement for a target team using the same logic as the API."""
    target_world = target_team["world_number"]
    target_level = target_team["level_number"]
    target_game_state = target_team.get("game_state", 0)
    target_effective_game_state = get_effective_game_state(target_game_state, target_world)
    
    teams_ahead = 0
    for team in all_teams:
        team_world = team["world_number"]
        team_level = team["level_number"]
        team_game_state = team.get("game_state", 0)
        team_effective_game_state = get_effective_game_state(team_game_state, team_world)
        
        # If this team is ahead (higher world or same world but higher level or same world/level but higher game state)
        if (team_world > target_world or 
            (team_world == target_world and team_level > target_level) or
            (team_world == target_world and team_level == target_level and team_effective_game_state > target_effective_game_state)):
            teams_ahead += 1
    
    return teams_ahead + 1

def print_test_results(test_name, teams, expected_placements):
    """Print test results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    results = []
    for team in teams:
        placement = get_placement(team, teams)
        world = team["world_number"]
        level = team["level_number"]
        game_state = team.get("game_state", 0)
        effective_game_state = get_effective_game_state(game_state, world)
        
        result = {
            "team": team["team_name"],
            "world": world,
            "level": level,
            "game_state": game_state,
            "effective_game_state": effective_game_state,
            "placement": placement
        }
        results.append(result)
    
    # Sort by placement for easier reading
    results.sort(key=lambda x: x["placement"])
    
    print(f"{'Team':<8} {'World':<5} {'Level':<5} {'GameState':<9} {'EffGameState':<11} {'Placement':<9} {'Expected':<8} {'Status'}")
    print("-" * 80)
    
    all_passed = True
    for result in results:
        expected = expected_placements.get(result["team"], "?")
        status = "✓ PASS" if result["placement"] == expected else "✗ FAIL"
        if result["placement"] != expected:
            all_passed = False
            
        print(f"{result['team']:<8} {result['world']:<5} {result['level']:<5} {result['game_state']:<9} {result['effective_game_state']:<11} {result['placement']:<9} {expected:<8} {status}")
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

def test_basic_world_progression():
    """Test 1: Basic world progression - higher world should rank higher."""
    teams = [
        {"team_name": "Team1", "world_number": 4, "level_number": 1, "game_state": 0},
        {"team_name": "Team2", "world_number": 3, "level_number": 10, "game_state": 0},
        {"team_name": "Team3", "world_number": 2, "level_number": 15, "game_state": 0},
        {"team_name": "Team4", "world_number": 2, "level_number": 5, "game_state": 0},
        {"team_name": "Team5", "world_number": 1, "level_number": 20, "game_state": 0},
        {"team_name": "Team6", "world_number": 1, "level_number": 1, "game_state": 0},
    ]
    
    expected = {
        "Team1": 1,  # World 4-1
        "Team2": 2,  # World 3-10
        "Team3": 3,  # World 2-15
        "Team4": 4,  # World 2-5
        "Team5": 5,  # World 1-20
        "Team6": 6,  # World 1-1
    }
    
    print_test_results("Basic World Progression", teams, expected)

def test_same_world_level_progression():
    """Test 2: Same world, different levels - higher level should rank higher."""
    teams = [
        {"team_name": "Team1", "world_number": 2, "level_number": 20, "game_state": 0},
        {"team_name": "Team2", "world_number": 2, "level_number": 15, "game_state": 0},
        {"team_name": "Team3", "world_number": 2, "level_number": 10, "game_state": 0},
        {"team_name": "Team4", "world_number": 2, "level_number": 5, "game_state": 0},
        {"team_name": "Team5", "world_number": 2, "level_number": 3, "game_state": 0},
        {"team_name": "Team6", "world_number": 2, "level_number": 1, "game_state": 0},
    ]
    
    expected = {
        "Team1": 1,  # 2-20
        "Team2": 2,  # 2-15
        "Team3": 3,  # 2-10
        "Team4": 4,  # 2-5
        "Team5": 5,  # 2-3
        "Team6": 6,  # 2-1
    }
    
    print_test_results("Same World Level Progression", teams, expected)

def test_game_state_tie_breaking():
    """Test 3: Same world and level, different game states - higher game state should rank higher."""
    teams = [
        {"team_name": "Team1", "world_number": 2, "level_number": 10, "game_state": 2},
        {"team_name": "Team2", "world_number": 2, "level_number": 10, "game_state": 1},
        {"team_name": "Team3", "world_number": 2, "level_number": 10, "game_state": 0},
        {"team_name": "Team4", "world_number": 2, "level_number": 10, "game_state": 2},
        {"team_name": "Team5", "world_number": 2, "level_number": 10, "game_state": 1},
        {"team_name": "Team6", "world_number": 2, "level_number": 10, "game_state": 0},
    ]
    
    expected = {
        "Team1": 1,  # 2-10, game_state 2 (tied for 1st)
        "Team2": 3,  # 2-10, game_state 1 (tied for 3rd)
        "Team3": 5,  # 2-10, game_state 0 (tied for 5th)
        "Team4": 1,  # 2-10, game_state 2 (tied for 1st)
        "Team5": 3,  # 2-10, game_state 1 (tied for 3rd)
        "Team6": 5,  # 2-10, game_state 0 (tied for 5th)
    }
    
    print_test_results("Game State Tie Breaking", teams, expected)

def test_world3_special_case():
    """Test 4: World 3 special case - game state 1 should be treated as 0."""
    teams = [
        {"team_name": "Team1", "world_number": 3, "level_number": 5, "game_state": 2},
        {"team_name": "Team2", "world_number": 3, "level_number": 5, "game_state": 1},  # Should be treated as 0
        {"team_name": "Team3", "world_number": 3, "level_number": 5, "game_state": 0},
        {"team_name": "Team4", "world_number": 3, "level_number": 5, "game_state": 2},
        {"team_name": "Team5", "world_number": 3, "level_number": 5, "game_state": 1},  # Should be treated as 0
        {"team_name": "Team6", "world_number": 3, "level_number": 5, "game_state": 0},
    ]
    
    expected = {
        "Team1": 1,  # 3-5, game_state 2 (tied for 1st)
        "Team2": 3,  # 3-5, game_state 1 → 0 (tied for 3rd)
        "Team3": 3,  # 3-5, game_state 0 (tied for 3rd)
        "Team4": 1,  # 3-5, game_state 2 (tied for 1st)
        "Team5": 3,  # 3-5, game_state 1 → 0 (tied for 3rd)
        "Team6": 3,  # 3-5, game_state 0 (tied for 3rd)
    }
    
    print_test_results("World 3 Special Case (game_state 1 → 0)", teams, expected)

def test_mixed_world_levels_with_game_states():
    """Test 5: Mixed worlds and levels with game states."""
    teams = [
        {"team_name": "Team1", "world_number": 3, "level_number": 5, "game_state": 1},  # World 3: 1→0
        {"team_name": "Team2", "world_number": 3, "level_number": 5, "game_state": 2},
        {"team_name": "Team3", "world_number": 2, "level_number": 10, "game_state": 2},
        {"team_name": "Team4", "world_number": 2, "level_number": 10, "game_state": 1},
        {"team_name": "Team5", "world_number": 2, "level_number": 10, "game_state": 0},
        {"team_name": "Team6", "world_number": 1, "level_number": 20, "game_state": 2},
    ]
    
    expected = {
        "Team1": 2,  # 3-5, game_state 1→0
        "Team2": 1,  # 3-5, game_state 2 (highest)
        "Team3": 3,  # 2-10, game_state 2
        "Team4": 4,  # 2-10, game_state 1
        "Team5": 5,  # 2-10, game_state 0
        "Team6": 6,  # 1-20, game_state 2 (lowest world)
    }
    
    print_test_results("Mixed Worlds/Levels with Game States", teams, expected)

def test_complex_tie_scenarios():
    """Test 6: Complex tie scenarios with multiple tie-breaking levels."""
    teams = [
        {"team_name": "Team1", "world_number": 2, "level_number": 8, "game_state": 2},
        {"team_name": "Team2", "world_number": 2, "level_number": 8, "game_state": 1},
        {"team_name": "Team3", "world_number": 2, "level_number": 7, "game_state": 2},
        {"team_name": "Team4", "world_number": 2, "level_number": 7, "game_state": 1},
        {"team_name": "Team5", "world_number": 2, "level_number": 7, "game_state": 0},
        {"team_name": "Team6", "world_number": 2, "level_number": 6, "game_state": 2},
    ]
    
    expected = {
        "Team1": 1,  # 2-8, game_state 2 (highest level + highest game_state)
        "Team2": 2,  # 2-8, game_state 1 (highest level + middle game_state)
        "Team3": 3,  # 2-7, game_state 2 (middle level + highest game_state)
        "Team4": 4,  # 2-7, game_state 1 (middle level + middle game_state)
        "Team5": 5,  # 2-7, game_state 0 (middle level + lowest game_state)
        "Team6": 6,  # 2-6, game_state 2 (lowest level)
    }
    
    print_test_results("Complex Tie Scenarios", teams, expected)

def test_world3_vs_other_worlds():
    """Test 7: World 3 teams vs other worlds to ensure world 3 special case doesn't affect cross-world comparisons."""
    teams = [
        {"team_name": "Team1", "world_number": 4, "level_number": 1, "game_state": 0},
        {"team_name": "Team2", "world_number": 3, "level_number": 10, "game_state": 1},  # World 3: 1→0
        {"team_name": "Team3", "world_number": 3, "level_number": 10, "game_state": 0},
        {"team_name": "Team4", "world_number": 2, "level_number": 15, "game_state": 2},
        {"team_name": "Team5", "world_number": 2, "level_number": 15, "game_state": 1},
        {"team_name": "Team6", "world_number": 1, "level_number": 20, "game_state": 2},
    ]
    
    expected = {
        "Team1": 1,  # 4-1, game_state 0 (highest world)
        "Team2": 2,  # 3-10, game_state 1→0 (tied for 2nd)
        "Team3": 2,  # 3-10, game_state 0 (tied for 2nd)
        "Team4": 4,  # 2-15, game_state 2
        "Team5": 5,  # 2-15, game_state 1
        "Team6": 6,  # 1-20, game_state 2 (lowest world)
    }
    
    print_test_results("World 3 vs Other Worlds", teams, expected)

def test_all_tied_scenarios():
    """Test 8: All teams completely tied (edge case)."""
    teams = [
        {"team_name": "Team1", "world_number": 2, "level_number": 5, "game_state": 1},
        {"team_name": "Team2", "world_number": 2, "level_number": 5, "game_state": 1},
        {"team_name": "Team3", "world_number": 2, "level_number": 5, "game_state": 1},
        {"team_name": "Team4", "world_number": 2, "level_number": 5, "game_state": 1},
        {"team_name": "Team5", "world_number": 2, "level_number": 5, "game_state": 1},
        {"team_name": "Team6", "world_number": 2, "level_number": 5, "game_state": 1},
    ]
    
    expected = {
        "Team1": 1,  # All tied for 1st
        "Team2": 1,
        "Team3": 1,
        "Team4": 1,
        "Team5": 1,
        "Team6": 1,
    }
    
    print_test_results("All Teams Tied", teams, expected)

def run_all_tests():
    """Run all placement tests."""
    print("VIGOROUS PLACEMENT LOGIC TEST SUITE")
    print("Testing Summer Bingo leaderboard placement calculations")
    print(f"Number of teams per test: 6 (min and max constraint)")
    
    test_basic_world_progression()
    test_same_world_level_progression()
    test_game_state_tie_breaking()
    test_world3_special_case()
    test_mixed_world_levels_with_game_states()
    test_complex_tie_scenarios()
    test_world3_vs_other_worlds()
    test_all_tied_scenarios()
    
    print(f"\n{'='*60}")
    print("ALL TESTS COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_all_tests()
