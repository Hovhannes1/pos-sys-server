import time
from math import log10, sqrt

from flask import Flask, request
from sqlalchemy import (Column, Float, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

application = Flask(__name__)

sqlEngine = create_engine('sqlite:///rssi.db')
sqlSession = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=sqlEngine))
sqlBase = declarative_base()

# Access point class


class AccessPoint(sqlBase):
    __tablename__ = "accesspoint"
    id = Column(Integer, primary_key=True)
    mac_address = Column(String)

# Location class


class Location(sqlBase):
    __tablename__ = "location"
    id = Column(Integer, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)


class Sample(sqlBase):
    __tablename__ = "sample"
    ap_id = Column(Integer, ForeignKey("accesspoint.id"))
    source_address = Column(String, nullable=False, primary_key=True)
    timestamp = Column(Float, nullable=False, primary_key=True)
    rssi = Column(Float, nullable=False)
    ap = relationship("AccessPoint", backref="sample")


class FingerprintValue(sqlBase):
    __tablename__ = "fingerprint_value"
    id = Column(Integer, primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.id"))
    ap_id = Column(Integer, ForeignKey("accesspoint.id"))
    rssi = Column(Float, nullable=False)
    location = relationship("Location", backref="fingerprint_value")
    ap = relationship("AccessPoint", backref="fingerprint_value")


class DeviceCalibration(sqlBase):
    __tablename__ = "device_calibration"
    mac_address = Column(String, primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.id"))
    location = relationship("Location", backref="device_calibration")


@application.route("/rssi", methods=['GET', 'POST'])
def rssi():
    if request.method == 'GET':
        initData = request.args.to_dict()
        missing = sqlSession.query(AccessPoint).filter_by(
            mac_address=initData['ap']).first()
        if missing is None:
            accessPoint = AccessPoint(mac_address=initData['ap'])
            sqlSession.add(accessPoint)
            sqlSession.commit()
            print(initData['ap'])

        for key in initData:
            if key != 'ap':
                ap1 = sqlSession.query(AccessPoint).filter_by(
                    mac_address=initData['ap']).first()
                Sample_data = Sample(ap_id=ap1.id, source_address=key, timestamp=time.time(
                ), rssi=initData[key], ap=ap1)
                sqlSession.add(Sample_data)
                sqlSession.commit()

        deviceCalibratData = sqlSession.query(DeviceCalibration).filter(
            DeviceCalibration.mac_address == ap1.mac_address).all()
        for c_data in deviceCalibratData:
            loc = c_data.location
            allSamples = sqlSession.query(Sample).filter(
                Sample.source_address == ap1.mac_address).filter(Sample.timestamp >= (time.time() - 1)).all()
            allSamples = sqlSession.query(Sample).filter(
                Sample.source_address == ap1.mac_address).all()
            print(ap1.mac_address)
            if (allSamples is not None):
                for sample in allSamples:
                    fingerprint_value = FingerprintValue(
                        loc_id=loc.id, ap_id=sample.ap.id, rssi=sample.rssi, location=loc, ap=sample.ap)
                    sqlSession.add(fingerprint_value)
                    sqlSession.commit()
    return "Updated the DataBase"


@application.route("/start_calibration", methods=['GET', 'POST'])
def start_calibration():
    if request.method == 'GET':
        # get data from the request
        initData = request.args.to_dict()
        # check if the location is missing
        checkLoc = sqlSession.query(Location).filter_by(
            x=initData['x'], y=initData['y'], z=initData['z']).first()
        print(checkLoc)
        if checkLoc is None:
            print("Location is missing so we add location in table")
            loc = Location(x=initData['x'],
                           y=initData['y'], z=initData['z'])
            sqlSession.add(loc)
            sqlSession.commit()

        secondLoc = sqlSession.query(Location).filter_by(
            x=initData['x'], y=initData['y'], z=initData['z']).first()

        # check if the mac adress is missing
        checkMacAdress = sqlSession.query(DeviceCalibration).filter_by(
            mac_address=initData['mac_addr']).first()
        if checkMacAdress is None:
            print("Mac address is missing so we add in Calibrating mobile table")
            calibrateData = DeviceCalibration(
                mac_address=initData['mac_addr'], loc_id=secondLoc.id, location=secondLoc)
            sqlSession.add(calibrateData)
            sqlSession.commit()

        allSamples = sqlSession.query(Sample).filter_by(
            source_address=initData['mac_addr']).all()
        for samp in allSamples:
            diff = time.time_ns() - samp.timestamp
            if diff < 10000000000000:
                print("Sample is less older so adding it to the FingerPrint Value Table")
                try:
                    ap2 = sqlSession.query(AccessPoint).filter_by(
                        mac_address=initData['mac_addr']).first()
                    finger_val = FingerprintValue(
                        loc_id=secondLoc.id, ap_id=ap2.id, rssi=samp.rssi, location=secondLoc, ap=ap2)
                    sqlSession.add(finger_val)
                    sqlSession.commit()
                except:
                    print("Access_point is not saved in Databasse")
    return "The calibration has succesfully Done"


@application.route("/stop_calibration", methods=['GET', 'POST'])
def stop_calibration():
    if request.method == 'GET':
        initData = request.args.to_dict()
        allMacAddr = sqlSession.query(DeviceCalibration).filter_by(
            mac_address=initData['mac_addr']).all()
        for mac in allMacAddr:
            print(mac)
            sqlSession.delete(mac)
            sqlSession.commit()
    return "Calibration is succefully Stopped"


def rssi_dist(arr1, arr2):
    return sqrt(pow(rssi_average(arr1) - rssi_average(arr2), 2))


def rssi_average(arr):
    total = 0
    for x in arr:
        total += 10 ** (x / 10.0)
    return 10 * log10(total / len(arr))


@application.route("/locate", methods=['GET', 'POST'])
def locate():
    sampleRSSiArray = []
    locationIDs = []
    for value in sqlSession.query(FingerprintValue.loc_id).distinct():
        locationIDs.append(value.loc_id)
    print(locationIDs)
    if request.method == 'GET':
        initData = request.args.to_dict()
        allSamples = sqlSession.query(Sample).filter_by(
            source_address=initData['mac_addr']).all()
        for samp in allSamples:
            diff = time.time() - samp.timestamp
            if diff < 10000000000000:
                sampleRSSiArray.append(samp.rssi)
    minRSSI = 9999999
    finalLocId = -1
    for id in locationIDs:
        tmp = []
        for value in sqlSession.query(FingerprintValue).filter_by(loc_id=id).all():
            tmp.append(value.rssi)
        print(tmp)
        dist = rssi_dist(sampleRSSiArray, tmp)
        if dist < minRSSI:
            minRSSI = dist
            finalLocId = id
    if finalLocId == -1:
        return "unavailable"
    coordinate = sqlSession.query(Location).filter_by(id=finalLocId).first()
    print(sampleRSSiArray)
    result = "Location Calculated is :  x:{} y:{} z:{}".format(
        coordinate.x, coordinate.y, coordinate.z)
    return result


if __name__ == '__main__':
    application.run(debug=True)
