#!/bin/bash
cp kigvision.service /etc/systemd/system/
systemctl enable kigvision.service
systemctl start kigvision.service
systemctl status kigvision.service
