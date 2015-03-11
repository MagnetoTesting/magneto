import sys
from IPython import embed

from .magneto import Magneto


m = magneto = None


def stop():
    if m:
        m.server.stop()


def main():
    args = sys.argv[1:]
    Magneto.configure(*args)
    m = magneto = Magneto.instance()

    embed()


if __name__ == '__main__':
    main()