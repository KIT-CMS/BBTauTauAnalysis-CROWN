"""
Scope-level energy scale variations of the light leptons (v8 spec C32, C37).

The pT corrections of muons and electrons run in the global scope, where a shift
reaches every scope. The shifts of the muon energy scale (mt and em) and of the
electron energy scale of the embedding (et) belong to single scopes. There the
selection, the pair and the four-vector of the lepton read its pT through a
producer of the scope, which scales the corrected pT per |eta| region
(`xyh::energy_scale::ScalePt`). Its nominal factors are 1 and pass the pT on
unchanged, so the nominal columns stay what they are.

The uncorrected four-vector of the lepton (`LVMu1Uncorrected`,
`LVEl1Uncorrected`, ...) keeps its input, so that the difference to the scaled
four-vector reaches the MET like every other lepton energy scale. The loose
leptons of the vetoes, selected in the global scope, are not varied.
"""

from code_generation.producer import Producer

from ..constants import EM_SCOPES, ET_SCOPES, MT_SCOPES
from ..quantities import nanoAOD as nanoAOD
from ..quantities import output as q
from . import electrons, muons, pairselection

MUON_ES_SCOPES = MT_SCOPES + EM_SCOPES
ELECTRON_ES_SCOPES = ET_SCOPES

# Muon pT of the scope with the energy scale variation of its |eta| regions
MuonPtScale = Producer(
    name="MuonPtScale",
    call="""
    xyh::energy_scale::ScalePt(
        {df},
        {output},
        {input},
        {vec_open}{muon_es_abs_eta_edges}{vec_close},
        {vec_open}{muon_es_scale_factors}{vec_close}
    )
    """,
    input=[q.Muon_pt_corrected, nanoAOD.Muon_eta],
    output=[q.Muon_pt_scaled],
    scopes=MUON_ES_SCOPES,
)

# Electron pT of the scope with the energy scale variation of its |eta| regions
ElectronPtScale = Producer(
    name="ElectronPtScale",
    call="""
    xyh::energy_scale::ScalePt(
        {df},
        {output},
        {input},
        {vec_open}{electron_es_abs_eta_edges}{vec_close},
        {vec_open}{electron_es_scale_factors}{vec_close}
    )
    """,
    input=[q.Electron_pt_corrected, nanoAOD.Electron_eta],
    output=[q.Electron_pt_scaled],
    scopes=ELECTRON_ES_SCOPES,
)


def _reading(producer: Producer, replacements: dict, scopes: list[str]) -> Producer:
    """
    `producer` for `scopes` with the input quantities of `replacements`
    (quantity -> its replacement) exchanged: same name, call and outputs.
    """
    (inputs,) = {tuple(producer.input[scope]) for scope in scopes}
    assert set(replacements) <= set(inputs), producer
    return Producer(
        name=producer.name,
        call=producer.call,
        input=[replacements.get(quantity, quantity) for quantity in inputs],
        output=producer.output,
        scopes=list(scopes),
    )


_SCALED_MUON_PT = {q.Muon_pt_corrected: q.Muon_pt_scaled}
_SCALED_ELECTRON_PT = {q.Electron_pt_corrected: q.Electron_pt_scaled}

# The producers of a scope that read the muon pT -> their variant reading the
# scaled pT
MUON_ES_PRODUCERS = {
    muons.GoodMuons: _reading(muons.GoodMuons, _SCALED_MUON_PT, MUON_ES_SCOPES),
    pairselection.MTPairSelection: _reading(
        pairselection.MTPairSelection, _SCALED_MUON_PT, MT_SCOPES
    ),
    pairselection.EMPairSelection: _reading(
        pairselection.EMPairSelection, _SCALED_MUON_PT, EM_SCOPES
    ),
    pairselection.LVMu1: _reading(pairselection.LVMu1, _SCALED_MUON_PT, MT_SCOPES),
    pairselection.LVMu2: _reading(pairselection.LVMu2, _SCALED_MUON_PT, EM_SCOPES),
}

# The same for the electron pT
ELECTRON_ES_PRODUCERS = {
    electrons.GoodElectrons: _reading(
        electrons.GoodElectrons, _SCALED_ELECTRON_PT, ELECTRON_ES_SCOPES
    ),
    pairselection.ETPairSelection: _reading(
        pairselection.ETPairSelection, _SCALED_ELECTRON_PT, ELECTRON_ES_SCOPES
    ),
    pairselection.LVEl1: _reading(
        pairselection.LVEl1, _SCALED_ELECTRON_PT, ELECTRON_ES_SCOPES
    ),
}


def with_muon_es(producers: list) -> list:
    """`producers` of a scope with the scaled muon pT: MuonPtScale and the
    variants of the producers that read the muon pT."""
    assert set(MUON_ES_PRODUCERS) & set(producers), producers
    return [MuonPtScale] + [MUON_ES_PRODUCERS.get(p, p) for p in producers]
