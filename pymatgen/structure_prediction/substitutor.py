#!/usr/bin/env python

"""
This module provides classes for predicting new structures from existing ones.
"""

from __future__ import division

__author__ = "Will Richards, Geoffroy Hautier"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "1.2"
__maintainer__ = "Will Richards"
__email__ = "wrichard@mit.edu"
__date__ = "Aug 31, 2012"

from pymatgen.serializers.json_coders import MSONable
from pymatgen.structure_prediction.substitution_probability \
    import SubstitutionProbability
from pymatgen.transformations.standard_transformations \
    import SubstitutionTransformation
from pymatgen.alchemy.transmuters import StandardTransmuter
from pymatgen.alchemy.materials import TransformedStructure
from pymatgen.alchemy.filters import RemoveDuplicatesFilter
import itertools
import logging
from operator import mul


class Substitutor(MSONable):
    """
    This object uses a data mined ionic substitution approach to propose
    compounds likely to be stable. It relies on an algorithm presented in
    Hautier, G., Fischer, C., Ehrlacher, V., Jain, A., and Ceder, G. (2011).
    Data Mined Ionic Substitutions for the Discovery of New Compounds.
    Inorganic Chemistry, 50(2), 656-663. doi:10.1021/ic102031h
    """

    def __init__(self, threshold=1e-3, **kwargs):
        """
        This substitutor uses the substitution probability class to
        find good substitutions for a given chemistry or structure.

        Args:
            threshold:
                probability threshold for predictions
            kwargs:
                kwargs for the SubstitutionProbability object
                lambda_table, alpha
        """
        self._kwargs = kwargs
        self._sp = SubstitutionProbability(**kwargs)
        self._threshold = threshold

    def get_allowed_species(self):
        """
        returns the species in the domain of the probability function
        any other specie will not work
        """
        return self._sp.species_list

    def pred_from_structures(self, target_species, structures_list,
                             remove_duplicates=True):
        """
        performs a structure prediction targeting compounds containing the
        target_species and based on a list of structure (those structures
        can for instance come from a database like the ICSD). It will return
        all the structures formed by ionic substitutions with a probability
        higher than the threshold

        Args:
            target_species:
                a list of species with oxidation states
                e.g., [Specie('Li',1),Specie('Ni',2), Specie('O',-2)]

            structures_list:
                a list of dictionnary of the form {'structure':Structure object
                ,'id':some id where it comes from}
                the id can for instance refer to an ICSD id

        Returns:
            a list of TransformedStructure objects.
        """
        result = []
        transmuter = StandardTransmuter([])
        if len(list(set(target_species) & set(self.get_allowed_species()))) \
                != len(target_species):
            return ValueError("the species in target_species are not allowed"
                              + "for the probability model you are using")

        for permut in itertools.permutations(target_species):
            for s in structures_list:
                #check if: species are in the domain,
                #and the probability of subst. is above the threshold
                els = s['structure'].composition.elements
                if len(list(set(els) & set(self.get_allowed_species()))) == \
                        len(els) and self._sp.cond_prob_list(permut, els) > \
                        self._threshold:
                    transf = SubstitutionTransformation(
                        {els[i]: permut[i]
                         for i in xrange(0, len(els))
                         if els[i] != permut[i]})

                    if Substitutor._is_charge_balanced(
                            transf.apply_transformation(s['structure'])):
                        ts = TransformedStructure(
                            s['structure'], [transf], history=[s['id']],
                            other_parameters={
                                'type': 'structure_prediction',
                                'proba': self._sp.cond_prob_list(permut, els)}
                        )
                        result.append(ts)
                        transmuter.append_transformed_structures([ts])
        if remove_duplicates:
            transmuter.apply_filter(RemoveDuplicatesFilter())
        return transmuter.transformed_structures

    @staticmethod
    def _is_charge_balanced(struct):
        """
        checks if the structure object is charge balanced
        """
        if sum([s.specie. oxi_state for s in struct.sites]) == 0.0:
            return True
        else:
            return False

    def pred_from_list(self, species_list):
        """
        There are an exceptionally large number of substitutions to
        look at (260^n), where n is the number of species in the
        list. We need a more efficient than brute force way of going
        through these possibilities. The brute force method would be::

            output = []
            for p in itertools.product(self._sp.species_list
                                       , repeat = len(species_list)):
                if self._sp.conditional_probability_list(p, species_list)
                                       > self._threshold:
                    output.append(dict(zip(species_list,p)))
            return output

        Instead of that we do a branch and bound.

        Args:
            species_list:
                list of species in the starting structure

        Returns:
            list of dictionaries, each including a substitutions
            dictionary, and a probability value
        """
        #calculate the highest probabilities to help us stop the recursion
        max_probabilities = []
        for s2 in species_list:
            max_p = 0
            for s1 in self._sp.species_list:
                max_p = max([self._sp.cond_prob(s1, s2), max_p])
            max_probabilities.append(max_p)
        output = []

        def _recurse(output_prob, output_species):
            best_case_prob = list(max_probabilities)
            best_case_prob[:len(output_prob)] = output_prob
            if reduce(mul, best_case_prob) > self._threshold:
                if len(output_species) == len(species_list):
                    odict = {
                        'substitutions':
                        dict(zip(species_list, output_species)),
                        'probability': reduce(mul, best_case_prob)}
                    output.append(odict)
                    return
                for sp in self._sp.species_list:
                    i = len(output_prob)
                    prob = self._sp.cond_prob(sp, species_list[i])
                    _recurse(output_prob + [prob], output_species + [sp])

        _recurse([], [])
        logging.info('{} substitutions found'.format(len(output)))
        return output

    def pred_from_comp(self, composition):
        """
        Similar to pred_from_list except this method returns a list after
        checking that compositions are charge balanced.
        """
        output = []
        predictions = self.pred_from_list(composition.elements)
        for p in predictions:
            subs = p['substitutions']
            charge = 0
            for i_el in composition.elements:
                f_el = subs[i_el]
                charge += f_el.oxi_state * composition[i_el]
            if charge == 0:
                output.append(p)
        logging.info('{} charge balanced '
                     'compositions found'.format(len(output)))
        return output

    @property
    def to_dict(self):
        return {"name": self.__class__.__name__, "version": __version__,
                "kwargs": self._kwargs, "threshold": self._threshold,
                "@module": self.__class__.__module__,
                "@class": self.__class__.__name__}

    @staticmethod
    def from_dict(d):
        t = d['threshold']
        kwargs = d['kwargs']
        return Substitutor(threshold=t, **kwargs)