import sys
from div3lib import modify_sky

# call signature: modify_sky night name number op value
# example: python modify_sky.py n3 ngc3169 15 + 0.5
# which means to increase the scaling of the sky subtracted from 
# spectrum 15 of ngc3169 from night three by 0.5

modify_sky(*sys.argv[1:])
