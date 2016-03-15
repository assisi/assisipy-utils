''' written by Sven Marnach - reference:
http://stackoverflow.com/questions/12334442/does-python-have-a-linspace-function-in-its-std-lib'''
def linspace(start, stop, n):
    '''
    Returns a generator producing n points, equally spaced between
    start and stop. Both endpoints are included.
    '''
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i

