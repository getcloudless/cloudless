#! /bin/bash

{% if cloudless_test_framework_ssh_key %}
adduser "{{ cloudless_test_framework_ssh_username }}" --disabled-password --gecos "Cloudless Test User"
echo "{{ cloudless_test_framework_ssh_username }} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
mkdir /home/{{ cloudless_test_framework_ssh_username }}/.ssh/
echo "{{ cloudless_test_framework_ssh_key }}" >> /home/{{ cloudless_test_framework_ssh_username }}/.ssh/authorized_keys
{% endif %}

curl https://releases.hashicorp.com/consul/1.2.3/consul_1.2.3_linux_amd64.zip --output consul.zip
apt-get install -y unzip
unzip consul.zip
mkdir /var/consul
./consul agent --data-dir /var/consul/ --bootstrap-expect 3 --server=true

./consul agent --data-dir /var/consul/ --bootstrap-expect 3 --server=true --retry-join "10.0.0.2"
