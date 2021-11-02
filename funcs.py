
def flush_tasks(tasks):
    to_flush = []
    for task in tasks:
        if tasks[task].cancelled():
            to_flush.append(task)
    for task in to_flush:
        tasks.pop(task)
    return len(to_flush)


def get_player_from_name(player_list, player_name):
    if player_list is None:
        return None
    for player in player_list:
        if player['name'] == player_name:
            return player