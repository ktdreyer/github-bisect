CI is failing. It used to pass. How to fix?

This tool will look at the most recent passing job, and compare the log output of that job to the log output of the earliest job that failed.

Example to look at the failing training jobs:

```
python github-bisect.py instructlab training main
```

## Things this tool can do:

- Auto-determine the latest run that passed and:

  - The next one that failed,

  - Or the most-recent one that failed, since many other things have changed and the cause may be different. Also, that is where you will want to land a fix.

- Print a table of Python libraries that changed between passing and failing runs.

## Future ideas:

- Print humanized dates for the pass/fail history on a given job, so that we know if the job has very flakey and unreliable, or if the failures are important enough to pay attention.

- Show an error if we're doubly-installing libraries with different versions (pytorch 2.7.0 and then downgrading to 2.6.0)
