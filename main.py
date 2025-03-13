from assistant import Assistant


def main():
    with Assistant() as a:
        a.start()

if __name__ == '__main__':
    main()