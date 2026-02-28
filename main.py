import argparse
from OLG import AutoPlay


def main():
    parser = argparse.ArgumentParser(description="Launcher for TRASH project tools")
    parser.add_argument('mode', choices=['olg','onetouch','predict'], help='Which component to run')
    parser.add_argument('--balance', type=float, default=1000.0, help='Starting balance for OLG AutoPlay')
    parser.add_argument('--debug', action='store_true', help='Enable on screen debug overlay')
    args = parser.parse_args()

    try:
        print("Starting OLG AutoPlay with balance:", args.balance)
        game = AutoPlay(args.balance)
        game.Play()

    except KeyboardInterrupt:
        print('\nInterrupted by user, exiting.')


if __name__ == '__main__':
    main()
