"Factory functions producing ABINIT workflows. Entry points for client code (high-level interface)"
from __future__ import division, print_function

import os

from pymatgen.io.abinitio.abiobjects import Smearing, KSampling, Screening, \
    SelfEnergy, ExcHamiltonian
from pymatgen.io.abinitio.strategies import ScfStrategy, NscfStrategy, \
    ScreeningStrategy, SelfEnergyStrategy, MDFBSE_Strategy
from pymatgen.io.abinitio.workflow import PseudoIterativeConvergence, \
    PseudoConvergence, BandStructure, GW_Workflow, BSEMDF_Workflow

__author__ = "Matteo Giantomassi"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Matteo Giantomassi"
__email__ = "gmatteo at gmail.com"


################################################################################

class PPConvergenceFactory(object):
    """Factory object"""

    def work_for_pseudo(self, workdir, pseudo, ecut_range, runmode="sequential",
                        atols_mev=(10, 1, 0.1), spin_mode="polarized",
                        acell=(8, 9, 10), smearing="fermi_dirac:0.1 eV",):
        """
        Return a Work object given the pseudopotential pseudo.

        Args:
            workdir:
                Working directory.
            pseudo:
                Pseudo object.
            ecut_range:
                range of cutoff energies in Ha units.
            runmode:
                Run mode.
            atols_mev:
                Tolerances in meV for accuracy in ["low", "normal", "high"]
            spin_mode:
                Spin polarization.
            acell:
                Length of the real space lattice (Bohr units)
            smearing:
                Smearing technique.
        """
        workdir = os.path.abspath(workdir)

        smearing = Smearing.assmearing(smearing)

        if isinstance(ecut_range, slice):
            workflow = PseudoIterativeConvergence(
                workdir, pseudo, ecut_range, atols_mev, runmode=runmode,
                spin_mode=spin_mode, acell=acell, smearing=smearing)

        else:
            workflow = PseudoConvergence(
                workdir, pseudo, ecut_range, atols_mev, runmode=runmode,
                spin_mode=spin_mode, acell=acell, smearing=smearing)

        return workflow

################################################################################


def bandstructure(workdir, runmode, structure, pseudos, scf_kppa, nscf_nband,
                  ndivsm, accuracy="normal", spin_mode="polarized",
                  smearing="fermi_dirac:0.1 eV", charge=0.0, scf_solver=None,
                  dos_kppa=None):
    """
    Returns a Work object that computes that bandstructure of the material.

    Args:
        workdir:
            Working directory.
        runmode:
            `RunMode` instance.
        structure:
            Pymatgen structure.
        pseudos:
            List of `Pseudo` objects.
        scf_kppa:
            Defines the sampling used for the SCF run.
        nscf_nband:
            Number of bands included in the NSCF run.
        ndivs:
            Number of divisions used to sample the smallest segment of the k-path.
        accuracy:
            Accuracy of the calculation.
        spin_mode:
            Spin polarization.
        smearing:
            Smearing technique.
        charge:
            Electronic charge added to the unit cell.
        scf_solver:
            Algorithm used for solving of the SCF cycle.
        dos_kppa
            Defines the k-point sampling used for the computation of the DOS 
            (None if DOS is not wanted).
    """
    scf_ksampling = KSampling.automatic_density(structure, scf_kppa,
                                                chksymbreak=0)

    scf_strategy = ScfStrategy(structure, pseudos, scf_ksampling,
                               accuracy=accuracy, spin_mode=spin_mode,
                               smearing=smearing, charge=charge,
                               scf_solver=scf_solver)

    nscf_ksampling = KSampling.path_from_structure(ndivsm, structure)

    nscf_strategy = NscfStrategy(scf_strategy, nscf_ksampling, nscf_nband)

    dos_strategy = None

    if dos_kppa is not None:
        raise NotImplementedError("DOS must be tested")
        dos_ksampling = KSampling.automatic_density(structure, kppa,
                                                    chksymbreak=0)
        dos_strategy = NscfStrategy(scf_strategy, dos_ksampling, nscf_nband,
                                    nscf_solver=None)

    return BandStructure(workdir, runmode, scf_strategy, nscf_strategy,
                         dos_strategy=dos_strategy)

################################################################################


