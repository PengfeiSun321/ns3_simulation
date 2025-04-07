// wifi_gradual_simulation.cc
#include "simulation_manager.h"
#include "interference_models.h"

int main(int argc, char* argv[]) {
    // ... setup code ...

    // Create simulation manager
    SimulationManager simManager(phy);

    // Add interference models
    simManager.AddInterferenceModel(
        InterferenceModelFactory::CreateNoiseModel(noiseFigure)
    );
    simManager.AddInterferenceModel(
        InterferenceModelFactory::CreateTrafficModel(numInterferers, trafficRate)
    );
    simManager.AddInterferenceModel(
        InterferenceModelFactory::CreateNumberModel(numInterferers)
    );

    // Apply all interference models
    simManager.ApplyAllInterferenceModels();

    // ... rest of the simulation code ...
}
