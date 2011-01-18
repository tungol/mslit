import os
import div3lib

def main():
	os.chdir('../n3')
	ngc3169 = div3lib.GalaxyClass('ngc3169')
	ngc3169.name = 'NGC 3169'
	ngc3169.redshift = 0.004130
	ngc3169.center = '10:14:15.0 +03:27:58'
	ngc3169.distance = 20100 #kpc
	ngc3169.r25 = 11.57 #kpc
	ngc3169.type = 'Sa'
	ngc3169.bar = 'A'
	ngc3169.ring = 's'
	ngc3169.env = 'pair'
	
	ngc4725 = div3lib.GalaxyClass('ngc4725')
	ngc4725.name = 'NGC 4725'
	ngc4725.redshift = 0.004023
	ngc4725.center = '12:50:26.6 +25:30:03'
	ngc4725.distance = 13918 #kpc
	ngc4725.r25 = 26.23 #kpc
	ngc4725.type = 'Sab'
	ngc4725.bar = 'AB'
	ngc4725.ring = 'r'
	ngc4725.env = 'pair'
	
	galaxies = [ngc3169, ngc4725]
	other_data = div3lib.get_other()
	
	for galaxy in galaxies:
		galaxy.run()
		galaxy.fit_OH()
		galaxy.output_tables()
		galaxy.output_graphs()
	
	for galaxy in other_data:
		galaxy.fit_OH()
			
	div3lib.compare_basic(galaxies, other_data)
	div3lib.compare_type(galaxies, other_data)
	div3lib.compare_bar(galaxies, other_data)
	div3lib.compare_ring(galaxies, other_data)
	div3lib.compare_env(galaxies, other_data)
	div3lib.make_comparison_table(galaxies, other_data)
	div3lib.compare_type_table(galaxies, other_data)
	div3lib.compare_bar_table(galaxies, other_data)
	div3lib.compare_ring_table(galaxies, other_data)
	div3lib.compare_env_table(galaxies, other_data)
	

main()
