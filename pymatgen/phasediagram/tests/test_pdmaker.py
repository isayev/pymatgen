import unittest
import os

from pymatgen import Element, Composition
from pymatgen.phasediagram.entries import PDEntryIO
from pymatgen.phasediagram.pdmaker import PhaseDiagram, \
    GrandPotentialPhaseDiagram, CompoundPhaseDiagram, PhaseDiagramError


class PhaseDiagramTest(unittest.TestCase):

    def setUp(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        (self.elements, self.entries) = \
            PDEntryIO.from_csv(os.path.join(module_dir, "pdentries_test.csv"))
        self.pd = PhaseDiagram(self.entries)

    def test_init(self):
        #Ensure that a bad set of entries raises a PD error. Remove all Li
        #from self.entries.
        entries = filter(lambda e: (not e.composition.is_element) or
                         e.composition.elements[0] != Element("Li"),
                         self.entries)
        self.assertRaises(PhaseDiagramError, PhaseDiagram, entries,
                          self.elements)

    def test_stable_entries(self):
        stable_formulas = [ent.composition.reduced_formula
                           for ent in self.pd.stable_entries]
        expected_stable = ["Fe2O3", "Li5FeO4", "LiFeO2", "Fe3O4", "Li", "Fe",
                           "Li2O", "O2", "FeO"]
        for formula in expected_stable:
            self.assertTrue(formula in stable_formulas,
                            formula + " not in stable entries!")

    def test_get_formation_energy(self):
        stable_formation_energies = {ent.composition.reduced_formula:
                                     self.pd.get_form_energy(ent)
                                     for ent in self.pd.stable_entries}
        expected_formation_energies = {'Li5FeO4': -164.8117344866667,
                                       'Li2O2': -14.119232793333332,
                                       'Fe2O3': -16.574164339999996,
                                       'FeO': -5.7141519966666685, 'Li': 0.0,
                                       'LiFeO2': -7.732752316666666,
                                       'Li2O': -6.229303868333332,
                                       'Fe': 0.0, 'Fe3O4': -22.565714456666683,
                                       'Li2FeO3': -45.67166036000002,
                                       'O2': 0.0}
        for formula, energy in expected_formation_energies.items():
            self.assertAlmostEqual(energy, stable_formation_energies[formula],
                                   7)
    def test_all_entries_hulldata(self):
        self.assertEqual(len(self.pd.all_entries_hulldata), 492)

    def test_str(self):
        self.assertIsNotNone(str(self.pd))


class GrandPotentialPhaseDiagramTest(unittest.TestCase):

    def setUp(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        (self.elements, self.entries) = PDEntryIO.from_csv(
            os.path.join(module_dir, "pdentries_test.csv"))
        self.pd = GrandPotentialPhaseDiagram(self.entries, {Element("O"): -5},
                                             self.elements)
        self.pd6 = GrandPotentialPhaseDiagram(self.entries, {Element("O"): -6})

    def test_stable_entries(self):
        stable_formulas = [ent.original_entry.composition.reduced_formula
                           for ent in self.pd.stable_entries]
        expected_stable = ['Li5FeO4', 'Li2FeO3', 'LiFeO2', 'Fe2O3', 'Li2O2']
        for formula in expected_stable:
            self.assertTrue(formula in stable_formulas, formula +
                            " not in stable entries!")
        self.assertEqual(len(self.pd6.stable_entries), 4)

    def test_get_formation_energy(self):
        stable_formation_energies = {
            ent.original_entry.composition.reduced_formula:
            self.pd.get_form_energy(ent)
            for ent in self.pd.stable_entries}
        expected_formation_energies = {'Fe2O3': 0.0,
                                       'Li5FeO4': -5.305515040000046,
                                       'Li2FeO3': -2.3424741500000152,
                                       'LiFeO2': -0.43026396250000154,
                                       'Li2O2': 0.0}
        for formula, energy in expected_formation_energies.items():
            self.assertAlmostEqual(energy, stable_formation_energies[formula],
                                   7, "Calculated formation for " +
                                   formula + " is not correct!")

    def test_str(self):
        self.assertIsNotNone(str(self.pd))


class CompoundPhaseDiagramTest(unittest.TestCase):

    def setUp(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        (self.elements, self.entries) = PDEntryIO.from_csv(
            os.path.join(module_dir, "pdentries_test.csv"))
        self.pd = CompoundPhaseDiagram(self.entries, [Composition("Li2O"),
                                                      Composition("Fe2O3")])

    def test_stable_entries(self):
        stable_formulas = [ent.name for ent in self.pd.stable_entries]
        expected_stable = ["Fe2O3", "Li5FeO4", "LiFeO2", "Li2O"]
        for formula in expected_stable:
            self.assertTrue(formula in stable_formulas)

    def test_get_formation_energy(self):
        stable_formation_energies = {ent.name:
                                     self.pd.get_form_energy(ent)
                                     for ent in self.pd.stable_entries}
        expected_formation_energies = {'Li5FeO4': -7.0773284399999739,
                                       'Fe2O3': 0,
                                       'LiFeO2': -0.47455929750000081,
                                       'Li2O': 0}
        for formula, energy in expected_formation_energies.items():
            self.assertAlmostEqual(energy, stable_formation_energies[formula],
                                   7)

    def test_str(self):
        self.assertIsNotNone(str(self.pd))


if __name__ == '__main__':
    unittest.main()
