from reedsolo import RSCodec, ReedSolomonError

rsc = RSCodec(32)

message = b"hello " * 20
encoded = rsc.encode(message)
print("Message: ", len(message), "bytes encoded: ", len(encoded), " bytes")

damaged = bytearray(encoded)
hole = list(range(50, 70))
for i in hole:
    damaged[i] = 0

# repair without telling it where the hole is
try:
    rsc.decode(damaged)
    print("worked")
except ReedSolomonError:
    print("didn't work")

# tell it where the hole is
fixed, _, _ = rsc.decode(damaged, erase_pos=hole)
print("with erasures: fixed ", bytes(fixed) == message)

# big hole
big_hole = list(range(50, 90))
for i in big_hole:
    damaged[i] = 0
try:
    rsc.decode(damaged, erase_pos=big_hole)
    print("40 holes fixed")
except ReedSolomonError:
    print("40 holes is too much damage")

