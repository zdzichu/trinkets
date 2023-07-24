## k3s cleanup

Each version of k3s unpacks its data in `/var/lib/rancher/k3s/data`. Those directories may
pile up, especially when using https://github.com/rancher/system-upgrade-controller

This little daemonset runs a script, which removes stale data every week. It leaves
only *current* and *previous* versions directories.
