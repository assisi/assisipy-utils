# hooks - rationale and usage

The `post-commit` hook is to generate a file containing a version number, which
is used in conjunction with the library functions in `common/tool_version.py`.
It includes a git revision of the tool version, for improved traceability in 
development mode.

To use this script, either copy into the ^/.git/hooks directoy, or link it.
This command will perform the linking from any location within the repository.

    ln -s  "$(git rev-parse --show-toplevel)"/hooks/post-commit "$(git rev-parse --show-toplevel)"/.git/hooks

