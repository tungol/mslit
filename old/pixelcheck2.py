import simplejson as json
import os, sys

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

def get_pixels(fn):
	file = open(fn, 'r')
	cood = json.load(file)
	file.close()
	columns = cood.keys()
	list1 = cood[columns[0]]
	list2 = cood[columns[1]]
	diff = []
	for i in range(len(list1)):
		start1 = list1[i]['start']
		end1 = list1[i]['end']
		start2 = list2[i]['start']
		end2 = list2[i]['end']
		start = avg(start1, start2)
		end = avg(end1, end2)
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
