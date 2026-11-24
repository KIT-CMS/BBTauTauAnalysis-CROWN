"""Immutable analysis profiles consumed by common_config.build_config."""
from dataclasses import dataclass, field, replace
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class ShiftScheme:
    """
    The systematic shifts of a profile where they differ from the common set of
    `variations/`. The defaults are the common set, which the NMSSM analysis and
    the tau-ID measurement keep; the SM analysis sets the scheme of its shift
    production (v8 spec section 4, the item is named at each field).
    """

    # The POG syst_TES_<era>_dm<DM> components of the vsJet SF as weight shifts
    # per era and decay mode (C18).
    tau_id_vs_jet_syst_tes: bool = False
    # The energy scale of genuine taus per decay mode without pT bins, and that
    # of mu -> tau fakes per decay mode instead of per muon wheel (C21).
    tau_es_per_decay_mode: bool = False
    # The scopes with the energy scale shifts of e -> tau and of mu -> tau
    # fakes; None: every scope with a hadronic tau (C29).
    electron_fake_tau_es_scopes: Optional[Tuple[str, ...]] = None
    muon_fake_tau_es_scopes: Optional[Tuple[str, ...]] = None
    # The jet energy resolution in the six eta/pT regions of JERC
    # (variations.jec.JER_REGIONS) instead of one shift per era (C33).
    jer_regions: bool = False
    # The muon energy scale of simulated and embedded events: scope -> the
    # |eta| regions (variations.muons.MUON_ES_REGIONS) with a shift. These
    # scopes read the muon pT through a producer of their own
    # (producers/lepton_energy_scale.py), whose nominal passes it on (C37).
    muon_es_regions: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    # The electron energy scale of the tau embedding in et, barrel and endcap
    # (variations.electrons.add_embedding_electron_es_shifts); the embedded
    # events of et then read the electron pT through a producer of the scope,
    # whose nominal passes it on (C32).
    embedding_electron_es: bool = False
    # The unclustered energy shift of the MET also on the recoil-corrected
    # samples (DY and W of the Run-2 v15 recoil eras), where it acts before
    # the recoil correction. Without it these samples have the recoil shifts
    # only, every other simulated sample the unclustered energy shift only
    # (C38).
    unclustered_energy_shift_on_recoil_corrected_samples: bool = True


