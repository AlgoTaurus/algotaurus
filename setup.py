# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from nvpy import nvpy

setup(name='algotaurus',
      version='1.2b0',
      license='GNU3',
      description='An educational game to teach programming.',
      long_description='Write a program to make the AlgoTaurus find the exit.',
      url='http://github.com/AlgoTaurus/algotaurus',
      download_url='http://sourceforge.net/projects/algotaurus/',
      author = 'Attila Krajcsi and Ádám Markója',
      author_email = 'markoja.adam@cogsci.bme.hu',
      py_modules=['algotaurus','appdirs'],      
      data_files=[('share/applications/', ['algotaurus.desktop'])],
      entry_points = {'gui_scripts' : ['algotaurus = algotaurus.algotaurus:AlgoTaurusGui']},
      packages=['algotaurus'],	  
      package_dir={'algotaurus':'algotaurus'},
      include_package_data=True,
      install_requires=['numpy'],
	  classifiers=[
			# "Development Status :: 1 - Planning",
			# "Development Status :: 2 - Pre-Alpha",
			# "Development Status :: 3 - Alpha",
			# "Development Status :: 4 - Beta",
			"Development Status :: 5 - Production/Stable",
			# "Development Status :: 6 - Mature",
			# "Development Status :: 7 - Inactive",
			"Intended Audience :: Education"
			"Intended Audience :: End Users/Desktop"
			"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
			"Operating System :: OS Independent",
			"Operating System :: POSIX :: Linux",
			"Operating System :: Microsoft :: Windows",
			"Programming Language :: Python",
			"Programming Language :: Python :: 2",
			"Programming Language :: Python :: 2.6",
			"Programming Language :: Python :: 2.7",
		  	"Topic :: Education",
		  	"Topic :: Games/Entertainment",
      ]
      )
