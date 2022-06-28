
def flush_tasks(tasks):  # Removes tasks from the tasks list if they have been cancelled (like live info)
    to_flush = []
    for task in tasks:
        if tasks[task].cancelled():
            to_flush.append(task)
    for task in to_flush:
        tasks.pop(task)
    return len(to_flush)


def get_player_from_name(player_list, player_name, precise=True):  # Finds the player data by player name
    if player_list is None:
        return None
    for player in player_list:
        if player['name'] == player_name:
            return player
        if not precise and player_name in player['name']:
            return player