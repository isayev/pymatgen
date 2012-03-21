#!/usr/bin/env python

"""
This module provides classes to define everything related to band structures.
"""

import numpy as np
import math
import pymatgen.core.lattice


__author__ = "Geoffroy Hautier, Shyue Ping Ong, Michael Kocher"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "1.0"
__maintainer__ = "Geoffroy Hautier"
__email__ = "geoffroy@uclouvain.be"
__status__ = "Development"
__date__ = "March 14, 2012"


class Kpoint(object):

    """
    class to store kpoint objects
    a kpoint is defined with a lattice and frac or cartesian coordinates
    syntax similar than the site object in pymatgen.core.structure
    """

    def __init__(self, coords, lattice, to_unit_cell = False, coords_are_cartesian = False, label = None):
        self._lattice = lattice
        self._fcoords = lattice.get_fractional_coords(coords) if coords_are_cartesian else coords
        self._label = label

        if to_unit_cell:
            for i in xrange(len(self._fcoords)):
                self._fcoords[i] = self._fcoords[i] - math.floor(self._fcoords[i])

        self._ccoords = lattice.get_cartesian_coords(self._fcoords)

    @property
    def lattice(self):
        """
        The lattice associated with the site.
        """
        return self._lattice

    @property
    def label(self):
        """
        The lattice associated with the site.
        """
        return self._label

    @property
    def frac_coords(self):
        """
        The fractional coordinates of the site as a tuple.
        """
        return np.copy(self._fcoords)

    @property
    def cart_coords(self):
        """
        The cartesian coordinates
        """
        return np.copy(self._ccoords)

    @property
    def a(self):
        """
        Fractional a coordinate
        """
        return self._fcoords[0]

    @property
    def b(self):
        """
        Fractional b coordinate
        """
        return self._fcoords[1]

    @property
    def c(self):
        """
        Fractional c coordinate
        """
        return self._fcoords[2]

    def __str__(self):
        return str(self.frac_coords) + " " + str(self.cart_coords) + " " + str(self.label)

    @property
    def to_dict(self):
        return {'lattice':self.lattice.to_dict, 'fcoords':list(self.frac_coords), 'ccoords':list(self.cart_coords), 'label':self.label}

class BandStructure(object):

    """
    This is the most generic band structure data possible
    it's defined by a list of kpoints + energy and occupancies for each of them
    """

    def __init__(self, kpoints, eigenvals, lattice, efermi, labels_dict = {}, coords_are_cartesian = False):
        """
        Args: 
            kpoints: (Array) of kpoint as numpy arrays, in frac_coords of the lattice given by default

            eigenvals: (Array) of {} with energy and occup keys each element of the array is one "band"

            label_dict: (dict) of {} this link a kpoint (in frac coords or cartesian coordinates depending on the coords
            are cartesian tag) with a label

            lattice: Materials Project Structure object

            efermi: fermi energy in eV
        """


        self._efermi = efermi

        #self._structure = structure
        self._lattice_rec = lattice

        self._kpoints = []
        """
        all kpoints, (order matter!)
        """
        self._labels_dict = {}
        """
        label to each kpoint (with kpoint objects.to_dict)
        """
        for k in kpoints:
            #let see if this kpoint has been assigned a label
            label = None
            for c in labels_dict:
                if(np.linalg.norm(k - np.array(labels_dict[c])) < 0.0001):
                    label = c
                    self._labels_dict[label] = Kpoint(k, lattice, label = label, coords_are_cartesian = coords_are_cartesian)
            self._kpoints.append(Kpoint(k, lattice, label = label, coords_are_cartesian = coords_are_cartesian))

        self._bands = eigenvals
        """
        all energy values for each band at the different kpoints
        """
        self._nb_bands = len(eigenvals)
        """
        the number of bands
        """

    @property
    def kpoints(self):
        """
        return the list of kpoints (as kpoint objects) in the band structure
        """
        return self._kpoints

    @property
    def lattice(self):
        """
        return the lattice of the band structure as a lattice object
        """
        return self._lattice_rec

    @property
    def efermi(self):
        """
        return the fermi energy
        """
        return self._efermi

