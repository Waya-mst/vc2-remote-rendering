import subprocess

remote_show = subprocess.run(
    "git remote show origin", shell=True, capture_output=True, text=True
).stdout.strip("/n")
head_branch_line = next(
    line for line in remote_show.split("\n") if "HEAD branch" in line
)
head_branch = head_branch_line.split()[-1]

current_branch = subprocess.run(
    "git rev-parse --abbrev-ref HEAD", shell=True, capture_output=True, text=True
).stdout.strip("\n")

rev_list = subprocess.run(
    f"git rev-list --reverse origin/{head_branch}..HEAD".format(
        head_branch=head_branch
    ),
    shell=True,
    capture_output=True,
    text=True,
).stdout.strip("\n")

for rev in rev_list.split("\n"):
    print(
        f"git push origin {rev}:{current_branch} --force-with-lease".format(
            rev=rev, current_branch=current_branch
        )
    )
    subprocess.run(
        f"git push origin {rev}:{current_branch} --force-with-lease".format(
            rev=rev, current_branch=current_branch
        ),
        shell=True,
    )
