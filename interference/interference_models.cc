// interference_models.cc
#include "interference_models.h"

namespace ns3 {

NoiseInterferenceModel::NoiseInterferenceModel(double noiseFigure)
    : noiseFigure(noiseFigure) {}

void NoiseInterferenceModel::Apply(Ptr<YansWifiPhy> phy) {
    NS_LOG_UNCOND("Applying noise interference with noise figure: " << noiseFigure);
    phy->Set("NoiseFigure", DoubleValue(noiseFigure));
}

TrafficInterferenceModel::TrafficInterferenceModel(uint32_t numInterferers, double trafficRate)
    : numInterferers(numInterferers), trafficRate(trafficRate) {}

void TrafficInterferenceModel::Apply(Ptr<YansWifiPhy> phy) {
    NS_LOG_UNCOND("Applying traffic interference with " << numInterferers << " interferers");
    // Implementation for traffic-based interference
}

NumberInterferenceModel::NumberInterferenceModel(uint32_t numInterferers)
    : numInterferers(numInterferers) {}

void NumberInterferenceModel::Apply(Ptr<YansWifiPhy> phy) {
    NS_LOG_UNCOND("Applying number-based interference with " << numInterferers << " interferers");
    // Implementation for number-based interference
}

// Factory implementations
std::unique_ptr<InterferenceModel> InterferenceModelFactory::CreateNoiseModel(double noiseFigure) {
    return std::make_unique<NoiseInterferenceModel>(noiseFigure);
}

std::unique_ptr<InterferenceModel> InterferenceModelFactory::CreateTrafficModel(uint32_t numInterferers, double trafficRate) {
    return std::make_unique<TrafficInterferenceModel>(numInterferers, trafficRate);
}

std::unique_ptr<InterferenceModel> InterferenceModelFactory::CreateNumberModel(uint32_t numInterferers) {
    return std::make_unique<NumberInterferenceModel>(numInterferers);
}

} // namespace ns3
