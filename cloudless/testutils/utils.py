"""
Utilities that are useful for frameworks that create temporary resources.
"""
import random
import string

def generate_unique_name(base):
    """
    Generates a somewhat unique name given "base".
    """
    random_length = 10
    random_string = ''.join(random.choices(string.ascii_lowercase,
                                           k=random_length))
    return "%s-%s" % (base, random_string)
