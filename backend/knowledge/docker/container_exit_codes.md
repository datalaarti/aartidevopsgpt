\# Docker Container Exit Codes



A Docker container with a non-zero exit code indicates that the

main process inside the container terminated unsuccessfully.



Exit code 1 is a generic application error.



Exit code 125 is commonly associated with Docker itself being

unable to execute the container command.



Exit code 126 indicates that the container command could not

be invoked.



Exit code 127 indicates that the command could not be found.



Exit codes above these values can be application-specific.

The exit code alone should not be used as the root cause. Always

inspect container logs, the container state, command, entrypoint,

environment, mounts, and related configuration.

