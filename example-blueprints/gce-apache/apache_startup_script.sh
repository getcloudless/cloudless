#! /bin/bash

{% if cloudless_test_framework_ssh_key %}
adduser "{{ cloudless_test_framework_ssh_username }}" --disabled-password --gecos "Cloudless Test User"
usermod -aG sudo "{{ cloudless_test_framework_ssh_username }}"
echo "{{ cloudless_test_framework_ssh_username }}" ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
mkdir /home/"{{ cloudless_test_framework_ssh_username }}"/.ssh/
chown "{{ cloudless_test_framework_ssh_username }}" /home/"{{ cloudless_test_framework_ssh_username }}"/.ssh/
echo "{{ cloudless_test_framework_ssh_key }}" >> /home/"{{ cloudless_test_framework_ssh_username }}"/.ssh/authorized_keys
chown -R "{{ cloudless_test_framework_ssh_username }}" /home/"{{ cloudless_test_framework_ssh_username }}"/.ssh/
{% endif %}

apt-get update
apt-get install -y apache2
cat <<EOF > /var/www/html/index.html
<html><body><h1>Hello World</h1>
<p>This page was created from a simple startup script!</p>
</body></html>
EOF
