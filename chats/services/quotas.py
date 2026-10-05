def chatbots_remaining(user):
    return user.chatbots_available - user.chatbots.filter(active=True).count()


def within_character_limit(character_length, limit):
    return character_length <= limit
