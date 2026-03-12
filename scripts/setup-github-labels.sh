#!/usr/bin/env bash
# DEPRECATED: This script is a wrapper for backward compatibility.
# Use scripts/setup-labels.sh instead, which supports both GitHub and GitLab.
exec bash "$(dirname "$0")/setup-labels.sh" "$@"
