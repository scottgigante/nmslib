import abc
import sys
import multiprocessing

if sys.version.split(".")[0] == "2":
    abstractproperty = abc.abstractproperty
else:
    abstractproperty = lambda f: property(abc.abstractmethod(f))


def parse_n_jobs(n_jobs):
    n_jobs = int(n_jobs)
    if n_jobs <= 0:
        n_jobs = multiprocessing.cpu_count() + 1 + n_jobs
    return n_jobs