class BandStructureSymmLine(BandStructure):

    """
    This object stores band structures along selected (symmetry) lines in the Brillouin zone
    """

    def __init__(self, kpoints, eigenvals, lattice, efermi, labels_dict, coords_are_cartesian = False):
        super(BandStructureSymmLine, self).__init__(kpoints, eigenvals, lattice, efermi, labels_dict, coords_are_cartesian)
        self._distance = []
        self._branches = []
        """
        all branches labels (ex: Gamma-Z, etc...)
        """
        one_group = []
        branches_tmp = []
        #get labels and distance for each kpoint
        previous_kpoint = self._kpoints[0]
        previous_distance = 0.0

        previous_label = self._kpoints[0].label
        for i in range(len(self._kpoints)):
            label = self._kpoints[i].label
            if label != None and previous_label != None:
                self._distance.append(previous_distance)
            else:
                self._distance.append(np.linalg.norm(self._kpoints[i].cart_coords - previous_kpoint.cart_coords) + previous_distance)
            previous_kpoint = self._kpoints[i]
            previous_distance = self._distance[i]
            if label != None:
                if previous_label != None:
                    if len(one_group) != 0:
                        branches_tmp.append(one_group)
                    one_group = []
            previous_label = label
            one_group.append(i)

        if len(one_group) != 0:
            branches_tmp.append(one_group)
        #self._branches=branches
        for b in branches_tmp:
            self._branches.append({'start_index':b[0], 'end_index':b[-1], 'name':(self._kpoints[b[0]].label + "-" + self._kpoints[b[-1]].label)})




    def get_branch_name(self, index):
        to_return = []
        for b in self._branches:
                if(b['start_index'] <= index <= b['end_index']):
                    to_return.append(b['name'])
        return to_return

    def get_vbm(self):
        """
        get the valence band minimum (VBM). returns a dictionary with
        'band_index': a list of the indices of the band containing the VBM (please note that you can have several bands 
        sharing the VBM)
        'kpoint_index': the index in self._kpoints of the kpoint vbm
        'kpoint': the kpoint (as a kpoint object)
        'energy': the energy of the VBM
        'label': the label of the vbm kpoint if any
        """
        max_tmp = -1000.0
        index = None
        for i in range(self._nb_bands):
            for j in range(len(self._kpoints)):
                if(self._bands[i]['energy'][j] < self._efermi):
                    if(self._bands[i]['energy'][j] > max_tmp):
                        max_tmp = self._bands[i]['energy'][j]
                        index = j
                        kpointvbm = self._kpoints[j]
        #get all other bands sharing the vbm
        list_index_band = []
        for i in range(self._nb_bands):
            if(math.fabs(self._bands[i]['energy'][index] - max_tmp) < 0.001):
                list_index_band.append(i)
        return {'band_index':list_index_band, 'kpoint_index':index, 'kpoint':kpointvbm, 'energy':max_tmp}


    def get_cbm(self):
        """
        get the conduction band minimum (CBM). returns a dictionnary with
        'band_index': a list of the indices of the band containing the CBM (please note that you can have several bands 
        sharing the CBM)
        'kpoint_index': the index in self._kpoints of the kpoint cbm
        'kpoint': the kpoint (as kpoint object)
        'energy': the energy of the CBM
        'label': the label of the cbm kpoint if any
        """
        max_tmp = 1000.0
        index = None
        for i in range(self._nb_bands):
            for j in range(len(self._kpoints)):
                if(self._bands[i]['energy'][j] > self._efermi):
                    if(self._bands[i]['energy'][j] < max_tmp):
                        max_tmp = self._bands[i]['energy'][j]
                        index = j
                        kpointvbm = self._kpoints[j]
        #get all other bands sharing the vbm
        list_index_band = []
        for i in range(self._nb_bands):
            if(math.fabs(self._bands[i]['energy'][index] - max_tmp) < 0.001):
                list_index_band.append(i)
        return {'band_index':list_index_band, 'kpoint_index':index, 'kpoint':kpointvbm, 'energy':max_tmp}

    def get_band_gap(self):
        """
        get the band gap 
        returns a dictionary with:
        'energy': the band gap energy in eV
        'direct': a boolean telling if the gap is direct (True) or not (False)
        'transition': the kpoint labels of the transition (e.g., \Gamma to X)
        
        TODO: not sure if the direct works, to test!
        
        """
        if self.is_metal():
            return {'energy':0.0, 'direct':False, 'transition':None}
        cbm = self.get_cbm()
        vbm = self.get_vbm()
        result = {}
        result['energy'] = cbm['energy'] - vbm['energy']
        result['direct'] = False
        if (cbm['kpoint'].label == vbm['kpoint'].label or np.linalg.norm(cbm['kpoint'].cart_coords - vbm['kpoint'].cart_coords) < 0.01):
            result['direct'] = True
        result['transition'] = '-'.join([str(c.label) for c in [vbm['kpoint'], cbm['kpoint']]])
        return result


    def is_metal(self):
        """
        check if the band structure indicates a metal by looking if the fermi level crosses a band
        
        """
        for i in range(self._nb_bands):
            below = False
            above = False
            for j in range(len(self._kpoints)):
                if self._bands[i]['energy'][j] < self._efermi:
                    below = True
                if self._bands[i]['energy'][j] > self._efermi:
                    above = True
            if above and below:
                return True
        return False

    @property
    def to_dict(self):
        dictio = {}
        dictio['lattice_rec'] = self._lattice_rec.to_dict
        dictio['efermi'] = self._efermi
        dictio['kpoints'] = []
        #kpoints are not kpoint objects dicts but are frac coords (this makes the dict
        #smaller and avoids the repetition of the lattice
        for k in self._kpoints:
            dictio['kpoints'].append(k.to_dict['fcoords'])
        dictio['branches'] = self._branches
        dictio['bands'] = self._bands
        dictio['is_metal'] = self.is_metal()
        dictio['VBM'] = self.get_cbm()['kpoint'].to_dict
        dictio['CBM'] = self.get_vbm()['kpoint'].to_dict
        dictio['band_gap'] = self.get_band_gap()
        dictio['labels_dict'] = {}
        for c in self._labels_dict:
            dictio['labels_dict'][c] = self._labels_dict[c].to_dict['fcoords']
        return dictio

    @staticmethod
    def from_dict(dictio):
        #dictio=dictio['band_structure']
        labels_dict = dictio['labels_dict']
        return BandStructureSymmLine(dictio['kpoints'], dictio['bands'], pymatgen.core.lattice.Lattice.from_dict(dictio['lattice_rec']), dictio['efermi'], labels_dict)



def get_reconstructed_band_structure(list_bs, efermi):
        """
        this method takes a list of band structure (divided by branches)
        and reconstruct one band structure object from all of them
        """
        if not efermi:
            efermi = sum([b.efermi for b in list_bs]) / len(list_bs)
        kpoints = []
        eigenvals = []
        labels_dict = {}
        rec_lattice = list_bs[0]._lattice_rec
        #lattice=list_bs[0]._lattice
        #efermi=list_bs[0]._efermi
        nb_bands = list_bs[0]._nb_bands
        for bs in list_bs:
            for k in bs._kpoints:
                kpoints.append(k.frac_coords)
            for k, v in bs._labels_dict.iteritems():
                labels_dict[k] = v.frac_coords
            #eigenvals.append({'energy':[0,6.0],'occup':[1.0,1.0]})
        for i in range(nb_bands):
            eigenvals.append({'energy':[], 'occup':[]})
            for bs in list_bs:
                for e in bs._bands[i]['energy']:
                    eigenvals[i]['energy'].append(e)
                for u in bs._bands[i]['occup']:
                    eigenvals[i]['occup'].append(u)
        return BandStructureSymmLine(kpoints, eigenvals, rec_lattice, efermi, labels_dict)