@dataclass(frozen=True)
class AnalysisProfile:
    name: str
    # SampleModifier mappings sample -> mother pdgid (default -1).
    bb_truegen_mother_pdgid: Mapping[str, int]
    tautau_truegen_mother_pdgid: Mapping[str, int]
    # Samples for which the STANDARD LHE_Scale_weight producer is removed; they
    # get no QCD scale shifts either.
    lhe_scale_weight_excluded_samples: Tuple[str, ...]
    # Samples for which the special NMSSM producer replaces the standard one.
    nmssm_lhe_scale_weight_samples: Tuple[str, ...]
    # Read Run-2 eras from NanoAOD v15 instead of the legacy v9: AK4-PUPPI jets
    # with correctionlib jet ID and v15 JEC/JER, Run-3-style EGM scale+smear,
    # PuppiMET covariance. Per-era payloads are resolved in common_config /
    # btag_payloads.
    use_run2_v15_inputs: bool
    # b-jet |eta| acceptance override; None keeps the era default.
    bjet_max_abs_eta_override: Optional[float]
    # "upart" switches branch/WPs/SF payloads to the UParTAK4 tagger; None = legacy.
    btag_algorithm: Optional[str]
    # Efficiency payload directory; may contain an "{era}" placeholder.
    btag_payload_dir: Optional[str]
    # Efficiency-ntuple profile switches.
    mc_only: bool = False
    enable_btag_sf: bool = True
    enable_probe_jet_collection: bool = False
    # Upper bound on the relative isolation of the light lepton kept in the
    # tau channels (et electron, mt muon); None keeps the 0.4 default. The
    # analysis cuts at 0.15, the stored sideband above it feeds the fake-factor
    # DR-to-SR corrections and the anti-isolated control regions.
    tau_channel_lepton_max_iso: Optional[float] = None
    # Tau embedding on the Run-2 v15 inputs (embedding_run2_v15): the scopes it
    # may be built for (empty: none), whether the embedded taus get the payload
    # tau energy scale, vsJet SF and their shifts, and an optional lower tau pT
    # threshold (tight_tau_min_pt) for embedding builds.
    embedding_scopes: Tuple[str, ...] = ()
    embedding_tau_corrections: bool = True
    embedding_min_tau_pt: Optional[float] = None
    # The corrections, triggers and MC shifts of the tau-ID SF and ES measurement
    # (tau_id_measurement.py) in place of the analysis ones.
    tau_id_measurement: bool = False
    # The lepton IDs the lepton SFs of the Tau Embedding group (KIT) are measured
    # for, as in the legacy SM analysis: MVA WP90 electrons with isolation
    # pre-cuts, medium-ID muons, and the POG SFs of these IDs. Otherwise the IDs
    # of add_electron_config and add_muon_config.
    kit_sf_lepton_ids: bool = False
    # The single-lepton triggers of the KIT trigger SFs (Tau Embedding group):
    # only the isolated analysis triggers of the era (tau_triggersetup), matched to
    # their trigger object within Delta R 0.1 as in the KIT tag and probe, and in
    # Run 2 the POG muon trigger SF of the era in MC evaluated at every pT within
    # the payload range (scalefactors.PogSingleMuonTriggerSF). Otherwise the
    # high-pT single-lepton triggers as well, matched within 0.4, with the POG
    # muon trigger SF where the trigger flag fires.
    kit_single_lepton_triggers: bool = False
    # The e-tau and mu-tau cross triggers (flags of et and mt).
    lepton_tau_cross_triggers: bool = True
    # The di-tau trigger of the tt embedding (embedding_run2_v15): "eff_data", the
    # weight eps_data(tau1) * eps_data(tau2) without trigger requirement (v7 spec
    # E33, variant A); the filter-bit flags stay as diagnostic columns.
    tt_embedding_trigger: str = "eff_data"
    # The L1 prefiring weight on MC only, in every Run-2 era (2018: the muon
    # prefiring), written as prefiring_wgt with its NanoAOD Up/Dn columns and
    # without prefiring shifts (v7 spec E11, C11; the tau-ID measurement adds
    # them). Otherwise the weight on every sample of 2016 and 2017 with shifts.
    prefiring_weight_columns: bool = False
    # The 2018 HEM 15/16 event flag hem_veto (v7 spec E29, C20) in place of the
    # HEM jet energy scale shift.
    hem_veto_flag: bool = False
    # The EGM electron ID and reconstruction SFs evaluated at the supercluster
    # eta, eta + deltaEtaSC (v7 spec K7, C22), instead of the electron eta.
    electron_sf_supercluster_eta: bool = False
    # Working points of the strict UParTAK4 b-tag event weight, tightest first
    # (v7 spec E14, C14).
    btag_sf_working_points: Tuple[str, ...] = ("T", "M")
    # The columns of the jets with the PNet/UParT pT regression (bpair_*_regressed*,
    # jpt_regressed*) and their producers. The Run-2 v15 path calibrates these
    # jets with the AK4PFPuppi corrections, which JERC excludes for regressed
    # jets, and nothing reads the columns (v8 spec C36).
    regressed_jet_columns: bool = True
    # The systematic shifts beyond the common set.
    shifts: ShiftScheme = field(default_factory=ShiftScheme)


NMSSM_PROFILE = AnalysisProfile(
    name="nmssm",
    bb_truegen_mother_pdgid={"nmssm_Ybb": 35, "nmssm_Ytautau": 25},
    tautau_truegen_mother_pdgid={"nmssm_Ybb": 25, "nmssm_Ytautau": 35},
    lhe_scale_weight_excluded_samples=(
        "data", "embedding", "embedding_mc", "diboson", "hh2b2tau",
    ),
    nmssm_lhe_scale_weight_samples=("nmssm_Ybb", "nmssm_Ytautau"),
    use_run2_v15_inputs=False,
    bjet_max_abs_eta_override=None,
    btag_algorithm=None,
    btag_payload_dir=None,
)

