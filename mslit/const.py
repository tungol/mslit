#!/usr/bin/env python
# encoding: utf-8

"""
Some useful values.

This file contains some useful values, all used during analyzing data.
"""

LOG_FORMAT = ('center', 'cont', 'flux', 'eqw', 'core', 'gfwhm', 'lfwhm')

LINES = {'OII': 3727, 'hgamma': 4341, 'hbeta': 4861, 'OIII1': 4959,
         'OIII2': 5007, 'NII1': 6548, 'halpha': 6563, 'NII2': 6583,
         'SII1': 6717, 'SII2': 6731, 'OIII3': 4363}

LOOKUP = {'OII': '[O II]$\lambda3727$', 'hgamma': 'H$\gamma$',
          'hbeta': 'H$\\beta$', 'OIII1': '[O III]$\lambda4959$',
          'OIII2': '[O III]$\lambda5007$', 'NII1': '[N II]$\lambda6548$',
          'halpha': 'H$\\alpha$', 'NII2': '[N II]$\lambda6583$',
          'SII1': '[S II]$\lambda6717$', 'SII2': '[S II]$\lambda6731$',
          'OIII3': '[O III]$\lambda4363$',
          'OH': '$12 + \log{\\textnormal{O/H}}$',
          'SFR': 'SFR(M$_\odot$ / year)', 'rdistance': 'Radial Distance (kpc)',
          'extinction': 'E(B - V)', 'r23': '$R_{23}$'}

GROUPS = {'env': [{'name': 'Isolated', 'members': ('isolated',)},
                  {'name': 'Group', 'members': ('group',)},
                  {'name': 'Pair', 'members': ('pair',)}],
          'ring': [{'name': 'S-Shaped', 'members': ('s',)},
                   {'name': 'Intermediate Type', 'members': ('rs',)},
                   {'name': 'Ringed', 'members': ('r',)}],
          'bar': [{'name': 'No Bar', 'members': ('A',)},
                  {'name': 'Weakly Barred', 'members': ('AB',)},
                  {'name': 'Strongly Barred', 'members': ('B',)}],
          'type': [{'name': 'Sa and Sab', 'members': ('Sa', 'Sab')},
                   {'name': 'Sb and Sbc', 'members': ('Sb', 'Sbc')},
                   {'name': 'Sc and Scd', 'members': ('Sc', 'Scd')},
                   {'name': 'Sd', 'members': ('Sd', 'Irr')}]}
