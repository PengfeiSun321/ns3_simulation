
import time


try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit(
        "Error: ns3 Python module not found;"
        " Python bindings may not be enabled"
        " or your PYTHONPATH might not be properly configured"
    )
import cppyy
import os

os.environ["CPPYY_UNCAUGHT_QUIET"] = "1"

_cpp_initialized = False

def initialize_cpp():
    global _cpp_initialized
    if _cpp_initialized:
        return
    ns.cppyy.cppdef("""
        #include "ns3/callback.h"
        #include "ns3/packet.h"
        #include "ns3/ipv4.h"
        #include "ns3/ipv4-address.h"
        #include "ns3/node.h"
        #include <vector>
        #include <map>
        
        using namespace ns3;
                    
        // Ipv4Address getIpv4AddressFromNode(Ptr<Node> node){
        // return node->GetObject<Ipv4>()->GetAddress(1,0).GetLocal();
        // }
                    
        Ipv4Address getIpv4AddressFromNode(Ptr<Node> node) {
            Ptr<Ipv4> ipv4 = node->GetObject<Ipv4>();
            if (!ipv4) {
                return Ipv4Address();
            }
            return ipv4->GetAddress(1, 0).GetLocal();
        }
                    
        struct WindowMetrics {
                    // counter part
                    int rxCount;
                    int txCount;
                    double rxSum;
                    double txSum;
                    
                    // ap data info, statistics
                    int RadioRXBitsPeak;
                    int RadioTXBitsPeak;
                    double RadioRXBitsMean;
                    double RadioTXBitsMean;
                    

                    double radioUtilization;
                    double meanRatioUtilization;
                    
                    int ratioAssociationClientsPeak;
                    double meanRatioAssociationClients;

                    int channelPeakRx;
                    int channelPeakTx;
                    int channelThroughput;
                    double channelInterference;
                    
                    double channelBusyRate;
                    // terminal data info 
                    int deviceRxPeak;
                    int deviceTxPeak;
                    int RetriedRx;
                    int RetriedTx;

                    WindowMetrics() :
                        rxCount(0),
                        txCount(0),
                        rxSum(0.0),
                        txSum(0.0),
                        RadioRXBitsPeak(0),
                        RadioTXBitsPeak(0),
                        RadioRXBitsMean(0.0),
                        RadioTXBitsMean(0.0) {}
        };
                    
        struct StatisticTracker {
            double timeWindow;
            double currentTime;
            double lastWindowEnd;
            WindowMetrics currentMetrics;
            std::map<double, WindowMetrics> windowStatistics;
                    
            StatisticTracker(double window=1.0): // can set the window size as up to 60 seconds
                    timeWindow(window),
                    currentTime(0.0),
                    lastWindowEnd(0.0) {}
                
            void updatePeaks(double time, int rxSize, int txSize) {
                    currentTime = time;
                    double windowEnd = std::floor(time / timeWindow) * timeWindow;
                    if (windowEnd > lastWindowEnd) {

                        if (currentMetrics.rxCount > 0) {
                            currentMetrics.RadioRXBitsMean = currentMetrics.rxSum / currentMetrics.rxCount;
                        }
                        if (currentMetrics.txCount > 0) {
                            currentMetrics.RadioTXBitsMean = currentMetrics.txSum / currentMetrics.txCount;
                        }

                        // Save metrics for the previous window
                        if (lastWindowEnd >= 0) {
                            windowStatistics[lastWindowEnd] = currentMetrics;
                        }
                        // Reset metrics for new window
                        currentMetrics = WindowMetrics();
                        lastWindowEnd = windowEnd;
                    }

                    currentMetrics.RadioRXBitsPeak = std::max(currentMetrics.RadioRXBitsPeak, rxSize);
                    currentMetrics.RadioTXBitsPeak = std::max(currentMetrics.RadioTXBitsPeak, txSize);

                    // Update sums and counts for mean calculation
                    if (rxSize > 0) {
                        currentMetrics.rxSum += rxSize;
                        currentMetrics.rxCount++;
                    }
                    if (txSize > 0) {
                        currentMetrics.txSum += txSize;
                        currentMetrics.txCount++;
                    }
                }
            
            void updateChannelMetrics(double time, double interference, double utilization, double busyRate) {
                currentTime = time;
                double windowEnd = std::floor(time / timeWindow) * timeWindow;

                // If we've moved to a new window
                if (windowEnd > lastWindowEnd) {
                    if (lastWindowEnd >= 0) {
                        windowStatistics[lastWindowEnd] = currentMetrics;
                    }
                    currentMetrics = WindowMetrics();
                    lastWindowEnd = windowEnd;
                }
                
                currentMetrics.channelInterference = interference;
                currentMetrics.radioUtilization = utilization;
                currentMetrics.channelBusyRate = busyRate;
            }
        };
                    
        static StatisticTracker* g_statistic_tracker = nullptr;
        
        void InitializeStatisticTracker(double window) {
            if (g_statistic_tracker != nullptr) {
                    delete g_statistic_tracker;
            }
             g_statistic_tracker = new StatisticTracker(window);
        }
        
        void DevRxTraceCallback(std::string context, Ptr<const Packet> packet) {
            int size = packet->GetSize();
            double now = Simulator::Now().GetSeconds();
            g_statistic_tracker->updatePeaks(now, size, 0);
        }
        
        void DevTxTraceCallback(std::string context, Ptr<const Packet> packet) {
            int size = packet->GetSize();
            double now = Simulator::Now().GetSeconds();
            g_statistic_tracker->updatePeaks(now, 0, size);
        }
                    
        // get all the metrics
        std::map<double, WindowMetrics> GetWindowMetrics() {
            return g_statistic_tracker->windowStatistics;
        }
                    
        void PhyRxOkTrace(std::string context, 
                        Ptr<const Packet> packet, 
                        double snr,
                        WifiMode mode,
                        WifiPreamble preamble) {
            std::string wifi_mode = mode.GetUniqueName();
            int size = packet->GetSize();
        }
        
        static std::vector<std::pair<int, int>> g_tx_events;
                    
        void PhyTxTrace(std::string context, 
                        Ptr<const Packet> packet, 
                        WifiMode mode,
                        WifiPreamble preamble,
                        uint8_t txPower) {
            g_tx_events.push_back(std::make_pair(packet->GetSize(), (int) txPower));
        }
        
        std::vector<std::pair<int, int>> GetTxEvents() {
            return g_tx_events;
        }
                    
      //   void ClearStatistics() {
      //       g_statistic_tracker = StatisticTracker(1.0);
      //       g_statistic_tracker.currentTime = 0.0;
      //       g_statistic_tracker.lastWindowEnd = 0.0;
      //   }
        
        void PhyTxTraceWrapper(std::string context, 
                        Ptr<const Packet> packet, 
                        WifiMode mode,
                        WifiPreamble preamble,
                        int txPowerInt) {
            uint8_t txPower = static_cast<uint8_t>(txPowerInt);
            PhyTxTrace(context, packet, mode, preamble, txPower);
        }
                    
        
    """)

    # ns.cppyy.cppdef(
    #     """
    #     Ipv4Address getIpv4AddressFromNode(Ptr<Node> node){
    #     return node->GetObject<Ipv4>()->GetAddress(1,0).GetLocal();
    #     }
    # """
    # )
    _cpp_initialized = True

