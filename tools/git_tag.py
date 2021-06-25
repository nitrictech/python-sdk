import re
from subprocess import Popen, PIPE


def get_current_version_tag():
    process = Popen(["git", "describe", "--tags", "--match", "v[0-9]*"], stdout=PIPE)
    (output, err) = process.communicate()
    process.wait()

    tags = str(output, "utf-8").strip().split("\n")

    version_tags = [tag for tag in tags if re.match(r"^v?(\d*\.){2}\d$", tag)]
    dev_tags = [tag for tag in tags if re.match(r"^v?(\d*\.){2}\d-\d*-[a-z\d]{8}$", tag)]

    if len(version_tags) == 1:
        return version_tags.pop()[1:]
    elif len(dev_tags) == 1:
        base_tag, num_commits = dev_tags.pop().split("-")[:2]
        return "{}.dev{}".format(base_tag, num_commits)[1:]
    else:
        raise Exception("Unable to determine or construct version from git tags.")
