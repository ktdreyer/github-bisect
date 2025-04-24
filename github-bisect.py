import argparse
import github
import sys
from netrc import netrc
import requests
from pathlib import Path
import json
from prettytable import PrettyTable
import datetime
import humanize



def github_token():
    netrc_info = netrc()
    token = netrc_info.authenticators("api.github.com")[0]
    if not token:
        print("No GitHub token found in .netrc file.")
        sys.exit(1)
    return token


def analyze(owner, repo_name, branch, workflow_name=None):
    """
    Find the most recent job that passed for a given branch.
    If workflow_name is provided, filter by that specific workflow.
    """
    g = github.Github(github_token())
    repo = g.get_repo(f"{owner}/{repo_name}")
    # TODO: look at all workflows and determine the one that is failing
    # workflows = repo.get_workflows()
    # for workflow in workflows:
    #    print(f"Workflow: {workflow.name}, id: {workflow.id}")
    # workflow_name = "E2E (NVIDIA L40S x4)"
    # Seems like a bug here, get_workflow errors with 404 errors on this workflow_name.
    # Maybe the spaces in the name throws it off?
    workflow_id = 124236519
    workflow = repo.get_workflow(workflow_id)

    # TODO: only fetch one run (the latest).
    success_runs = workflow.get_runs(
        branch=branch, status="success", exclude_pull_requests=True
    )
    success_run = success_runs[0]
    # Fetch the failed run that failed immediately after the last successful one:
    fail_runs = workflow.get_runs(
        branch=branch, status="failure", exclude_pull_requests=True, created=">=" + success_run.created_at.isoformat()
    )
    *_, fail_run = fail_runs
    # Alternatively, use the *latest* failure:
    # fail_run = fail_runs[0]

    fail_job = find_job(fail_run, conclusion="failure")
    # fail_job.name is like "e2e-large-test"
    success_job = find_job(success_run, name=fail_job.name)

    success_log = save_job_log(success_job)
    fail_log = save_job_log(fail_job)
    success_packages = find_installed_packages(success_log)
    fail_packages = find_installed_packages(fail_log)
    save_packages(success_packages, success_job)
    save_packages(fail_packages, fail_job)
    compare_packages(success_packages, fail_packages)


def compare_packages(success_packages: dict, fail_packages: dict):
    """
    Compare the installed packages between the success and failure runs.
    """
    table = PrettyTable()
    table.field_names = ["Package", "Success Version", "Fail Version"]
    for package, version in success_packages.items():
        if package in fail_packages:
            if version != fail_packages[package]:
                table.add_row([package, version, fail_packages[package]])
        else:
            table.add_row([package, version, "Not installed"])
    for package, version in fail_packages.items():
        if package not in success_packages:
            table.add_row([package, "Not installed", version])
    print(table.get_string(sortby="Package"))


def find_job(run: github.WorkflowRun.WorkflowRun, name=None, conclusion=None):
    """ Search this WorkflowRun for a job with the given name or conclusion.
    """
    if not name and not conclusion:
        raise ValueError("Provide either name or conclusion.")
    for job in run.jobs():
        if name and job.name == name:
            return job
        if conclusion and job.conclusion == conclusion:
            return job
    raise ValueError("Job not found in WorkflowRun.")


def save_job_log(job: github.WorkflowJob.WorkflowJob):
    now = datetime.datetime.now(datetime.UTC)
    human_readable_time = humanize.naturaltime(now - job.created_at)
    print(f"{job.name} job ({job.conclusion} {human_readable_time} ago): {job.html_url}")
    logs_url = job.logs_url()
    # TODO: use temp files here instead of writing to cwd
    logfile = Path(f"job-{job.id}-{job.conclusion}.txt")
    if logfile.exists():
        return logfile
    print(f"Downloading logs to {logfile}...")
    with requests.get(logs_url, stream=True) as response:
        response.raise_for_status()  # Raise an exception for HTTP errors
        with logfile.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    clean_log(logfile)
    return logfile


def clean_log(logfile: Path):
    # Remove the timestamp and space at the beginning of each line,
    # example: 2025-04-19T16:04:17.8416307Z
    cleaned_lines = []
    with logfile.open() as f:
        for line in f:
            cleaned_line = line.split(" ", 1)[-1] if " " in line else line
            cleaned_lines.append(cleaned_line)
    with logfile.open("w") as f:
        f.writelines(cleaned_lines)


def save_packages(packages, job: github.WorkflowJob.WorkflowJob):
    """
    Save the installed packages to a JSON file named after the job ID.
    """
    output_file = Path(f"packages-{job.id}-{job.conclusion}.json")
    print(f"Saving installed packages to {output_file}...")
    with output_file.open("w") as f:
        json.dump(packages, f, indent=4)


def find_installed_packages(logfile: Path):
    """
    Parse the logfile to find lines that start with "Successfully installed"
    and extract the package names and versions into a dictionary.
    """
    installed_packages = {}

    with logfile.open() as f:
        for line in f:
            if line.startswith("Successfully installed"):
                # Extract the package list from the line
                packages = line.split("Successfully installed", 1)[1].strip().split()
                for package in packages:
                    # Split package name and version
                    if "-" in package:
                        name, version = package.rsplit("-", 1)
                        installed_packages[name] = version
    if not installed_packages:
        raise ValueError(f"No installed packages found in {logfile}.")
    return installed_packages


def show_workflow_run_info(branch, run):
    print(f"  Workflow: {run.name}")
    print(f"  Run ID: {run.id}")
    print(f"  URL: {run.html_url}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="analyze the logs between a successful run and failed run."
    )
    parser.add_argument("owner", help="Owner of the repository")
    parser.add_argument("repo", help="Name of the repository")
    parser.add_argument("branch", help="Branch to check")
    parser.add_argument(
        "workflow_name", nargs="?", help="Name of the workflow to filter by"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    analyze(args.owner, args.repo, args.branch, args.workflow_name)
