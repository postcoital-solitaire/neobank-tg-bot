checksum_table = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'a': 10, 'b': 11, 'c': 12, 'd': 13, 'e': 14, 'f': 15, 'g': 16, 'h': 17, 'i': 18, 'j': 19, 'k': 20, 'l': 21, 'm': 22,
    'n': 23, 'o': 24, 'p': 25, 'q': 26, 'r': 27, 's': 28, 't': 29, 'u': 30, 'v': 31, 'w': 32, 'x': 33, 'y': 34, 'z': 35,
    '<': 0
}


def calc_checksum(text: str):
    checksum = 0
    for i, symbol in enumerate(text):
        m = {
            0: 7,
            1: 3,
            2: 1
        }[i % 3]

        checksum += checksum_table[symbol.lower()] * m

    return checksum % 10
