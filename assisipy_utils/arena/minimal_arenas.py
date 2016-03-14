from math import pi, sin, cos
import random
import yaml

#from assisipy_simtools.utils.maths_utils import linspace
from transforms import Point, Transformation #,trans_valid_area_to_rect
from transforms import translate_point, find_ctr_seq, rotate_point_about_other

#{{{ arcs
def create_arc_with_width(cx, cy, radius, theta_0=pi/2, theta_end=-pi/2,
        steps=10, width=2.0):

    thetas = linspace(theta_0, theta_end, steps+1)
    arc_ctrs = [pos_on_perim(cx, cy, theta, radius) for theta in thetas]
    # there should be 'steps' polygons, joining the 's+1' points
    polys = []
    for i in xrange(steps):
        cb = arc_ctrs[i]
        ce = arc_ctrs[i+1]
        #poly = [arc_ctrs[i], arc_ctrs[i+1]]; # zero width
        # we have the centres, so we have a vector. Now we want the perp of
        # lets compute the points that are w either side of the line.
        l1, l2 = parallel_pts_w_offset(cb, ce, -width/2.0)
        r1, r2 = parallel_pts_w_offset(cb, ce, +width/2.0)

        # annoyingly the points have to go clockwise.  # will this always hold?
        poly = [r1, r2, l2, l1]
        # check that the width is approx what we asked it to be
        '''
        w1 = (l1 - r1).abs()
        w2 = (l2 - r2).abs()
        #print w1, w2, width
        '''

        polys.append(poly)

    #print "width=", width
    return polys

def parallel_pts_w_offset(cb, ce, dw):
    ''' compute positions of points that are in line parallel to cb->ce, dw away'''
    l_recip = 1.0 / ( ( (cb.x - ce.x)**2 + (cb.y - ce.y)**2)**0.5) # divide once
    pbx = cb.x + (dw * (ce.y-cb.y) * l_recip)
    pex = ce.x + (dw * (ce.y-cb.y) * l_recip)

    pby = cb.y + (dw * (cb.x-ce.x) * l_recip)
    pey = ce.y + (dw * (cb.x-ce.x) * l_recip)
    return ( Point(pbx, pby, 0), Point(pex, pey,0) )



def pos_on_perim(cx, cy, theta, radius):
    x = cx + radius * cos(theta)
    y = cy + radius * sin(theta)
    return Point(x, y, 0)
#}}}


#{{{ add bees
def gen_valid_bee_positions(valid_area, n=1, theta_rng=(0, 2*pi), trans=None):
    '''
    return a list of (x, y, theta) tuples, for locations of bees that
    are within the valid_area. '''
    # the area as given is untransformed - generate within this rectangle, uniformly
    # then transform all the points, and return them.
    xlims = valid_area[0][0], valid_area[1][0]
    ylims = valid_area[0][1], valid_area[1][1]

    # compute centre of the valid area
    bl = Point(*valid_area[0])
    tr = Point(*valid_area[1])
    poly = [bl, Point(bl.x, tr.y), tr, Point(tr.x, bl.y)]
    ctr = find_ctr_seq(poly)

    pts = []
    for i in xrange(n):
        x = random.uniform(*xlims)
        y = random.uniform(*ylims)
        yaw = random.uniform(*theta_rng)
        p = Point(x, y, 0)

        pts.append( (p, yaw) )

    # now we have the points in canonical positions, transform them appropriately
    pts_transformed = list(pts)
    if trans is None:
        pass
    else:
        pts_transformed = []
        for (p, yaw) in pts:
            p_tr = rotate_point_about_other(p, ctr, theta=trans.theta)
            p_tr = translate_point(p_tr, trans.dx, trans.dy)
            yaw_tr = yaw + trans.theta

            pts_transformed.append( (p_tr, yaw_tr) )

    return pts_transformed



#}}}


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


def read_reqs(fname):
    with open(fname) as f:
        _d = yaml.safe_load(f)
        bl_bound = _d.get('base_bl')
        tr_bound = _d.get('base_tr')
        dx = _d.get('trans').get('dx')
        dy = _d.get('trans').get('dy')
        theta = _d.get('trans').get('theta')

    trans = Transformation(dx, dy, theta)

    return (bl_bound, tr_bound, trans)
