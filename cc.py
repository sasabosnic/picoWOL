#!/usr/bin/env python

# Last commit date: $Date
# Revision: $Rev
# Author: $Author

import sys
import re
import math


class BaselineMap:
    def __init__( self, separator, filename ):
	self.map = {}
	try:
	    inmap = open( filename )
	except IOError, err:
	    sys.exit( "Error opening baseline map file '%s': %s" % ( filename, err ) )

	
	expected_headings = ["System", "Baseline", "Meridian", "Longitude", "Latitude"]
	headings = inmap.readline( ).strip( ).split( separator )
	if headings != expected_headings:
	    sys.exit( "Expected column headings %s in first line of baseline map file" % expected_headings )	

	recnum = 1
	for line in inmap:
	    recnum += 1
	    line = line[:-1]
	    fields = line.split( separator )
	    if len( fields ) != len( expected_headings ):
		sys.exit( "Expected %d values on record %d of baseline map file %s" % ( len( expected_headings ),
										       recnum,
										       filename ) )
	    key = ( int(fields[0]), int(fields[1]), int(fields[2]) )
	    long, lat = fields[3:5]
	    if long == "":
		long = "0.0"
	    if lat == "":
		lat = "0.0"

	    self.map[key] = ( float(lat), float(long) )

    def getLatLong( self, sys, baseline, meridian ):
	lat, long = self.map.get( (sys, baseline, meridian), (None,None) )
	return lat, long

'''
The following routine converts the DLS specification into lat/long
'''
def fromDLS( recnum, bmap, lsd, section, township, range, meridian ):
    if lsd < 1 or lsd > 16:
	print >> sys.stderr, "The lsd number on record %d must be in the range [1,16]" % recnum
	return None, None
    if section < 1 or section > 36:
	print >> sys.stderr, "The section number on record %d must be in the range [1,36]" % recnum
	return None, None
    if township < 1 or township > 126:
	print >> sys.stderr, "The township number on record %d must be in the range [1,126]" % recnum
	return None, None
    if range < 1 or range > 35:
	print >> sys.stderr, "The range number on record %d must be in the range [1,35]" % recnum
	return None, None
    if meridian < 1 or meridian > 6:
	print >> sys.stderr, "The meridian number on record %d must be in the range [1,6]" % recnum
	return None, None

    # Find the lsd offsets (each section broken into 4x4 grid of
    # sinusoidally ordered lsds).
    dn = (lsd-1) / 4
    if dn % 2 == 0:
	dw = (lsd-1) % 4
    else:
	dw = 3 - ( (lsd-1) % 4 )

    shiftN = (5280/4) * dn
    shiftW = (5280/4) * dw

    # Find the distance from the SE corner to the specified point in the lsd.
    # Note that the original paradox code used the value of 4 as a parameter to
    # this function.  If you divide the lsd into 4 squares, you get 9 possible
    # grid point indicess (0-8): the value of pnt indicates which.
    # Here, we are interested in the center of the lsd hence pnt = 4.
    pnt = 4
    shiftN += (pnt/3) * (5280/8)
    shiftW += (pnt%3) * (5280/8)

    # Find the section offsets (each township broken into 6x6 grid of
    # sinusoidally ordered sections).
    dn = (section-1) / 6
    if dn % 2 == 0:
	dw = (section-1) % 6
    else:
	dw = 5 - ( (section-1) % 6 )

    system = 3
    if meridian == 1:
	if township >= 27 and range <= 28:
	    system = 3
	elif township >= 31:
	    system = 3
	else:
	    system = 1
    elif meridian == 2:
	if township <= 2 and range <= 8:
	    system = 1
	elif township >= 19 and township <= 30 and range <= 12:
	    system = 1
	elif township >= 27 and township <= 30 and range <= 12:
	    system = 1
	elif township == 44 and range == 21:
	    system = 1
	elif township == 45 and (range == 21 or range == 22 or range >= 26):
	    system = 1
	elif township == 46 and range >= 25:
	    system = 1
	elif township == 47 and range >= 24:
	    system = 1
	elif township >= 49:
	    system = 3
	elif township == 48 and range >= 24 and range <= 26:
	    system = 1
	else:
	    system = 3
    elif meridian == 3:
	if range == 1 and township >= 42 and township <= 47:
	    system = 1
	elif range >= 4:
	    system = 3
	elif (range == 2 or range == 3) and (township == 43 or township == 44):
	    system = 1
	else:
	    system = 3
    else:
	system = 3

    if system == 1:
	# In this system, there are 99ft width roads surrounding every
	# section
	num_ew_roads = 6
	num_ns_roads = 6
	road_width = 99
    elif system == 3:
	# In this system, there are 66ft width roads.  Roads running ns occur
	# every section while roads running ew occur every other section
	num_ew_roads = 3
	num_ns_roads = 6
	road_width = 66
    else:
	print >> sys.stderr, "Invalid survey system for input record %d" % recnum
	return None, None

    twp_width = 6 * 5280 + ( num_ns_roads * road_width )
    twp_height = 6 * 5280 + ( num_ew_roads * road_width )

    # Calculate offset for the section
    shiftN += 5280 * dn + road_width * int( dn / ( 6 / num_ew_roads ) )
    shiftW += dw *( 5280 + road_width )

    # Find the appropriate baseline (baseline numbers start at 1
    # and increase by one every 4 townships -- the first 2 townships
    # belong to the first baseline while townships 3-6 belong to the
    # second baseline).
    base = 1 + (township+1) / 4
    diff = (township+1) % 4

    # Calculate offset from the baseline
    if diff % 2 == 1:
	shiftN += twp_height
    if diff <= 1:
	shiftN -= 2 * twp_height

    # Get the base lat and long
    baselat, baselong = bmap.getLatLong( system, base, meridian )
    if baselat is None or baselong is None:
	print >> sys.stderr, "Unable to lookup baseline for %s on input record %d" % ( dls, recnum )
	return None, None
    if baselat == '0':
	print >> sys.stderr, "Found a 0 latitude looking up baseline for %s on input record %d" % ( dls, recnum )
	return None, None

    # Calculate Latitude
    altr = 0.01745329 * baselat
    sn   = math.sin( altr )
    tmp  = math.sqrt( 1.0 - 0.00676866*sn*sn )
    lat  = baselat + shiftN*tmp*tmp*tmp/362756.54

    # Calculate Longitude
    long  = -( baselong + (shiftW + (range-1)*twp_width)*tmp/(365228.63*math.cos(altr)) )

    return lat, long



