// simulation_manager.cc
#include "simulation_manager.h"

namespace ns3 {

SimulationManager::SimulationManager(Ptr<YansWifiPhy> phy)
    : phy(phy) {}

void SimulationManager::AddInterferenceModel(std::unique_ptr<InterferenceModel> model) {
    interferenceModels.push_back(std::move(model));
}

void SimulationManager::ApplyAllInterferenceModels() {
    for (const auto& model : interferenceModels) {
        model->Apply(phy);
    }
}

void SimulationManager::ClearInterferenceModels() {
    interferenceModels.clear();
}

} // namespace ns3
