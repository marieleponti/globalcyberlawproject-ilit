#!/usr/bin/env bash
#
# Safe loader for .env.production. Source this, then call `load_env <file>`.
#
# Why this exists instead of `set -a; source .env.production; set +a`:
#
# `source` runs the file as shell script. A generated secret such as
#
#     SECRET_KEY=dhCYlWLmo3pwuW4BU^jiaT3b2fT&x(9)
#
# is not an assignment to bash, it is an assignment followed by commands, pipes
# and subshells. The result is "command not found" at best, and arbitrary
# execution of whatever the random generator happened to produce at worst.
# Docker Compose reads the same file literally and never had this problem, so
# the application worked while every ops script broke.
#
# This reads KEY=VALUE pairs as data. Values are never evaluated, so any
# character is safe, and secrets do not have to be weakened to suit the shell.

load_env() {
    local file="${1:?load_env necesita la ruta del archivo}"
    local line key value

    if [[ ! -f "$file" ]]; then
        echo "ERROR: no encuentro $file" >&2
        return 1
    fi

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip blanks and comments.
        [[ -z "${line//[[:space:]]/}" ]] && continue
        [[ "${line#"${line%%[![:space:]]*}"}" == \#* ]] && continue
        [[ "$line" != *=* ]] && continue

        key="${line%%=*}"
        value="${line#*=}"

        # Trim surrounding whitespace from the key only; values are taken
        # verbatim, since trailing spaces can be meaningful in a passphrase.
        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"

        # Ignore anything that is not a valid shell identifier rather than
        # trying to export it.
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

        # Strip one layer of matching quotes, the way Compose does.
        if [[ "$value" == \"*\" && ${#value} -ge 2 ]]; then
            value="${value:1:${#value}-2}"
        elif [[ "$value" == \'*\' && ${#value} -ge 2 ]]; then
            value="${value:1:${#value}-2}"
        fi

        export "${key}=${value}"
    done < "$file"
}
