import sys


def main() -> None:
    print("READY", flush=True)

    for line in sys.stdin:
        if line.strip() == "SHUTDOWN":
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
