def count_w1_keys(team):
    return sum(int(key) == 0 for key in [
        team["w1key1_completion_counter"],
        team["w1key2_completion_counter"],
        team["w1key3_completion_counter"],
        team["w1key4_completion_counter"],
        team["w1key5_completion_counter"]
    ])