fancontrol-hddtemp
==================

Simplistic script to control PWM output in relation to HDD/SSD temperatures.
Does not contain any more features (like settings fan to full speed on exit).
Needs https://github.com/guzu/hddtemp

For more advanced scripts, check:
* https://github.com/KostyaEsmukov/afancontrol
* fancontrol script from https://github.com/lm-sensors/lm-sensors

Note: the hddtemp method got obsoleted with Linux kernel 5.6, where
drive temperatures are reported through hwmon subsystem.

