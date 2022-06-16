CC=g++
CCFLAGS=-std=c++14 -I../resources/radiotap-library -I.
LDFLAGS= -L../resources/build
TARGET=pcap
TARGET_LIBS=../resources/build

all: $(TARGET)

$(TARGET): pcap.cpp defines.h http.o pcap_handler.o config.o
	$(CC) $(CCFLAGS) $(LDFLAGS) pcap.cpp -o pcap http.o pcap_handler.o config.o -lpcap -lradiotap -lPocoNet

%.o: %.cpp %.h
	$(CC) $(CCFLAGS) -c $< -o $@
