import sys
from magneto.magneto import Magneto

if __name__ == '__main__':
    args = sys.argv[1:]
    Magneto.configure(*args)
    m = magneto = Magneto.instance()