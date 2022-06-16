#include <map>
#include <set>
#include <cmath>
#include <iostream>
#include "http.h"
#include <Poco/Net/Net.h>
#include <Poco/Net/HTTPClientSession.h>
#include <Poco/URI.h>
#include <Poco/Exception.h>
#include <Poco/Net/HTTPRequest.h>
#include <Poco/Net/HTMLForm.h>
#include <Poco/Net/NetException.h>



using namespace std;
using namespace Poco::Net;
float to_dbm(float mw){
    return std::log10(mw) * 10;
}

float to_mw(float dbm){
    return (float) pow(10.0, dbm / 10.0);
}
float average(vector<float> rssi_values){
    float sum_mw = 0;
    for (auto i: rssi_values) {
        sum_mw+= to_mw(i);
    }
    return to_dbm(sum_mw);
}

void send_samples(RSSILog samples, string ap_mac_addr) {


    * TODO: Implement this function
    * It takes two parameters:
    * 	- samples with RSSI samples ordered by reception time
    * 	- ap_mac_addr the Raspberry Pi MAC address
    *
    * It must send its MAC address as variable name ap
    * and a list of pairs DeviceMAC=RSSI where each DeviceMAC is unique
            * and RSSI are average RSSI values when multiple values exist for a
            * given DeviceMAC
            *
            * The packet must be sent to http://localhost:8080/rssi
            *
            * HTTP requests handling use Poco::Net API
            * */
            // TODO: your code here

    Configuration* cfg = Configuration::getInstance();
    string port = to_string(cfg->getServerPort());
    string host = cfg->getServerHost();
    string parameters = "?ap="+ap_mac_addr;
    map<string, vector<float>> device_mac_rssi;
    for (int i = 0; i < samples.size(); ++i) {
        device_mac_rssi[samples[i].mac_address].push_back(samples[i].rssi);
    }
    for (auto it = device_mac_rssi.begin(); it != device_mac_rssi.end(); ++it) {
        parameters +="&"+it->first+"="+ to_string(average(it->second));
    }
    string url = "http://"+host+":"+port+"/rssi"+parameters;
    Poco::Net::HTTPClientSession session(host, cfg->getServerPort());
    Poco::Net::HTTPRequest request(Poco::Net::HTTPRequest::HTTP_GET, url, Poco::Net::HTTPMessage::HTTP_1_1);
    session.sendRequest(request);

}


