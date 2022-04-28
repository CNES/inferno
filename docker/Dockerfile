FROM ubuntu:20.04

# Change user (not root)
# Can be set at building
ARG UNAME=user
ARG UID=1000
ARG GID=1000
# GID, UID, UNAME can be overrided by --build-arg GID (ie) during building
RUN groupadd -g $GID -o $UNAME \
    && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME
USER $UNAME

# Install OTB from binary distribution
WORKDIR /tmp

ARG OTB_VERSION=7.4.0
ENV DEBIAN_FRONTEND noninteractive
LABEL OTB="${OTB_VERSION}"
ENV OTB_INSTALL_DIRNAME=/opt/otb-${OTB_VERSION}
ENV DIAPOTB_INSTALL_DIRNAME=/opt/diapotb
ENV SNAPHU_INSTALL_DIRNAME=/usr/local/bin

# ----------------------------------------------------------------------------
# External files that need to be present in curent directory
# ----------------------------------------------------------------------------
ADD OTB-${OTB_VERSION}-Linux64.run /tmp
ADD gdal-config /tmp
ADD inferno-develop.tar.gz /tmp

# As ROOT
USER root

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    file apt-utils \
    && apt-get install -y sudo build-essential \
    g++ cmake make git freeglut3-dev emacs \
    libpython3.8 python3 python3-dev python3-numpy python3-pip \
    && dpkg -l | grep libpython3.8 \
    && echo "Make sure we have libpython3.8m.so" \
    && find /usr/lib -name "libpython3.8*.so*" | grep "." 

RUN ln -s $(find /usr/lib -name "libpython3.7*.so*" | grep "."  | head -n 1) /usr/lib/x86_64-linux-gnu/libpython3.5m.so.rh-python35-1.0

# Create directories and change to $UNAME
RUN chown -R $UID:$GID /tmp \
    && mkdir $OTB_INSTALL_DIRNAME \
    && mkdir $DIAPOTB_INSTALL_DIRNAME \
    && mkdir /opt/env \
    && chown -R $UID:$GID $OTB_INSTALL_DIRNAME  \
    && chown -R $UID:$GID $DIAPOTB_INSTALL_DIRNAME \
    && chown -R $UID:$GID /opt/env

# Change user (not root anymore but sudoers)
RUN sudo usermod -a -G sudo $UNAME \
    && echo "$UNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER $UNAME


# Install OTB for binary distribution and copy gdal-config in bin/
RUN chmod +x ./OTB-${OTB_VERSION}-Linux64.run \
    && ./OTB-${OTB_VERSION}-Linux64.run --target "${OTB_INSTALL_DIRNAME}"\
    && chmod +x ./gdal-config \
    && mv ./gdal-config "${OTB_INSTALL_DIRNAME}/bin" \
    && sudo ln -s ${OTB_INSTALL_DIRNAME}/bin/gdal-config /bin/gdal-config \
    && rm -rf ./OTB-${OTB_VERSION}-Linux64.run

RUN echo "# Patching for diapotb" >> "${OTB_INSTALL_DIRNAME}/otbenv.profile" \
    && echo 'export LD_LIBRARY_PATH="${CMAKE_PREFIX_PATH}/lib:${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"' >> "${OTB_INSTALL_DIRNAME}/otbenv.profile"

# Bind OTB to Python
RUN cd ${OTB_INSTALL_DIRNAME} \
    && . "${OTB_INSTALL_DIRNAME}/otbenv.profile" \
    && ctest -S share/otb/swig/build_wrapping.cmake -VV \
    && cd ..

# Install DiapOTB (python_src, only)
WORKDIR $DIAPOTB_INSTALL_DIRNAME

RUN git clone https://gitlab.orfeo-toolbox.org/remote_modules/diapotb.git . \
    && git checkout python_TSX

# Install python src (Install numpy and gdal, first)
# setuptools is a requirements to install DiapOTB, use v57.0.0to avoid conflicts with gdal (v 3.2.2)
RUN cd python_src \
    && . "${OTB_INSTALL_DIRNAME}/otbenv.profile" \
    &&  python3 -m pip --no-cache-dir install --upgrade pip \
    &&  python3 -m pip --no-cache-dir install setuptools==57.0.0 \
    &&  python3 -m pip --no-cache-dir install numpy==1.20 \
    &&  python3 -m pip --no-cache-dir install "gdal==$(gdal-config --version)" \
    && python3 -m pip --no-cache-dir install .

# ---------------------------------------------------------------

# ---------------------------------------------------------------
# This fix: libGL error: No matching fbConfigs or visuals found
ENV LIBGL_ALWAYS_INDIRECT=1
 
# install SNAPHU
RUN cd /tmp/inferno-develop/ \
    && mkdir ./snaphu-v2.0.5/bin \
    && sudo mkdir -p /usr/local/man/man1/ \
    && cd ./snaphu-v2.0.5/src \
    && sudo make install \
    && sudo make Clean


# Install inferno
RUN cd /tmp/inferno-develop \
    && sudo apt-get update && sudo apt-get install -y python3-pyqt5 \
    && python3 -m pip --no-cache-dir install . \ 
    && rm -rf /tmp/inferno-develop

ENV PATH=/home/user/.local/bin:$PATH

RUN sudo apt install python-is-python3

RUN touch /opt/env/run_inferno.sh \
    && echo "#!/bin/sh" >> /opt/env/run_inferno.sh \
    && echo "export LC_ALL=C.UTF-8" >> /opt/env/run_inferno.sh \
    && echo "export LANG=C.UTF-8" >> /opt/env/run_inferno.sh \
    && echo ". ${OTB_INSTALL_DIRNAME}/otbenv.profile" >> /opt/env/run_inferno.sh \
    && echo "export LD_LIBRARY_PATH=\${OTB_INSTALL_DIRNAME}/lib:\$LD_LIBRARY_PATH" >> /opt/env/run_inferno.sh \
    && echo "LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH">>/opt/env/run_inferno.sh \
    && echo "inferno \$@" >> /opt/env/run_inferno.sh \
    && chmod +x /opt/env/run_inferno.sh

ENTRYPOINT ["/opt/env/run_inferno.sh"]