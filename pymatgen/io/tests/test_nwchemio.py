#!/usr/bin/env python

"""
TODO: Modify module doc.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "6/6/13"


import unittest
import os
import json

from pymatgen.core.structure import Molecule
from pymatgen.io.nwchemio import NwTask, NwInput, NwInputError, NwOutput


test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        'test_files', "molecules")


coords = [[0.000000, 0.000000, 0.000000],
          [0.000000, 0.000000, 1.089000],
          [1.026719, 0.000000, -0.363000],
          [-0.513360, -0.889165, -0.363000],
          [-0.513360, 0.889165, -0.363000]]
mol = Molecule(["C", "H", "H", "H", "H"], coords)


class NwTaskTest(unittest.TestCase):

    def setUp(self):
        self.task = NwTask(0, 1, basis_set={"H": "6-31g"}, theory="dft",
                           theory_directives={"xc": "b3lyp"})

    def test_multi_bset(self):
        t = NwTask.from_molecule(
            mol, theory="dft", basis_set={"C": "6-311++G**",
                                          "H": "6-31++G**"},
            theory_directives={"xc": "b3lyp"})
        ans = """title "H4C1 dft optimize"
charge 0
basis
 H library "6-31++G**"
 C library "6-311++G**"
end
dft
 xc b3lyp
end
task dft optimize"""
        self.assertEqual(str(t), ans)

    def test_str_and_from_string(self):

        ans = """title "dft optimize"
charge 0
basis
 H library "6-31g"
end
dft
 xc b3lyp
end
task dft optimize"""
        self.assertEqual(str(self.task), ans)

    def test_to_from_dict(self):
        d = self.task.to_dict
        t = NwTask.from_dict(d)
        self.assertIsInstance(t, NwTask)

    def test_init(self):
        self.assertRaises(NwInputError, NwTask, 0, 1, {"H": "6-31g"},
                          theory="bad")
        self.assertRaises(NwInputError, NwTask, 0, 1, {"H": "6-31g"},
                          operation="bad")

    def test_dft_task(self):
        task = NwTask.dft_task(mol, charge=1, operation="energy")
        ans = """title "H4C1 dft energy"
charge 1
basis
 H library "6-31g"
 C library "6-31g"
end
dft
 xc b3lyp
 mult 2
end
task dft energy"""
        self.assertEqual(str(task), ans)


class NwInputTest(unittest.TestCase):

    def setUp(self):
        tasks = [
            NwTask.dft_task(mol, operation="optimize", xc="b3lyp",
                            basis_set="6-31++G*"),
            NwTask.dft_task(mol, operation="freq", xc="b3lyp",
                            basis_set="6-31++G*"),
            NwTask.dft_task(mol, operation="energy", xc="b3lyp",
                            basis_set="6-311++G**"),
            NwTask.dft_task(mol, charge=mol.charge + 1, operation="energy",
                            xc="b3lyp", basis_set="6-311++G**"),
            NwTask.dft_task(mol, charge=mol.charge - 1, operation="energy",
                            xc="b3lyp", basis_set="6-311++G**")
        ]
        self.nwi = NwInput(mol, tasks,
                           geometry_options=["units", "angstroms", "noautoz"])

    def test_str(self):
        ans = """geometry units angstroms noautoz
 C 0.0 0.0 0.0
 H 0.0 0.0 1.089
 H 1.026719 0.0 -0.363
 H -0.51336 -0.889165 -0.363
 H -0.51336 0.889165 -0.363
end

title "H4C1 dft optimize"
charge 0
basis
 H library "6-31++G*"
 C library "6-31++G*"
end
dft
 xc b3lyp
 mult 1
end
task dft optimize

title "H4C1 dft freq"
charge 0
basis
 H library "6-31++G*"
 C library "6-31++G*"
end
dft
 xc b3lyp
 mult 1
end
task dft freq

title "H4C1 dft energy"
charge 0
basis
 H library "6-311++G**"
 C library "6-311++G**"
