FROM ros:jazzy-ros-base AS base

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu130
ARG GENESIS_VERSION=

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_SOURCE=/opt/ros/${ROS_DISTRO}/setup.bash


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    python3-venv \
    python3-pip \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-ros2-controllers \
    libgl1 \
    libegl1 \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libx11-6 && \
    rm -rf /var/lib/apt/lists/*

 
RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip install --no-cache-dir torch --index-url ${TORCH_INDEX_URL}
RUN pip install --no-cache-dir "genesis-world${GENESIS_VERSION:+==$GENESIS_VERSION}"

COPY src /tmp/src
RUN apt-get update && \
    rosdep update --rosdistro ${ROS_DISTRO} && \
    rosdep install --from-paths /tmp/src --ignore-src -y --rosdistro ${ROS_DISTRO} && \
    rm -rf /tmp/src /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID
ARG USER_GID

ENV COLCON_WS=/home/${USERNAME}/genesis_ws

RUN userdel -r ubuntu 2>/dev/null || true && \
    (getent group ${USER_GID} || groupadd -g ${USER_GID} ${USERNAME}) && \
    useradd -m -s /bin/bash -u ${USER_UID} -g ${USER_GID} ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

RUN echo "source ${ROS_SOURCE}" >> /etc/bash.bashrc && \
    echo "[ -f ${COLCON_WS}/install/setup.bash ] && source ${COLCON_WS}/install/setup.bash" >> /etc/bash.bashrc

USER ${USERNAME}
RUN rosdep update --rosdistro ${ROS_DISTRO}
WORKDIR ${COLCON_WS}