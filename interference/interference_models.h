// interference_models.h
#pragma once

#include "ns3/core-module.h"
#include "ns3/wifi-module.h"

namespace ns3 {

class InterferenceModel {
public:
    virtual ~InterferenceModel() = default;
    virtual void Apply(Ptr<YansWifiPhy> phy) = 0;
};

class NoiseInterferenceModel : public InterferenceModel {
private:
    double noiseFigure;
public:
    NoiseInterferenceModel(double noiseFigure);
    void Apply(Ptr<YansWifiPhy> phy) override;
};

class TrafficInterferenceModel : public InterferenceModel {
private:
    uint32_t numInterferers;
    double trafficRate;
public:
    TrafficInterferenceModel(uint32_t numInterferers, double trafficRate);
    void Apply(Ptr<YansWifiPhy> phy) override;
};

class NumberInterferenceModel : public InterferenceModel {
private:
    uint32_t numInterferers;
public:
    NumberInterferenceModel(uint32_t numInterferers);
    void Apply(Ptr<YansWifiPhy> phy) override;
};

// Factory class to create interference models
class InterferenceModelFactory {
public:
    static std::unique_ptr<InterferenceModel> CreateNoiseModel(double noiseFigure);
    static std::unique_ptr<InterferenceModel> CreateTrafficModel(uint32_t numInterferers, double trafficRate);
    static std::unique_ptr<InterferenceModel> CreateNumberModel(uint32_t numInterferers);
};

} // namespace ns3
