// simulation_manager.h
#pragma once

#include "interference_models.h"
#include <vector>
#include <memory>

namespace ns3 {

class SimulationManager {
private:
    std::vector<std::unique_ptr<InterferenceModel>> interferenceModels;
    Ptr<YansWifiPhy> phy;

public:
    SimulationManager(Ptr<YansWifiPhy> phy);
    
    void AddInterferenceModel(std::unique_ptr<InterferenceModel> model);
    void ApplyAllInterferenceModels();
    void ClearInterferenceModels();
};

} // namespace ns3
