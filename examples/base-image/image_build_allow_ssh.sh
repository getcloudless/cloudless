#! /bin/bash

# This is a startup script that will be passed to both AWS and GCE instances.  The image build
# framework runs the blueprint with the options "cloudless_image_build_ssh_key" and
# "cloudless_image_build_ssh_username", so we have to have this script to properly install that
# user.

{% if cloudless_image_build_ssh_key %}
adduser "{{ cloudless_image_build_ssh_username }}" --disabled-password --gecos "Cloudless Test User"
echo "{{ cloudless_image_build_ssh_username }} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
mkdir /home/{{ cloudless_image_build_ssh_username }}/.ssh/
echo "{{ cloudless_image_build_ssh_key }}" >> /home/{{ cloudless_image_build_ssh_username }}/.ssh/authorized_keys
{% endif %}
