"""Contract of the payload-independent UParT probe-jet profile (Run-2 UL v15, MC only).

TauFakeFactors' ``configs/btag_efficiency/<era>/*`` reads the probe columns by exactly
these names in every channel and era (P2 runs all four), while the analysis b-jet
layer must be gone. The era/sample gates of the entry point are covered by
``test_sm_main_config.py``.
"""

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    output_names,
    producer_names,
)

PROBES = {f"btag_probe_jet_{name}" for name in ("pt", "eta", "hadron_flavour", "upart")}
NOMINAL_WEIGHTS = {"puweight", "lhe_scale_weight", "genWeight"}
ANALYSIS_BJET_LAYER = {"id_wgt_bjet", "n_bjets", "mass_tautaubb", "btag_weight_upart"}


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("scope", SCOPES)
def test_probe_jet_contract_in_every_scope(scope, era):
    config = build("sm_btag_efficiency_config", "ttbar", era=era, scopes=tuple(SCOPES))
    outputs = output_names(config, scope)
    assert PROBES | NOMINAL_WEIGHTS <= outputs
    assert not ANALYSIS_BJET_LAYER & outputs
    assert not {o for o in outputs if o.startswith("btag_weight_upart")}
    assert "StrictUParTBtagWeight" not in producer_names(config, scope)
    # the probe collection is the base b-jet acceptance cleaned of lepton
    # overlaps, with no discriminator cut of its own
    mask = find_producer(config, scope, "BtagProbeJetMask")
    assert "physicsobject::CombineMasks" in mask.call
    assert [q.name for q in mask.get_inputs(scope)] == [
        "base_bjets_mask",
        "jet_overlap_veto_mask",
    ]
