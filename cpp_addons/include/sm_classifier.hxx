#ifndef GUARD_SM_CLASSIFIER_HXX
#define GUARD_SM_CLASSIFIER_HXX

#include "../../../../include/utility/Logger.hxx"
#include "../../../../include/utility/OnnxSessionManager.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

// NN classifier friend sm_nn_classifier (nn spec 3.3, 3.4): the gate flag, the
// scores of a model trained in n outer folds and their output columns.

namespace xyh {

namespace classifier {

/// Defines the bool column `output` from an RDataFrame expression whose
/// columns are written $0, $1, ...: $i stands for `columns[i]`, so that a
/// shifted producer reads the shifted columns.
ROOT::RDF::RNode SelectionFlag(ROOT::RDF::RNode df, const std::string &output,
                               const std::string &expression,
                               const std::vector<std::string> &columns);

/// Writes the scores of a classifier into flat columns: outputs[0] the index
/// of the largest of the first `num_classes` scores, outputs[1] that score and
/// outputs[2 + i] score i (the classes, then a binary head). An empty score
/// vector (event outside the gate) gives -1 in every column.
ROOT::RDF::RNode UnpackScores(ROOT::RDF::RNode df,
                              const std::vector<std::string> &outputs,
                              const std::string &scores,
                              const int &num_classes);

namespace detail {

/// Throws unless a model tensor has the fixed shape [1, expected].
inline void CheckShape(const std::string &file, const std::string &tensor,
                       const std::vector<int64_t> &dims, const int &expected) {
    std::string shape;
    for (const auto &dim : dims) {
        shape += (shape.empty() ? "" : ", ") + std::to_string(dim);
    }
    for (const auto &dim : dims) {
        if (dim <= 0) {
            throw std::runtime_error(
                "Model " + file + ": dynamic dimension in the " + tensor +
                " shape [" + shape + "], CROWN needs a fixed [1, n]");
        }
    }
    if (dims.size() != 2 || dims[0] != 1 || dims[1] != expected) {
        throw std::runtime_error("Model " + file + ": " + tensor + " shape [" +
                                 shape + "], expected [1, " +
                                 std::to_string(expected) + "]");
    }
}

} // namespace detail

/// Scores of a classifier trained in n outer folds: the model of residue r,
/// `model_files[r]`, scores the events with `event % n == r` (unsigned 64-bit
/// arithmetic on the event number, no conversion), which it never saw in its
/// training. Every model must take one input [1, num_inputs] and give one
/// output [1, num_outputs], num_outputs = num_classes or num_classes + 1 (a
/// binary head); a dynamic dimension, other shapes, an input vector of another
/// length or a non-finite input or score throw. Outside the gate the models
/// are not evaluated and the scores are empty. With `apply_softmax` (a model
/// giving logits) the softmax of the class scores is taken; models giving
/// probabilities must not get it, it would apply a second softmax.
///
/// Inline like EvaluatePNN: the ONNX Runtime functions in a source file of
/// the addons do not link (see ml::GenericOnnxEvaluator).
inline ROOT::RDF::RNode
EvaluateFolds(ROOT::RDF::RNode df, OnnxSessionManager &onnxSessionManager,
              const std::string &output, const std::string &inputs,
              const std::string &event, const std::string &gate,
              const std::vector<std::string> &model_files,
              const int &num_inputs, const int &num_classes,
              const int &num_outputs, const bool &apply_softmax) {
    if (model_files.size() < 2) {
        throw std::invalid_argument(
            "EvaluateFolds: " + std::to_string(model_files.size()) +
            " model files, a fold classifier needs at least 2");
    }
    if (num_outputs != num_classes && num_outputs != num_classes + 1) {
        throw std::invalid_argument(
            "EvaluateFolds: " + std::to_string(num_outputs) + " outputs for " +
            std::to_string(num_classes) + " classes");
    }
    struct Model {
        Ort::Session *session;
        std::string input_name, output_name;
    };
    std::vector<Model> models;
    Ort::AllocatorWithDefaultOptions allocator;
    for (const auto &file : model_files) {
        auto session = onnxSessionManager.getSession(file);
        std::vector<int64_t> input_dims, output_dims;
        int num_input_nodes, num_output_nodes;
        // throws unless the model has one input and one output
        onnxhelper::prepare_model(session, allocator, input_dims, output_dims,
                                  num_input_nodes, num_output_nodes);
        detail::CheckShape(file, "input", input_dims, num_inputs);
        detail::CheckShape(file, "output", output_dims, num_outputs);
        models.push_back({session,
                          session->GetInputNameAllocated(0, allocator).get(),
                          session->GetOutputNameAllocated(0, allocator).get()});
        Logger::get("xyh::classifier::EvaluateFolds")
            ->info("{}: residue {} of {}, {} inputs, {} outputs", file,
                   models.size() - 1, model_files.size(), num_inputs,
                   num_outputs);
    }
    const ULong64_t folds = models.size();
    const std::vector<int64_t> input_shape{1, num_inputs},
        output_shape{1, num_outputs};
    const auto memory_info = std::make_shared<Ort::MemoryInfo>(
        Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault));

    auto evaluate = [models, folds, input_shape, output_shape, memory_info,
                     num_classes, apply_softmax](const std::vector<float> &x,
                                                 const ULong64_t &event_number,
                                                 const bool &pass) {
        ROOT::RVec<float> scores;
        if (!pass) {
            return scores;
        }
        if (x.size() != static_cast<size_t>(input_shape[1])) {
            throw std::runtime_error(
                "EvaluateFolds: event " + std::to_string(event_number) +
                " has " + std::to_string(x.size()) +
                " inputs, the model takes " + std::to_string(input_shape[1]));
        }
        for (size_t i = 0; i < x.size(); ++i) {
            if (!std::isfinite(x[i])) {
                throw std::runtime_error("EvaluateFolds: input " +
                                         std::to_string(i) + " of event " +
                                         std::to_string(event_number) + " is " +
                                         std::to_string(x[i]));
            }
        }
        const auto &model = models[event_number % folds];
        std::vector<float> input(x);
        scores.resize(output_shape[1]);
        auto input_tensor = Ort::Value::CreateTensor<float>(
            *memory_info, input.data(), input.size(), input_shape.data(),
            input_shape.size());
        auto output_tensor = Ort::Value::CreateTensor<float>(
            *memory_info, scores.data(), scores.size(), output_shape.data(),
            output_shape.size());
        const char *input_names[] = {model.input_name.c_str()};
        const char *output_names[] = {model.output_name.c_str()};
        model.session->Run(Ort::RunOptions{nullptr}, input_names, &input_tensor,
                           1, output_names, &output_tensor, 1);
        if (apply_softmax) {
            float largest = scores[0], norm = 0;
            for (int i = 1; i < num_classes; ++i) {
                largest = std::max(largest, scores[i]);
            }
            for (int i = 0; i < num_classes; ++i) {
                scores[i] = std::exp(scores[i] - largest);
                norm += scores[i];
            }
            for (int i = 0; i < num_classes; ++i) {
                scores[i] /= norm;
            }
        }
        for (size_t i = 0; i < scores.size(); ++i) {
            if (!std::isfinite(scores[i])) {
                throw std::runtime_error("EvaluateFolds: score " +
                                         std::to_string(i) + " of event " +
                                         std::to_string(event_number) + " is " +
                                         std::to_string(scores[i]));
            }
        }
        return scores;
    };
    return df.Define(output, evaluate, {inputs, event, gate});
}

} // namespace classifier

} // namespace xyh

#endif /* GUARD_SM_CLASSIFIER_HXX */
