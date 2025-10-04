# STYLE.md - notes for LLM assistants

A few notes to consider when helping me write Python on this project:

GO HEAVY ON COMMENTS AND DOCSTRINGS. Explanatory comments are highly desirable and should be added liberally. I may be coming back to this project years in the future when I've forgotten all the context and background. I may share this code with someone who does not know Python at all. 

CODE IN A STRUCTURED, PRECISE STYLE. Validate inputs rigorously. Aggresively include type hints. Handle exceptions with `try/except/finally/else` blocks. Design for graceful failures, and make sure those failures are verbose and logged.

ALWAYS PREFER PYTHON'S STANDARD LIBRARY. You should never suggest the use of a third-party modules unless I ask you to. I strongly prefer using Python's standard library for my tasks.

USE THE RIGHT TOOL FOR THE JOB. Use the `pathlib` module for working with the filesystem, not the `os` module. Use `argparse` to construct command-line interfaces. Use `logging` to log everything the script does. Use `shutil` for file copying, moving, or deletion rather than manual path manipulation. Use `tempfile` when creating transient files. Use `subprocess` instead of `os.system` when running system commands. Use `dataclasses` or `typing.NamedTuple` for structured data. Use `enum` for sets of named constants.

USE EXIT CODES. When our script exits, it must return [a value that indicates the circumstances of its termination](https://tldp.org/LDP/abs/html/exitcodes.html). Not all of these will be relevant to our script, but when our script terminates with one of these situations it MUST indicate that via exit codes. This [link](https://tldp.org/LDP/abs/html/exitcodes.html) suggests we restrict any custom exit codes to the numbers 64 through 113, while [this link](https://man7.org/linux/man-pages/man3/sysexits.h.3head.html) further defines codes for 64 through 78. Therefore, any additional codes we define MUST be in the range 79 through 113. The existing codes are:
- *0 -- Success.*
- *1 -- General error (not otherwise defined).* Miscellaneous errors, such as "divide by zero" and other impermissible operations.
- *2 -- Usage error.* Missing keyword or command, or a permission problem. Not relevant for our script.
- *64 -- EX_USAGE.* The command was used incorrectly, e.g., with the wrong number of arguments, a bad flag, a bad syntax in a parameter, or whatever.
- *65 -- EX_DATAERR.* The input data was incorrect in some way. This should only be used for user's data, not system files.
- *66 -- EX_NOINPUT.* An input file (not a system file) did not exist or was not readable. This could be a missing configuration file explicitly specified by the user.
- *67 -- EX_NOUSER.* The specified user did not exist. Rare for our script; only use if we validate system usernames.
- *68 -- EX_NOHOST.* The specified host did not exist. Use if network hostnames provided by the user cannot be resolved.
- *69 -- EX_UNAVAILABLE.* A required service or resource is unavailable (e.g., dependent external command or network service temporarily down).
- *70 -- EX_SOFTWARE.* Internal software error: e.g., an unexpected invariant failure or unhandled condition we deliberately trap and classify.
- *71 -- EX_OSERR.* Operating system error (e.g., cannot fork, low-level I/O error) outside the user's control.
- *72 -- EX_OSFILE.* A system file (e.g., `/etc/hosts`) does not exist, is inaccessible, or has invalid format—distinct from user-provided files (see 66).
- *73 -- EX_CANTCREAT.* Cannot create (user-specified) output file or required path component.
- *74 -- EX_IOERR.* An I/O error occurred while doing any sort of read/write (after the file was successfully opened / created).
- *75 -- EX_TEMPFAIL.* Temporary failure: the operation may succeed if retried later (e.g., transient network glitch, lock contention). Caller may retry.
- *76 -- EX_PROTOCOL.* Protocol error: remote system violated a defined protocol; data stream inconsistent or malformed at the protocol layer.
- *77 -- EX_NOPERM.* Permission denied: not authorized to perform the requested operation (after confirming path/object exists).
- *78 -- EX_CONFIG.* Configuration error: something in system or application configuration is incorrect, inconsistent, or missing.
- *126 -- Command invoked cannot execute.* Permission problems, or the command is simply not executable (like `/dev/null`). Not relevant for our script.
- *127 -- "Command not found."* Possibly a problem with the `$PATH`, or simply a typo on the part of the user. Not relevant for our script.
- *130 -- Script terminated by `Ctrl-C` (SIGINT).*

MAINTAIN COMPATIBILITY WITH PYTHON 3.12 AND ABOVE. This is fairly self-explanatory, but the oldest versions of Python that will be running this script are Python 3.12. We cannot allow any code incompatible with Python 3.12.