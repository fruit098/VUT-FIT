Second project for Cryptography subject, main goal is to derive private key from public based on Eliptict Curves cryptography via the enumaration of small group of numbers

Code has set this parameters:
Fp = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
a = -0x3
b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
Base point = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)

Example use of program:

$ make decipher publicKey="(0x477...3e, 0xaa0...dc)"
17
