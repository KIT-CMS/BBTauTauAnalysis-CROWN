#ifndef GUARD_PNN_HXX
#define GUARD_PNN_HXX

#include "../../../../include/utility/OnnxSessionManager.hxx"
#include "utility/utility.hxx"
#include <cstddef>
#include <nlohmann/json.hpp>

namespace xyh {

namespace classifier {

ROOT::RDF::RNode GetMaxScoreIndex(
    ROOT::RDF::RNode df,
    const std::string &output,
    const std::string &scores
);

ROOT::RDF::RNode GetMaxScoreValue(
    ROOT::RDF::RNode df,
    const std::string &output,
    const std::string &scores,
    const std::string &max_score_index
);

inline ROOT::RDF::RNode EvaluatePNN(
    ROOT::RDF::RNode df,
    OnnxSessionManager &onnxSessionManager,
    const std::string &output_vector,
    const std::string &reco_input_vector,
    const std::string &event_id,
    const std::string &model_onnx_file_parity_0,
    const std::string &model_onnx_file_parity_1,
    const std::string &params_trafo_file_parity_0,
    const std::string &params_trafo_file_parity_1,
    int num_reco_inputs,
    int num_param_inputs,
    int num_outputs,
    const int &m_x,
    const int &m_y
) {
    Logger::get("EvaluatePNN")
        ->debug("mass hypothesis: mX={}, mY={}", m_x, m_y);

    // Calculate number of input nodes
    int num_inputs = num_reco_inputs + num_param_inputs;

    // Lambda function to transform m_x and m_y values according to ordinal
    // encoding used during training 
    auto transformed = [](const nlohmann::json &trafo, const int &m_x, const int &m_y) {
        int m_x_trans = 0;
        int m_y_trans = 0;

        auto m_x_json = trafo["m_x"];
        for (const auto &pair : trafo["m_x"]) {
            if (pair[0] == m_x) {
                m_x_trans = pair[1].get<int>();
                break;
            }
        }

        auto m_y_json = trafo["m_y"];
        for (const auto &pair : trafo["m_y"]) {
            if (pair[0] == m_y) {
                m_y_trans = pair[1].get<int>();
                break;
            }
        }

        return std::vector<float>({(float) m_x_trans, (float) m_y_trans});
    };

    // Transform input parameters for even training fold
    auto f_trans_0 = std::ifstream(params_trafo_file_parity_0);
    auto params_trafo_training_parity_0 = nlohmann::json::parse(f_trans_0);
    const std::vector<float> param_inputs_parity_0 = transformed(
        params_trafo_training_parity_0, m_x, m_y
    );
    Logger::get("EvaluatePNN")
        ->debug(
            "Input parameters transformed from ({}, {}) to ({}, {}) for fold 0",
            m_x, m_y, param_inputs_parity_0.at(0), param_inputs_parity_0.at(1));

    // Transform input parameters for odd training fold
    auto f_trans_1 = std::ifstream(params_trafo_file_parity_1);
    auto params_trafo_training_parity_1 = nlohmann::json::parse(f_trans_1);
    const std::vector<float> param_inputs_parity_1 = transformed(
        params_trafo_training_parity_1, m_x, m_y
    );
    Logger::get("EvaluatePNN")
        ->debug(
            "Input parameters transformed from ({}, {}) to ({}, {}) for fold 1",
            m_x, m_y, param_inputs_parity_1.at(0), param_inputs_parity_1.at(1));

    // Load the model and create InferenceSession
    std::vector<int64_t> input_node_dims;
    std::vector<int64_t> output_node_dims;
    Ort::AllocatorWithDefaultOptions allocator;

    // Load the session for both folds
    auto session_training_parity_0 = onnxSessionManager.getSession(model_onnx_file_parity_0);
    auto session_training_parity_1 = onnxSessionManager.getSession(model_onnx_file_parity_1);
    onnxhelper::prepare_model(
        session_training_parity_0,
        allocator,
        input_node_dims,
        output_node_dims,
        num_inputs,
        num_outputs
    );
    onnxhelper::prepare_model(
        session_training_parity_1,
        allocator,
        input_node_dims,
        output_node_dims,
        num_inputs,
        num_outputs
    );

    auto evaluate_nn = [
        session_training_parity_0,
        session_training_parity_1,
        allocator,
        input_node_dims,
        output_node_dims,
        num_inputs,
        num_outputs,
        param_inputs_parity_0,
        param_inputs_parity_1
    ] (
        const std::vector<float> &reco_inputs,
        const unsigned long long &event
    ) {
        TStopwatch timer;
        timer.Start();

        auto input = std::vector<float>(reco_inputs);
        std::vector<float> output;

        if (event % 2 == 0) {
            for (const auto& p : param_inputs_parity_1) {
                input.push_back(p);
            }
            output = onnxhelper::run_interference(
                session_training_parity_1,
                allocator,
                input,
                input_node_dims,
                output_node_dims,
                num_inputs,
                num_outputs
            );
        } else {
            for (const auto& p : param_inputs_parity_0) {
                input.push_back(p);
            }
            output = onnxhelper::run_interference(
                session_training_parity_0,
                allocator,
                input,
                input_node_dims,
                output_node_dims,
                num_inputs,
                num_outputs
            );
        }
        timer.Stop();

        // Calculate the softmax values of output scores
        auto output_softmax = ROOT::RVec<float>(output.size());
        float softmax_norm = 0;
        for (const auto &o : output) {
            softmax_norm += exp(o);
        }
        for (size_t i = 0; i < output.size(); ++i) {
            output_softmax[i] = exp(output[i]) / softmax_norm;
        }

        Logger::get("OnnxEvaluate")
            ->debug("Inference time: {} mus", timer.RealTime() * 1000 * 1000); 

        return output_softmax;
    };

    return df.Define(
        output_vector,
        evaluate_nn,
        {
            reco_input_vector,
            event_id
        }
    );
}

}

} // end namespace ml
#endif /* GUARD_ML_H */
