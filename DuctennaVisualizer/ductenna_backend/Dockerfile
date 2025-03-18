FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Install dependencies
RUN apt-get update && apt-get install -y --fix-broken

RUN apt-get install -y \
    libusb-1.0-0 \
    avahi-daemon \
    libavahi-common3 \
    libavahi-client3 \
    libavahi-core7 \
    libdaemon0 \
    libdbus-1-3 \
    libexpat1 \
    libtinfo5 \
    libgpm2 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxinerama1 \
    libxrandr2 \
    libftdi1-2 \
    libjpeg62-turbo \
    libpng16-16 \
    libc6 \
    libncurses5 \
    libstdc++6 \
    wget \
    libpsl5 \
    xdg-utils \
    digilent.adept.runtime \
    libqt5multimedia5-plugins \
    libqt5scripttools5 \
    libqt5network5 \
    libqt5serialport5

RUN mkdir -p /usr/share/desktop-directories/
# Copy both .deb files into the container
COPY digilent.adept.runtime_2.27.9-arm64.deb /tmp/adept.deb
COPY digilent.waveforms_3.23.4_arm64.deb /tmp/waveforms.deb

# Install Adept SDK first, then WaveForms SDK
RUN dpkg -i /tmp/adept.deb || apt-get -fy install
RUN dpkg -i /tmp/waveforms.deb || apt-get -fy install

# Clean up
RUN rm /tmp/adept.deb /tmp/waveforms.deb

# Ensure the library is available
ENV LD_LIBRARY_PATH=/usr/lib

CMD ["python", "ductenna_backend.py"]
