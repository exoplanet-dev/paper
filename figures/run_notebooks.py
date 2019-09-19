#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import re
import sys
import multiprocessing

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor

if len(sys.argv) >= 2:
    pattern = sys.argv[1]
else:
    pattern = "*.ipynb"

filenames = [fn for fn in glob.glob(pattern) if not fn.endswith("_exec.ipynb")]

num_files = len(filenames)
cpu_count = multiprocessing.cpu_count()
num_jobs = min(1, cpu_count // 4)
print("Running on {0} CPUs".format(cpu_count))
print("Running {0} jobs".format(num_jobs))


def process_notebook(filename):
    errors = []

    with open(filename) as f:
        notebook = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=-1)

    print("running: {0}".format(filename))
    try:
        ep.preprocess(notebook, {"metadata": {"path": "."}})
    except CellExecutionError as e:
        msg = "error while running: {0}\n\n".format(filename)
        msg += e.traceback
        print(msg)
        errors.append(msg)
    finally:
        with open(
            os.path.splitext(filename)[0] + "_exec.ipynb", mode="wt"
        ) as f:
            nbformat.write(notebook, f)

    return "\n\n".join(errors)


with multiprocessing.Pool(num_jobs) as pool:
    errors = list(pool.imap_unordered(process_notebook))

errors = [e for e in errors if len(e.strip())]
txt = "\n\n".join(errors)
ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
txt = ansi_escape.sub("", txt)

with open("notebook_errors.log", "wb") as f:
    f.write(txt.encode("utf-8"))

sys.exit(len(errors))
