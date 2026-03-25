def send_to_board(patterns):
    print("\nSending to fake board...")
    for item in patterns:
        print(f"Character: {item['char']} -> Pattern: {item['pattern']}")
    print("Done.\n")

def reset_board():
    print("Fake board reset.\n")

def clear_board():
    print("Fake board cleared.\n")