end
dft
 xc b3lyp
 mult 1
end
task dft energy

title "H4C1 dft energy"
charge 1
basis
 H library "6-311++G**"
 C library "6-311++G**"
end
dft
 xc b3lyp
 mult 2
end
task dft energy

title "H4C1 dft energy"
charge -1
basis
 H library "6-311++G**"
 C library "6-311++G**"
end
dft
 xc b3lyp
 mult 2
end
task dft energy
"""
        self.assertEqual(str(self.nwi), ans)

    def test_to_from_dict(self):
        d = self.nwi.to_dict
        nwi = NwInput.from_dict(d)
        self.assertIsInstance(nwi, NwInput)
        #Ensure it is json-serializable.
        json.dumps(d)

    def test_from_string_and_file(self):
        nwi = NwInput.from_file(os.path.join(test_dir, "ch4.nw"))
        self.assertEqual(nwi.tasks[0].theory, "dft")
        self.assertEqual(nwi.tasks[0].basis_set["C"], "6-31++G*")
        self.assertEqual(nwi.tasks[-1].basis_set["C"], "6-311++G**")
        #Try a simplified input.
        str_inp = """start H4C1
geometry units angstroms
 C 0.0 0.0 0.0
 H 0.0 0.0 1.089
 H 1.026719 0.0 -0.363
 H -0.51336 -0.889165 -0.363
 H -0.51336 0.889165 -0.363
end

title "H4C1 dft optimize"
charge 0
basis
 H library "6-31++G*"
 C library "6-31++G*"
end
dft
 xc b3lyp
 mult 1
end
task scf optimize

title "H4C1 dft freq"
charge 0
task scf freq

title "H4C1 dft energy"
charge 0
basis
 H library "6-311++G**"
 C library "6-311++G**"
end
task dft energy

title "H4C1 dft energy"
charge 1
dft
 xc b3lyp
 mult 2
end
task dft energy

title "H4C1 dft energy"
charge -1
task dft energy
"""
        nwi = NwInput.from_string(str_inp)
        self.assertEqual(nwi.geometry_options, ['units', 'angstroms'])
        self.assertEqual(nwi.tasks[0].theory, "scf")
        self.assertEqual(nwi.tasks[0].basis_set["C"], "6-31++G*")
        self.assertEqual(nwi.tasks[-1].theory, "dft")
        self.assertEqual(nwi.tasks[-1].basis_set["C"], "6-311++G**")


class NwOutputTest(unittest.TestCase):

    def test_read(self):
        nwo = NwOutput(os.path.join(test_dir, "CH4.nwout"))

        self.assertEqual(0, nwo.data[0]["charge"])
        self.assertEqual(-1, nwo.data[-1]["charge"])
        self.assertAlmostEqual(-1102.622361621359, nwo.data[0]["energies"][-1])
        self.assertAlmostEqual(-1102.9985415777337, nwo.data[2]["energies"][-1])
        ie = (nwo.data[4]["energies"][-1] - nwo.data[2]["energies"][-1])
        ea = (nwo.data[2]["energies"][-1] - nwo.data[3]["energies"][-1])
        self.assertAlmostEqual(0.7575358046858582, ie)
        self.assertAlmostEqual(-14.997876767843081, ea)
        self.assertEqual(nwo.data[4]["basis_set"]["C"]["description"],
                         "6-311++G**")

        nwo = NwOutput(os.path.join(test_dir, "H4C3O3_1.nwout"))
        self.assertTrue(nwo.data[-1]["has_error"])
        self.assertEqual(nwo.data[-1]["errors"][0], "Bad convergence")

        nwo = NwOutput(os.path.join(test_dir, "C1N1Cl1_1.nwout"))
        self.assertTrue(nwo.data[-1]["has_error"])
        self.assertEqual(nwo.data[-1]["errors"][0], "autoz error")


if __name__ == "__main__":
    unittest.main()
