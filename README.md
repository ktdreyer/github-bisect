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

## Other ways to bisect failures:

The `gh` CLI tool can display human-readable deltas for the last time a job succeeded:

```
gh run list --workflow e2e-nvidia-l40s-x4.yml -s success
STATUS  TITLE                 WORKFLOW              BRANCH  EVENT     ID           ELAPSED   AGE
✓       E2E (NVIDIA L40S x4)  E2E (NVIDIA L40S x4)  main    schedule  14550704806  3h59m45s  about 8 days ago
✓       E2E (NVIDIA L40S x4)  E2E (NVIDIA L40S x4)  main    schedule  12735039001  2h26m1s   about 3 months ago
✓       E2E (NVIDIA L40S x4)  E2E (NVIDIA L40S x4)  main    schedule  12725634517  2h26m51s  about 3 months ago
✓       E2E (NVIDIA L40S x4)  E2E (NVIDIA L40S x4)  main    schedule  12712906169  2h27m55s  about 3 months ago
✓       E2E (NVIDIA L40S x4)  E2E (NVIDIA L40S x4)  main    schedule  12693703629  2h27m23s  about 3 months ago
```

This shows that (with one exception eight days ago), this job succeeded one time in the past three months.

This tells us if a job has very flakey and unreliable, or if the failures are important enough to pay attention.

## Future ideas:

- Show an error if we're doubly-installing libraries with different versions (pytorch 2.7.0 and then downgrading to 2.6.0)