class BCBlock:
    def __init__( self, num_lat, num_long ):
	self.num_lat = int(num_lat)
	self.num_long = int(num_long)
	self.size_lat = 0.0
	self.size_long = 0.0
	self.subblock = None

    def addSubBlock( self, block ):
	self.subblock = block
	block.setSize( self.size_lat, self.size_long )

    def setSize( self, size_lat, size_long ):
	self.size_lat = float(size_lat) / self.num_lat
	self.size_long = float(size_long) / self.num_long

    def getSubLatLong( self, indices ):
	if self.subblock is None:
	    return self.size_lat/2.0, self.size_long/2.0
	else:
	    return self.subblock.getLatLong( indices )

class FirstBlock( BCBlock ):
    def __init__( self, num_lat, num_long ):
	BCBlock.__init__( self, num_lat, num_long )

    def getLatLong( self, indices ):
	index = indices.pop( 0 )
	x = index / self.num_lat
	long = self.size_long * x
	lat = self.size_lat * ( index % self.num_lat )

	sublat, sublong = BCBlock.getSubLatLong( self, indices )
	return 40+lat+sublat, 48+long+sublong

class LRBlock( BCBlock ):
    def __init__( self, num_lat, num_long ):
	BCBlock.__init__( self, num_lat, num_long )

    def getLatLong( self, indices ):
	index = indices.pop( 0 )
	y = (index-1) / self.num_long
	lat = self.size_lat * y
	long = self.size_long * ( (index-1) % self.num_long )

	sublat, sublong = BCBlock.getSubLatLong( self, indices )
	return lat+sublat, long+sublong