SM_PROFILE = AnalysisProfile(
    name="sm",
    bb_truegen_mother_pdgid={"hh2b2tau": 25},
    tautau_truegen_mother_pdgid={"hh2b2tau": 25},
    # SM keeps the standard LHE producer for hh2b2tau (9-entry LHEScaleWeight
    # in the v15 HH input) and for diboson: all 56 diboson nicks of the Run-2
    # v15 lists carry the 9-entry LHEScaleWeight (v8 spec C34).
    lhe_scale_weight_excluded_samples=("data", "embedding", "embedding_mc"),
    nmssm_lhe_scale_weight_samples=(),
    use_run2_v15_inputs=True,
    bjet_max_abs_eta_override=2.4,
    btag_algorithm="upart",
    btag_payload_dir="payloads/btagging_efficiencies/upart/{era}",
    tau_channel_lepton_max_iso=0.5,
    embedding_scopes=("et", "mt", "tt"),
    kit_sf_lepton_ids=True,
    kit_single_lepton_triggers=True,
    lepton_tau_cross_triggers=False,
    prefiring_weight_columns=True,
    hem_veto_flag=True,
    electron_sf_supercluster_eta=True,
    btag_sf_working_points=("T", "M"),
    regressed_jet_columns=False,
    shifts=ShiftScheme(
        tau_id_vs_jet_syst_tes=True,
        tau_es_per_decay_mode=True,
        electron_fake_tau_es_scopes=("et",),
        muon_fake_tau_es_scopes=("mt",),
        jer_regions=True,
        # mt keeps no muon above |eta| = 2.1 in the analysis (v7 spec E31)
        muon_es_regions={
            "mt": ("etalt1p2", "eta1p2to2p1"),
            "em": ("etalt1p2", "eta1p2to2p1", "eta2p1to2p4"),
        },
        embedding_electron_es=True,
        unclustered_energy_shift_on_recoil_corrected_samples=False,
    ),
)

# The surfaces of the productions smrun2_btag_eff_v1 and smrun2_tau_id_v2, which
# the profiles below keep: diboson without the QCD scale weight, and the columns
# of the regressed jets.
_V7_LHE_SCALE_WEIGHT_EXCLUDED_SAMPLES = ("data", "embedding", "embedding_mc", "diboson")

# Same selection as the SM analysis, but MC only, no b-tag SF, and the
# payload-independent probe-jet collection the efficiency is measured from.
SM_BTAG_EFFICIENCY_PROFILE = replace(
    SM_PROFILE,
    name="sm_btag_efficiency",
    btag_payload_dir=None,
    mc_only=True,
    enable_btag_sf=False,
    enable_probe_jet_collection=True,
    # produced without shifts (smrun2_btag_eff_v1); the surface of that production stays
    shifts=ShiftScheme(),
    lhe_scale_weight_excluded_samples=_V7_LHE_SCALE_WEIGHT_EXCLUDED_SAMPLES,
    regressed_jet_columns=True,
)

# The SM selection in mt and mm with the corrections and MC shifts of the tau-ID
# SF and ES measurement, which applies no b-tag SF. The embedded taus stay
# uncorrected and keep a lower pT threshold, so that the ES grid applied
# downstream (up to +20 %) still finds every tau above 20 GeV. Its MC shifts are
# those of its production smrun2_tau_id_v2, the common set (README, section
# "Tau-ID measurement"), not the scheme of the SM shift production.
SM_TAU_ID_MEASUREMENT_PROFILE = replace(
    SM_PROFILE,
    name="sm_tau_id_measurement",
    btag_payload_dir=None,
    enable_btag_sf=False,
    embedding_scopes=("mt", "mm"),
    embedding_tau_corrections=False,
    embedding_min_tau_pt=20.0 / 1.2,
    tau_id_measurement=True,
    shifts=ShiftScheme(),
    lhe_scale_weight_excluded_samples=_V7_LHE_SCALE_WEIGHT_EXCLUDED_SAMPLES,
    regressed_jet_columns=True,
)
