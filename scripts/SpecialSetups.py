from dataclasses import dataclass
<<<<<<< Updated upstream
from ..producers import taus, embedding, scalefactors
=======
from ..producers import taus, embedding
>>>>>>> Stashed changes


@dataclass
class _Embedding_ES_ID_Scheme_dm_binned:
    producerES = taus.TauPtCorrection_emb_genTau_dm_binned
    producerGroupES = taus.TauEnergyCorrection_Embedding_ES_dm_binned
    producerID_2 = embedding.Tau_2_VsJetTauID_lt_SF_dm_binned
    producerID_1 = embedding.Tau_1_VsJetTauID_tt_SF_dm_binned
    tau_emb_vsjet_sf_dependence = "dm"
    tau_emb_ES_json_name = "tau_energy_scale_dm_binned"


@dataclass
class _Embedding_ES_ID_Scheme_dm_pt_binned:
    producerES = taus.TauPtCorrection_emb_genTau_dm_pt_binned
    producerGroupES = taus.TauEnergyCorrection_Embedding_ES_dm_pt_binned
    producerID_2 = embedding.Tau_2_VsJetTauID_lt_SF_dm_pt_binned
    producerID_1 = embedding.Tau_1_VsJetTauID_tt_SF_dm_pt_binned
    tau_emb_vsjet_sf_dependence = "pt"
    tau_emb_ES_json_name = "tau_energy_scale"



class ES_ID_SCHEME:
    def __init__(self, scheme: str = "dm_pt_binned", ):
        self.scheme = scheme
        self.is_dm_binned = scheme == "dm_binned"
        self.is_dm_pt_binned = scheme == "dm_pt_binned"

        if self.is_dm_binned:
            self.embedding = _Embedding_ES_ID_Scheme_dm_binned()
        elif self.is_dm_pt_binned:
            self.embedding = _Embedding_ES_ID_Scheme_dm_pt_binned()
        else:
            raise ValueError(f"Unknown ES/ID scheme: {scheme}, known schemes are 'dm_binned' and 'dm_pt_binned'")

    @property
    def pt_binning(self):
<<<<<<< Updated upstream
        return [""] if self.is_dm_binned else ["20to40", "40toInf"]
=======
        return [""] if self.is_dm_binned else ["20to40", "40toInf"]
>>>>>>> Stashed changes
