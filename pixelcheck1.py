import simplejson as json
import os, sys

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

def get_pixels(fn):
	file = open(fn, 'r')
	diff = []
	for line in file:
		if line[0] == '#':
			pass
		else:
			tmp = line.split('-')
			start = float(tmp[0].strip())
			end = float(tmp[1].strip())
			diff.append(end - start)
	return diff

def get_mask(fn):
	file = open(fn, 'r')
	mask = file.readlines()
	file.close()
	mask = mask[2:]
	diff = []
	for line in mask:
		line = line.split()
		low = float(line[4])
		high = float(line[5])
		diff.append(high - low)
	diff.reverse()
	return diff

def main(cood_fn, mask_fn):
	pixels = get_pixels(cood_fn)
	mask = get_mask(mask_fn)
	if len(mask) >= len(pixels):
		for i in range(len(mask)):
			print "row %s:" % (i+1)
			try:
				print '%s inches, %s pixels, %s pixels per inch' % (mask[i], pixels[i], pixels[i] / mask[i])
			except:
				print '%s inches, no pixels' % mask[i]
	else:
		 for i in range(len(pixels)):
			print "row %s:" % (i+1)
			try:
				print '%s inches, %s pixels, %s pixels per inch'% (mask[i], pixels[i], pixels[i] / mask[i])
			except:
				print 'no inches, %s pixels' % pixels[i]

if __name__ == '__main__':
	main(sys.argv[1], sys.argv[2])