class SinusoidalBlock( BCBlock ):
    def __init__( self, num_lat, num_long ):
	BCBlock.__init__( self, num_lat, num_long )

    def getLatLong( self, indices ):
	index = indices.pop( 0 )
	y = (index-1) / self.num_long
	lat = self.size_lat * y
	if y % 2 == 0:
	    long = self.size_long * ( (index-1) % self.num_long )
	else:
	    long = self.size_long * ( (self.num_long-1) - ( (index-1) % self.num_long ) )

	sublat, sublong = BCBlock.getSubLatLong( self, indices )
	return lat+sublat, long+sublong
	



def fromBCNTS( recnum, blocks, b0, b1, b2, b3, b4, b5 ):

    bc_mapnums = frozenset( (82, 83, 92, 93, 94, 95, 102, 103, 104, 105 ) )
    if b0 not in bc_mapnums:
	print >> sys.stderr, "The bc nts coordinate MM **-**-**/MM-**-** must be in the set " + ",".join(x for x in bc_mapnums.items( ) ) + " on input record %d" % recnum
	return None, None

    if b1 < 1 or b1 > 16:
	print >> sys.stderr, "The bc nts coordinate MM **-**-**/**-MM-** must be in the range ['A','P']" + " on input record %d" % recnum
	return None, None
    if b2 < 1 or b2 > 16:
	print >> sys.stderr, "The bc nts coordinate MM **-**-**/**-**-MM must be in the range [1,16]" + " on input record %d" % recnum
	return None, None
    if b3 < 1 or b3 > 16:
	print >> sys.stderr, "The bc nts coordinate MM **-**-MM/**-**-** must be in the range ['A','L']" + " on input record %d" % recnum
	return None, None
    if b4 < 1 or b4 > 100:
	print >> sys.stderr, "The bc nts coordinate MM **-MM-**/**-**-** must be in the range [1,100]" + " on input record %d" % recnum
	return None, None
    if b5 < 1 or b5 > 4:
	print >> sys.stderr, "The bc nts coordinate MM MM-**-**/**-**-** must be in the range ['A','D']" + " on input record %d" % recnum
	return None, None

    lat, long = blocks.getLatLong( [b0, b1, b2, b3, b4, b5] )
    return lat, -long

'''
The following routine reads the input file, does the appropriate conversion,
and produces the output file.
'''
def convert( separator, replace_latlong, bmap, blocks ):

    columns = sys.stdin.readline( ).strip( ).split( separator )
    colnum = 0
    lat_col = None
    long_col = None
    in_col = None
    for col in columns:
	if col.lower() == "latitude" or col.lower() == "lat":
	    lat_col = colnum
	if col.lower() == "longitude" or col.lower() == "long":
	    long_col = colnum
	if col.lower() == "dls" or col.lower() == "location" or col.lower() == 'nts':
	    in_col = colnum
	colnum += 1

    if lat_col is None:
	sys.exit( "Input file must have a column titled 'latitude' or 'lat'" )
    if long_col is None:
	sys.exit( "Input file must have a column titled 'longitude' or 'long'" )
    if in_col is None:
	sys.exit( "Input file must have a column titled 'dls', 'nts', or 'location'" )
    print separator.join( columns )

    dls_re = re.compile( "^(\d+)-(\d+)-(\d+)-(\d+)W(\d+)$" )
    bcnts_re = re.compile( "^([A-Z])-(\d+)-([A-Z])/(\d+)-([A-Z])-(\d+)$" )

    recnum = 1
    for line in sys.stdin:
	recnum += 1
	line = line[:-1]
	fields = line.split( separator )
	outline = line
	if len( fields ) != len( columns ):
	    print >> sys.stderr, "Expected %d fields on record %d of input" % ( len( columns ), recnum )
	    exit( 1 )

	if replace_latlong or fields[lat_col] == "" or fields[long_col] == "":
	    dls = fields[in_col].strip( ).upper( )
	    match_dls = dls_re.match( dls )
	    match_bcnts = bcnts_re.match( dls )
	    lat = None
	    if match_dls:
		lsd, section, township, range, meridian = [ int(x) for x in match_dls.groups( ) ]
		lat, long = fromDLS( recnum, bmap,
				     lsd, section, township, range, meridian )
	    elif match_bcnts:
		( b4, b0, b2 ) = ( int(x) for x in match_bcnts.group( 2, 4, 6 ) )
		( b5, b3, b1 ) = ( ord(x)-ord("A")+1 for x in match_bcnts.group( 1, 3, 5 ) ) 
		lat, long = fromBCNTS( recnum, blocks, b0, b1, b2, b3, b4, b5 )
	    else:
		print >> sys.stderr, "Poorly formated dls or nts location '%s' on record %d of input" % ( dls, recnum )

	    if lat is None:
		fields[lat_col] = ""
		fields[long_col] = ""
	    else:
		fields[lat_col] = str(lat)
		fields[long_col] = str(long)
	    
	print separator.join( fields )
   



