#!/bin/sh
set -e

DOCKER_USER='dockeruser'
DOCKER_GROUP='dockergroup'


if ! id "$DOCKER_USER" >/dev/null 2>&1; then
    echo "First start of the docker container, start initialization process."

    USER_ID=${PUID:-1000}
    GROUP_ID=${PGID:-1001}
    echo "Starting with $USER_ID:$GROUP_ID (UID:GID)"

    # Check if the desired GROUP_ID is already in use
    if getent group $GROUP_ID >/dev/null 2>&1; then
        EXISTING_GROUP=$(getent group $GROUP_ID | cut -d: -f1)
        echo "GID $GROUP_ID is already in use by group $EXISTING_GROUP. Using this group."
        DOCKER_GROUP=$EXISTING_GROUP
    else
        addgroup --gid $GROUP_ID $DOCKER_GROUP
        echo "Created group $DOCKER_GROUP with GID $GROUP_ID."
    fi

    # Check if the desired USER_ID is already in use
    if id -u $USER_ID >/dev/null 2>&1; then
        EXISTING_USER=$(getent passwd $USER_ID | cut -d: -f1)
        echo "UID $USER_ID is already in use by user $EXISTING_USER. Using this user."
        DOCKER_USER=$EXISTING_USER
    else
        # Create user with the specified UID and associated group
        adduser --shell /bin/sh --uid $USER_ID --ingroup $DOCKER_GROUP --disabled-password --gecos "" $DOCKER_USER
        echo "Created user $DOCKER_USER with UID $USER_ID."
    fi

    # Set ownership and permissions
    chown -vR $USER_ID:$GROUP_ID /src

fi

export HOME=/home/$DOCKER_USER
exec gosu $DOCKER_USER:$DOCKER_GROUP "$@"