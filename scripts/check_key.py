import os
import sys


def main():
    k = os.getenv("DEEPSEEK_API_KEY")
    if k:
        print("DEEPSEEK_API_KEY set")
        return 0
    else:
        print("DEEPSEEK_API_KEY NOT set")
        return 1


if __name__ == "__main__":
    sys.exit(main())