if __name__ == "__main__":

    from optparse import OptionParser

    description = \
"""
This script is used to translate Alberta/DLS or British Columbia NTS
coordinates into latitude and longitude.
"""

    parser = OptionParser( version="%prog 1.0", description = description )

    parser = OptionParser( version="%prog 1.0", description = description )
    parser.add_option( "-s", "--separator", dest="separator",
		       help="character used to separate columns (typically a comma or a tab" )
    parser.add_option( "-b", "--baselinemap", dest="baselinemap_name",
		       help="name of file containing baseline mappings" )
    parser.add_option( "-i", "--inputfile", dest="in_fname",
		       help="name of file containing input data to convert" )
    parser.add_option( "-o", "--outputfile", dest="out_fname",
		       help="name of file containing converted output data" )
    parser.add_option( "-r", "--replace", dest="replace",
		       action="store_true", default=False,
		       help="replace existing latitude/longitude values" )
    parser.add_option( "-e", "--errorfile", dest="err_fname",
		       help="name of file containing error messages" )

    parser.set_defaults( baselinemap_name="", separator=",",
			 in_fname="", out_fname="", err_fname="" )
    ( options, args ) = parser.parse_args( )
    if options.baselinemap_name == "":
	print >> sys.stderr, "Must specify name of the file containing the baseline map data."
	parser.print_help( )
	sys.exit( 2 )

    if options.in_fname != "":
	try:
	    in_file = open( options.in_fname )
	    sys.stdin = in_file
	except IOError, e:
	    sys.exit( "Error opening input file '%s': %s" % ( options.in_fname, e ) )
    if options.out_fname != "":
	try:
	    out_file = open( options.out_fname, "w" )
	    sys.stdout = out_file
	except IOError, e:
	    sys.exit( "Error opening output file '%s': %s" % ( options.out_fname, e ) )
    if options.err_fname != "":
	try:
	    err_file = open( options.err_fname, "w" )
	    sys.stderr = err_file
	except IOError, e:
	    sys.exit( "Error opening error message file '%s': %s" % ( options.err_fname, e ) )

    # Initialize for DLS
    bmap = BaselineMap( "\t", options.baselinemap_name )

    # Initialize for BC NTS
    blk5 = SinusoidalBlock( 2, 2 )
    blk4 = LRBlock( 10, 10 )
    blk3 = SinusoidalBlock( 3, 4 )
    blk2 = SinusoidalBlock( 4, 4 )
    blk1 = SinusoidalBlock( 4, 4 )
    blk0 = FirstBlock( 10, 12 )
    blk0.setSize( 40.0, 96.0 )
    blk0.addSubBlock( blk1 )
    blk1.addSubBlock( blk2 )
    blk2.addSubBlock( blk3 )
    blk3.addSubBlock( blk4 )
    blk4.addSubBlock( blk5 )

    convert( options.separator, options.replace, bmap, blk0 )
