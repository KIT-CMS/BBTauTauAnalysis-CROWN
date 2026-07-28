#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"


namespace xyh {

namespace classifier {

ROOT::RDF::RNode GetMaxScoreIndex(
    ROOT::RDF::RNode df,
    const std::string &output,
    const std::string &scores
) {

    auto get_max_score_index = [] (const ROOT::RVec<float> &scores) {
        auto i_max = ROOT::VecOps::ArgMax(scores);
        return static_cast<int>(i_max);
    };

    return df.Define(
        output,
        get_max_score_index,
        {scores}
    );
}

ROOT::RDF::RNode GetMaxScoreValue(
    ROOT::RDF::RNode df,
    const std::string &output,
    const std::string &scores,
    const std::string &max_score_index
) {

    auto get_max_score_softmax = [] (
        const ROOT::RVec<float> &scores,
        const int &max_score_index
    ) {
        float max_score = scores.at(max_score_index);
        return max_score;
    };

    return df.Define(
        output,
        get_max_score_softmax,
        {
            scores,
            max_score_index
        }
    );
}

}

}