def g0w0_with_ppmodel(workdir, runmode, structure, pseudos, scf_kppa,
                      nscf_nband, ecuteps, ecutsigx, accuracy="normal",
                      spin_mode="polarized", smearing="fermi_dirac:0.1 eV",
                      ppmodel="godby", charge=0.0, scf_solver=None,
                      inclvkb=2, scr_nband=None, sigma_nband=None):
    """
    Returns a Work object that performs G0W0 calculations for the given the material.

    Args:
        workdir:
            Working directory.
        runmode:
            `RunMode` instance.
        structure:
            Pymatgen structure.
        pseudos:
            List of `Pseudo` objects.
        scf_kppa:
            Defines the sampling used for the SCF run.
        nscf_nband:
            Number of bands included in the NSCF run.
        ecuteps:
            Cutoff energy [Ha] for the screening matrix.
        ecutsigx:
            Cutoff energy [Ha] for the exchange part of the self-energy.
        accuracy:
            Accuracy of the calculation.
        spin_mode:
            Spin polarization.
        smearing:
            Smearing technique.
        ppmodel:
            Plasmonpole technique.
        charge:
            Electronic charge added to the unit cell.
        scf_solver:
            Algorithm used for solving of the SCF cycle.
        inclvkb:
            Treatment of the dipole matrix elements (see abinit variable).
        scr_nband:
            Number of bands used to compute the screening (default is nscf_nband)
        sigma_nband:
            Number of bands used to compute the self-energy (default is nscf_nband)
    """
    # TODO: Cannot use istwfk != 1.
    extra_abivars = {"istwfk": "*1"}

    scf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)

    scf_strategy = ScfStrategy(structure, pseudos, scf_ksampling,
                               accuracy=accuracy, spin_mode=spin_mode,
                               smearing=smearing, charge=charge,
                               scf_solver=None, **extra_abivars)

    nscf_ksampling = KSampling.automatic_density(structure, 1, chksymbreak=0)

    nscf_strategy = NscfStrategy(scf_strategy, nscf_ksampling, nscf_nband,
                                 **extra_abivars)

    if scr_nband is None:
        scr_nband = nscf_nband

    if sigma_nband is None:
        sigma_nband = nscf_nband

    screening = Screening(ecuteps, scr_nband, w_type="RPA", sc_mode="one_shot",
                          freq_mesh=None, hilbert_transform=None, ecutwfn=None,
                          inclvkb=inclvkb)

    self_energy = SelfEnergy("gw", "one_shot", sigma_nband, ecutsigx, screening,
                             ppmodel=ppmodel)

    scr_strategy = ScreeningStrategy(scf_strategy, nscf_strategy, screening,
                                     **extra_abivars)

    sigma_strategy = SelfEnergyStrategy(scf_strategy, nscf_strategy,
                                        scr_strategy, self_energy,
                                        **extra_abivars)

    return GW_Workflow(workdir, runmode, scf_strategy, nscf_strategy,
                       scr_strategy, sigma_strategy)

################################################################################


def bse_with_mdf(workdir, runmode, structure, pseudos, scf_kppa, nscf_nband, 
                 nscf_ngkpt, nscg_shiftk, ecuteps, bs_loband, soenergy, mdf_epsinf, 
                 accuracy="normal", spin_mode="polarized", smearing="fermi_dirac:0.1 eV",
                 charge=0.0, scf_solver=None):
    """
    Returns a Work object that performs a GS + NSCF + Bethe-Salpeter calculation.
    The self-energy corrections are approximated with the scissors operator. The screening
    in modeled by the model dielectric function.

    Args:
        workdir:
            Working directory.
        runmode:
            `RunMode` instance.
        structure:
            Pymatgen structure.
        pseudos:
            List of `Pseudo` objects.
        scf_kppa:
            Defines the sampling used for the SCF run.
        nscf_nband:
            Number of bands included in the NSCF run.
        nscf_ngkpt:
            Division of the k-mesh used for the NSCF and the BSE run.
        nscf_shiftk:
            Shifts used for the NSCF and the BSE run.
        ecuteps:
            Cutoff energy [Ha] for the screening matrix.
        bs_loband:
            Firs occupied band index used for constructing the e-h basis set (ABINIT convenetion i.e. starts at 1).
        so_energy:
            Scissor energy in Hartree
        mdf_epsing:
            Value of the macroscopic dielectric function used in expression for the model dielectric function.
        accuracy:
            Accuracy of the calculation.
        spin_mode:
            Spin polarization.
        smearing:
            Smearing technique.
        charge:
            Electronic charge added to the unit cell.
        scf_solver:
            Algorithm used for solving of the SCF cycle.
    """
    # Ground-state strategy.
    scf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)

    scf_strategy = ScfStrategy(structure, pseudos, scf_ksampling,
                               accuracy=accuracy, spin_mode=spin_mode,
                               smearing=smearing, charge=charge,
                               scf_solver=None)

    # NSCF calculation on the randomly-shifted k-mesh.
    nscf_ksampling = KSampling.monkhorst(nscf_ngkpt, shiftk=nscf_shiftk, chksymbreak=0)

    nscf_strategy = NscfStrategy(scf_strategy, nscf_ksampling, nscf_nband)

    # Init Strategy for the BSE calculation.
    # FIXME
    raise NotImplementedError("")
    bs_nband = 6
    coulomb_mode = "model_df"
    bs_freq_mesh = [0, 2, 0.1]

    exc_ham = ExcHamiltonian(bs_loband, bs_nband, soenergy, coulomb_mode, ecuteps, bs_freq_mesh, 
                             mdf_epsinf=mdf_epsinf, exc_type="TDA", algo="haydock", with_lf=True, zcut=None)

    # TODO: Cannot use istwfk != 1.
    extra_abivars = {"istwfk": "*1"}
    bse_strategy = MDFBSE_Strategy(scf_strategy, nscf_strategy, exc_ham, **extra_abivars)

    return BSEMDF_Workflow(workdir, runmode, scf_strategy, nscf_strategy, bse_strategy)
