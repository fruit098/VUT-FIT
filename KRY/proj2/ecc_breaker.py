import sys
import ast

p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
a = -0x3
b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
g = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
         0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)

public_k = (0x6863aeecb4af52b068aed5c8e3bf2d7030b7c46e16609ce2ba2af1c9c54c116,0xe69b3f636feb14eb303579a28477e0e8880fb697580c2092c57007c79cb000bd)

def egcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        g, y, x = egcd(b % a, a)
        return g, x - (b // a) * y, y


def mod_inv(a, p):
    if a < 0:
        return p - mod_inv(-a, p)
    g, x, y = egcd(a, p)
    if g != 1:
        raise ArithmeticError("Modular inverse does not exist")
    else:
        return x % p

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def __mul__(self, other):
        _lambda = self._lambda_double(other)
        x = (_lambda ** 2 - 2 * other.x) % p
        y = (_lambda * (other.x - x) - other.y) % p
        return Point(x,y)

    def __add__(self, other):
        if self.x is None:
            return other
        if other.x is None:
            return self
        if self.x == other.x:
            return self.__mul__(other)
        _lambda = self._lambda_add(other)
        x = (_lambda ** 2 - other.x - self.x) % p
        y = (_lambda * (other.x - x) - other.y) % p
        return Point(x,y)

    def _lambda_add(self, other):
        return (self.y - other.y) * mod_inv(self.x - other.x, p)

    def _lambda_double(self, other):
        return (3 * self.x ** 2 + a) * mod_inv(2 * self.y, p)

    def __repr__(self):
        return "Point x: {}, y: {}".format(self.x, self.y)

if __name__ == "__main__":
    public_k = ast.literal_eval(sys.argv[1])

    private_key = 1
    result = Point(None, None)
    for _ in range(p):
        result += Point(*g)
        if (result.x, result.y) == public_k:
            print(private_key)
            sys.exit(0)
        private_key += 1
    print(0)

