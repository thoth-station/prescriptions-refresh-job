#!/usr/bin/env sh
#
# This script is run by OpenShift's s2i. Here we guarantee that we run desired
# sub-command based on env-variables configuration.
#

[ -z "${THOTH_PRESCRIPTIONS_REFRESH_SUBCOMMAND}" ] && {
    echo "No sub-command defined in THOTH_PRESCRIPTIONS_REFRESH_SUBCOMMAND environment variable" >&2
    exit 1
}

exec /opt/app-root/bin/python3 thoth-prescriptions-refresh "${THOTH_PRESCRIPTIONS_REFRESH_SUBCOMMAND}"
