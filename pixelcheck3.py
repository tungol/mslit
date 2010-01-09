from pixelcheck1 import get_pixels
import sys

def main(one, two):
	pixels1 = get_pixels(one)
	pixels2 = get_pixels(two)
	print len(pixels1)
	print len(pixels2)
	for i, count in enumerate(pixels1):
		print i, (count / pixels2[i])

main(sys.argv[1], sys.argv[2])