# ns.cppyy.cppdef("""
#     #include "ns3/callback.h"
#     #include "ns3/packet.h"
#     #include "ns3/wifi-module.h"
#     using namespace ns3;

#     // Define a type for our callback
#     typedef void (*PhyTxCallback_t)(std::string, Ptr<const Packet>, WifiMode, WifiPreamble, int);
    
#     // Global function pointer (initially null)
#     PhyTxCallback_t MyPhyTxTraceCallback = 0;

#     // Wrapper that converts txPower and calls the global callback if set
#     void PhyTxTraceCallbackWrapper(std::string context, 
#           Ptr<const Packet> packet, WifiMode mode, WifiPreamble preamble, uint8_t txPower) {
#          if (MyPhyTxTraceCallback) {
#              MyPhyTxTraceCallback(context, packet, mode, preamble, static_cast<int>(txPower));
#          }
#     }
# """)


# def rx_trace_callback(context, packet):
#     rx_packet_sizes.append(packet.GetSize())

# def rx_phy_callback(context, packet, snr, mode, pre_amble):
#     rx_events.append({
#         'packet_size': packet.GetSize(),
#         'mode': mode.GetUniqueName(),
#     })



def MixedWireless(numofbackbone, numofInfra, numofLan, duration, sampleCts):
    """
        the simulation params are predefined. we can set a logic here to choose the params 
        based on the requestFlag. for instance, if it requst the channel interference then 
        we can set two ap or we if not then we can just passed the config.
    """
    from ctypes import c_double, c_int
    
    ns.Simulator.Destroy()
    initialize_cpp() # intialize the cpp module
    # ns.cppyy.gbl.ClearStatistics()
    

    ns.cppyy.gbl.InitializeStatisticTracker(float(7.0/sampleCts))

    backboneNodes = c_int(numofbackbone)
    infraNodes = c_int(numofInfra)
    lanNodes = c_int(numofLan)
    stopTime = c_double(duration)

    
    # statistic_events = collections.defaultdict(list)
    # if not requestFlag:
    #     statistic_events['TimeWindow'] = []
    statistic_events = []
    
    ns.Config.SetDefault("ns3::OnOffApplication::PacketSize", ns.StringValue("1024"))
    ns.Config.SetDefault("ns3::OnOffApplication::DataRate", ns.StringValue("100kb/s"))

    if stopTime.value < 10:
        print("Use a simulation stop time >= 10 seconds")
        exit(1)

    backbone = ns.NodeContainer()
    backbone.Create(backboneNodes.value)

    wifi = ns.WifiHelper()
    mac = ns.WifiMacHelper()
    mac.SetType("ns3::AdhocWifiMac")
    wifi.SetRemoteStationManager(
        "ns3::ConstantRateWifiManager", "DataMode", ns.StringValue("OfdmRate54Mbps")
    )

    wifiPhy = ns.YansWifiPhyHelper()
    wifiPhy.SetPcapDataLinkType(wifiPhy.DLT_IEEE802_11_RADIO)
    wifiChannel = ns.YansWifiChannelHelper.Default()
    wifiPhy.SetChannel(wifiChannel.Create())
    backboneDevices = wifi.Install(wifiPhy, mac, backbone)

    # Add the IPv4 protocol stack to the nodes in our container

    internet = ns.InternetStackHelper()
    olsr = ns.OlsrHelper()
    internet.SetRoutingHelper(olsr)
    
    internet.Install(backbone)
    
    ipAddrs = ns.Ipv4AddressHelper()
    ipAddrs.SetBase(ns.Ipv4Address("192.168.0.0"), ns.Ipv4Mask("255.255.255.0"))
    ipAddrs.Assign(backboneDevices)

    mobility = ns.MobilityHelper()
    mobility.SetPositionAllocator(
        "ns3::GridPositionAllocator",
        "MinX",
        ns.DoubleValue(20.0),
        "MinY",
        ns.DoubleValue(20.0),
        "DeltaX",
        ns.DoubleValue(20.0),
        "DeltaY",
        ns.DoubleValue(20.0),
        "GridWidth",
        ns.UintegerValue(5),
        "LayoutType",
        ns.StringValue("RowFirst"),
    )
    mobility.SetMobilityModel(
        "ns3::RandomDirection2dMobilityModel",
        "Bounds",
        ns.RectangleValue(ns.Rectangle(-500, 500, -500, 500)),
        "Speed",
        ns.StringValue("ns3::ConstantRandomVariable[Constant=2]"),
        "Pause",
        ns.StringValue("ns3::ConstantRandomVariable[Constant=0.2]"),
    )
    mobility.Install(backbone)

    # ## construct the LANs # future simulation can introduce the LAN network
    # #  Reset the address base-- all of the CSMA networks will be in
    # #  the "172.16 address space
    # ipAddrs.SetBase(ns.Ipv4Address("172.16.0.0"), ns.Ipv4Mask("255.255.255.0"))

    # for i in range(backboneNodes.value):
    #     print("Configuring local area network for backbone node ", i)
    #     #
    #     #  Create a container to manage the nodes of the LAN.  We need
    #     #  two containers here; one with all of the new nodes, and one
    #     #  with all of the nodes including new and existing nodes
    #     #
    #     newLanNodes = ns.NodeContainer()
    #     newLanNodes.Create(lanNodes.value - 1)
    #     #  Now, create the container with all nodes on this link
    #     lan = ns.NodeContainer(ns.NodeContainer(backbone.Get(i)), newLanNodes)
    #     #
    #     #  Create the CSMA net devices and install them into the nodes in our
    #     #  collection.
    #     #
    #     csma = ns.CsmaHelper()
    #     csma.SetChannelAttribute("DataRate", ns.DataRateValue(ns.DataRate(5000000)))
    #     csma.SetChannelAttribute("Delay", ns.TimeValue(ns.MilliSeconds(2)))
    #     lanDevices = csma.Install(lan)
    #     #
    #     #  Add the IPv4 protocol stack to the new LAN nodes
    #     #
    #     internet.Install(newLanNodes)
    #     #
    #     #  Assign IPv4 addresses to the device drivers(actually to the
    #     #  associated IPv4 interfaces) we just created.
    #     #
    #     ipAddrs.Assign(lanDevices)
    #     #
    #     #  Assign a new network prefix for the next LAN, according to the
    #     #  network mask initialized above
    #     #
    #     ipAddrs.NewNetwork()
    #     #
    #     # The new LAN nodes need a mobility model so we aggregate one
    #     # to each of the nodes we just finished building.
    #     #
    #     mobilityLan = ns.MobilityHelper()
    #     positionAlloc = ns.ListPositionAllocator()
    #     for j in range(newLanNodes.GetN()):
    #         positionAlloc.Add(ns.Vector(0.0, (j * 10 + 10), 0.0))

    #     mobilityLan.SetPositionAllocator(positionAlloc)
    #     mobilityLan.PushReferenceMobilityModel(backbone.Get(i))
    #     mobilityLan.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    #     mobilityLan.Install(newLanNodes)

    #  Reset the address base-- all of the 802.11 networks will be in
    #  the "10.0" address space
    ipAddrs.SetBase(ns.Ipv4Address("10.0.0.0"), ns.Ipv4Mask("255.255.255.0"))
    tempRef = []  # list of references to be held to prevent garbage collection
    for i in range(backboneNodes.value):
        print("Configuring wireless network for backbone node ", i)
        #
        #  Create a container to manage the nodes of the LAN.  We need
        #  two containers here; one with all of the new nodes, and one
        #  with all of the nodes including new and existing nodes
        #
        stas = ns.NodeContainer()
        stas.Create(infraNodes.value - 1)
        #  Now, create the container with all nodes on this link
        infra = ns.NodeContainer(ns.NodeContainer(backbone.Get(i)), stas)
        #
        #  Create another ad hoc network and devices
        #
        ssid = ns.Ssid("wifi-infra" + str(i))
        wifiInfra = ns.WifiHelper()
        wifiPhy.SetChannel(wifiChannel.Create())
        macInfra = ns.WifiMacHelper()
        macInfra.SetType("ns3::StaWifiMac", "Ssid", ns.SsidValue(ssid))

        # setup stas
        staDevices = wifiInfra.Install(wifiPhy, macInfra, stas)
        # setup ap.
        macInfra.SetType("ns3::ApWifiMac", "Ssid", ns.SsidValue(ssid))
        apDevices = wifiInfra.Install(wifiPhy, macInfra, backbone.Get(i))
        # Collect all of these new devices
        infraDevices = ns.NetDeviceContainer(apDevices, staDevices)

        #  Add the IPv4 protocol stack to the nodes in our container
        #
        internet.Install(stas)
        #
        #  Assign IPv4 addresses to the device drivers(actually to the associated
        #  IPv4 interfaces) we just created.
        #
        ipAddrs.Assign(infraDevices)
        #
        #  Assign a new network prefix for each mobile network, according to
        #  the network mask initialized above
        #
        ipAddrs.NewNetwork()

        # This call returns an instance that needs to be stored in the outer scope
        # not to be garbage collected when overwritten in the next iteration
        subnetAlloc = ns.ListPositionAllocator()

        # Appending the object to a list is enough to prevent the garbage collection
        tempRef.append(subnetAlloc)

        #
        #  The new wireless nodes need a mobility model so we aggregate one
        #  to each of the nodes we just finished building.
        #
        for j in range(infra.GetN()):
            subnetAlloc.Add(ns.Vector(0.0, j, 0.0))

        mobility.PushReferenceMobilityModel(backbone.Get(i))
        mobility.SetPositionAllocator(subnetAlloc)
        mobility.SetMobilityModel(
            "ns3::RandomDirection2dMobilityModel",
            "Bounds",
            ns.RectangleValue(ns.Rectangle(-10, 10, -10, 10)),
            "Speed",
            ns.StringValue("ns3::ConstantRandomVariable[Constant=3]"),
            "Pause",
            ns.StringValue("ns3::ConstantRandomVariable[Constant=0.4]"),
        )
        mobility.Install(stas)

    #  Create the OnOff application to send UDP datagrams of size
    #  210 bytes at a rate of 448 Kb/s, between two nodes
    port = 9  #  Discard port(RFC 863)

    appSource = ns.NodeList.GetNode(backboneNodes.value)
    lastNodeIndex = (
        backboneNodes.value
        + backboneNodes.value * (lanNodes.value - 1)
        + backboneNodes.value * (infraNodes.value - 1)
        - 1
    )
    appSink = ns.NodeList.GetNode(lastNodeIndex)

    # Let's fetch the IP address of the last node, which is on Ipv4Interface 1
    remoteAddr = ns.cppyy.gbl.getIpv4AddressFromNode(appSink)
    socketAddr = ns.InetSocketAddress(remoteAddr, port)
    onoff = ns.OnOffHelper("ns3::UdpSocketFactory", socketAddr.ConvertTo())
    apps = onoff.Install(ns.NodeContainer(appSource))
    apps.Start(ns.Seconds(3))
    apps.Stop(ns.Seconds(stopTime.value - 1))

    #  Create a packet sink to receive these packets
    sink = ns.PacketSinkHelper(
        "ns3::UdpSocketFactory",
        ns.InetSocketAddress(ns.InetSocketAddress(ns.Ipv4Address.GetAny(), port)).ConvertTo(),
    )
    sinkContainer = ns.NodeContainer(appSink)
    apps = sink.Install(sinkContainer)
    apps.Start(ns.Seconds(2)) # from 2 to 10 simulate 8 seconds 

    # ====================================================== MacRx recording

    ns.Config.Connect(
    "/NodeList/*/DeviceList/*/Mac/MacRx",
    ns.MakeCallback(ns.cppyy.gbl.DevRxTraceCallback)
    )
    ns.Config.Connect(
    "/NodeList/*/DeviceList/*/Mac/MacTx",
    ns.MakeCallback(ns.cppyy.gbl.DevTxTraceCallback)
    )

    # ns.Config.Connect(
    # "/NodeList/*/DeviceList/*/Phy/State/RxOk",
    # ns.MakeCallback(ns.cppyy.gbl.PhyRxOkTrace)
    # )

    # ns.Config.Connect(
    # "/NodeList/*/DeviceList/*/Phy/State/Tx",
    # ns.MakeCallback(ns.cppyy.gbl.PhyTxTraceWrapper)
    # )

    # ns.Config.Connect(
    #     "/NodeList/*/DeviceList/*/Mac/MacRx",
    #     ns.MakeCallback(rx_trace_callback)
    # )
    # ns.Config.Connect(
    #     "/NodeList/*/DeviceList/*/Mac/MacTx",
    #     ns.MakeCallback(tx_trace_callback)
    # )

    # ====================================================== Phy Rx recording
    # ns.Config.Connect(
    #     "/NodeList/*/DeviceList/*/Phy/State/RxOk",
    #     ns.MakeCallback(rx_phy_callback)
    # )

    # ns.Config.Connect(
    #     "/NodeList/*/DeviceList/*/Phy/State/Tx",
    #     ns.MakeCallback(tx_phy_callback)
    # )

    ns.Simulator.Stop(ns.Seconds(stopTime.value))
    ns.Simulator.Run()

    base_time = int(time.time())
    # 

    
    events = ns.cppyy.gbl.GetWindowMetrics()

    field_mapping = {
        'ap_status': [],
        'radio_tx_bits': [],
        'radio_rx_bits': [],
        'radio_utilization': [],
        'radio_associated_clients': [],
        'channel_tx_rate': [],
        'channel_rx_rate': [],
        'channel_throughput': [],
        'channel_busy_rate': [],
        'channel_interference_rate': []
    }
    for time_window, val in events:
        tstamp = base_time + int(time_window)*180
        field_mapping['ap_status'].append([tstamp, str(1)])
        field_mapping['radio_tx_bits'].append([tstamp, str(val.txSum)])
        field_mapping['radio_rx_bits'].append([tstamp, str(val.rxSum)])
        field_mapping['radio_utilization'].append([tstamp, str(0.8)])
        field_mapping['radio_associated_clients'].append([tstamp, str(3)])
        field_mapping['channel_tx_rate'].append([tstamp, str(val.RadioTXBitsMean)])
        field_mapping['channel_rx_rate'].append([tstamp, str(val.RadioRXBitsMean)])
        field_mapping['channel_throughput'].append([tstamp, str((val.RadioRXBitsPeak+val.RadioTXBitsPeak)//2)])
        field_mapping['channel_busy_rate'].append([tstamp, str(0.8)])
        field_mapping['channel_interference_rate'].append([tstamp, str(0.1)])

        # statistic_events['TimeWindow'].append(time_window)
        # statistic_events['RadioRXBitsPeak'].append(val.RadioRXBitsPeak)
        # statistic_events['RadioRXBitsMean'].append(val.RadioRXBitsMean)
        # statistic_events['RadioTXBitsPeak'].append(val.RadioTXBitsPeak)
        # statistic_events['RadioTXBitsMean'].append(val.RadioTXBitsMean)
        # for k, v in val.items():
        #     statistic_events[k].append(v)
    
    ns.Simulator.Destroy()

    return field_mapping
