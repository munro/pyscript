def blah(a):
    print('hey', a)
    h = yield 123
    print('hey', h)

g = blah(44)
print('next', g.send(None))
try:
    print('next', g.send('wee'))
except Exception:
    pass
