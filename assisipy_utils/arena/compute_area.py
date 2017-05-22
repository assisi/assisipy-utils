'''
I want to add this to the constructors but until all are done, just leave
this one stand alone



'''

def area_stadium(l, w):
    '''
    stadium-shaped arena.

    '''
    r = w/2.0
    x = l - w
    y = w
    a1 = x*y
    a2 = np.pi * r**2 /2.0
    a3 = a2
    print "{:.3f} + {:.3f} + {:.3f}".format(a1, a2, a3)
    return a1+a2+a3

