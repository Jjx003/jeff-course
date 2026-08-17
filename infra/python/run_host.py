"""
Warm run host for jeff-course baremetal Python execution.

The problem this solves: every Run used to pay for interpreter startup plus
`import torch` (3-10s) plus CUDA context init before a single line of the
learner's code executed. This host pays that cost *once*, while the learner
is still reading the problem statement, and then blocks waiting for work.

Protocol (deliberately tiny, so Node needs no ZMQ binding):

  1. Import everything named in $JEFF_PREWARM (comma separated).
  2. Write the ready sentinel to stderr and flush. Node treats the process
     as available from this point and discards everything printed before it.
  3. Block on one line of JSON from stdin: {"path": "...", "argv": [...]}.
  4. Execute that file as __main__ and exit with its status code.

One run per host, then the process dies and the pool starts a replacement.
That matters for two reasons: the learner's namespace is always fresh (so
stdout-diff grading stays sound, and nothing leaks between users), and a
run that corrupts interpreter state can't poison the next one. The only
thing that survives is the contents of sys.modules, which is exactly the
part we wanted to keep.

Executed by `uv run ... python run_host.py` - see runtime/pool.ts.
"""

import json
import os
import runpy
import sys
import traceback

READY_SENTINEL = "__JEFF_COURSE_HOST_READY__"


def _prewarm(module_names):
    """Import each module, ignoring failures.

    A prewarm miss is not fatal: the module may simply not be installed in
    this requirement set, and the learner's own import will raise a proper
    error at run time if it actually needed it.
    """
    for name in module_names:
        try:
            __import__(name)
        except Exception:
            pass


def _user_traceback(exc, script_path):
    """Format a traceback trimmed to the learner's own frames.

    Without this, every uncaught exception would be topped by run_host.py
    and runpy frames that mean nothing to someone debugging their solution.
    """
    tb = exc.__traceback__
    target = os.path.abspath(script_path)
    walker = tb
    while walker is not None:
        if os.path.abspath(walker.tb_frame.f_code.co_filename) == target:
            tb = walker
            break
        walker = walker.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb))


def _run(script_path, argv):
    sys.argv = list(argv)
    # `python script.py` puts the script's directory first on sys.path;
    # runpy.run_path does not, so we match CPython's behaviour explicitly.
    sys.path.insert(0, os.path.dirname(os.path.abspath(script_path)))

    try:
        runpy.run_path(script_path, run_name="__main__")
        return 0
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        sys.stderr.write("%s\n" % (code,))
        return 1
    except BaseException as exc:  # noqa: BLE001 - mirror the interpreter
        sys.stderr.write(_user_traceback(exc, script_path))
        return 1
    finally:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass


def main():
    _prewarm([m for m in os.environ.get("JEFF_PREWARM", "").split(",") if m])

    sys.stderr.write(READY_SENTINEL + "\n")
    sys.stderr.flush()

    line = sys.stdin.readline()
    if not line.strip():
        # Pool evicted us before any work arrived.
        return 0

    try:
        command = json.loads(line)
        script_path = command["path"]
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("run_host: malformed command: %s\n" % (exc,))
        return 1

    return _run(script_path, command.get("argv") or [script_path])


if __name__ == "__main__":
    sys.exit(main())
