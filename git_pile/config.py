# SPDX-License-Identifier: LGPL-2.1+
"""
Module providing the ``Config`` class, which is responsible for handling
git-pile configuration.
"""

from .helpers import (
    error,
    git,
    git_can_fail,
    nul_f,
    run_wrapper,
    warn,
)


class Config:
    __attr_doc_dir = "(path): Directory with PILE_BRANCH checkout (path)"
    __attr_doc_linear_branch = (
        "(string): Name of the linear branch to be generated by genlinear-branch. See `genlinear-branch --branch`"
    )
    __attr_doc_result_branch = "(string): Name of the branch generated by genbranch. Also see `genbranch --branch`"
    __attr_doc_pile_branch = '(string): Local name of the PILE_BRANCH - usually "pile"'
    __attr_doc_format_add_header = "(string): Additional email header to be added on each patch. See `--add-header`"
    __attr_doc_format_output_directory = "(path): Default output directory. Also see `--output`"
    __attr_doc_format_compose = "(bool): Invoke a text editor. See `--compose`"
    __attr_doc_format_signoff = "(bool): Add Signed-off-by trailer. See `--signoff`"
    __attr_doc_genbranch_committer_date_is_author_date = "(bool): Set committer date as the author date for generated patches. See --committer-date-is-author-date in GIT-COMMIT(1)"
    __attr_doc_genbranch_user_name = "(string): Name to use as committer when generating the commits"
    __attr_doc_genbranch_user_email = "(string): E-mail to use as committer when generating the commits"
    __attr_doc_genbranch_use_cache = "(bool): Use cached information to avoid recreating commits"
    __attr_doc_genbranch_cache_path = "(path): Path (relative to the .git dir) to the cache file for genbranch"

    @classmethod
    def per_worktree(cls):
        return git_can_fail("config --get --bool extensions.worktreeConfig", stderr=nul_f).stdout.strip() == "true"

    def __init__(self):
        self.dir = ""
        self.linear_branch = ""
        self.result_branch = ""
        self.pile_branch = ""
        self.format_add_header = ""
        self.format_output_directory = ""
        self.format_compose = False
        self.format_signoff = False
        self.genbranch_committer_date_is_author_date = True
        self.genbranch_user_name = None
        self.genbranch_user_email = None
        self.genbranch_use_cache = True
        self.genbranch_cache_path = "pile-genbranch-cache.pickle"
        self.write = None

        if Config.per_worktree():
            self.write = run_wrapper(["git", "config", "--worktree"], capture=True)
        else:
            self.write = run_wrapper(["git", "config"], capture=True)

        s = git(["config", "--get-regexp", "^pile\\.*"], check=False, stderr=nul_f).stdout.strip()
        if not s:
            return

        for kv in s.split("\n"):
            try:
                key, value = kv.strip().split(maxsplit=1, sep=" ")
            except ValueError:
                key = kv
                value = None

            # pile.*
            key = key[5:].translate(str.maketrans("-.", "__"))
            try:
                if hasattr(self, key) and isinstance(getattr(self, key), bool):
                    value = self._value_to_bool(value)

                setattr(self, key, value)
            except:
                warn(f"could not set {key}={value} from git config")

    def _value_to_bool(self, value):
        return value is None or value.lower() in ["yes", "on", "true", "1"]

    def is_valid(self):
        return self.dir != "" and self.result_branch != "" and self.pile_branch != ""

    def check_is_valid(self):
        if not self.is_valid():
            error("git-pile configuration is not valid. Configure it first with 'git pile init' or 'git pile setup'")
            return False

        return True

    def revert(self, other):
        if not other.is_valid():
            self.destroy()

        self.dir = other.dir
        if self.dir:
            self.write("pile.dir %s" % self.dir)

        self.result_branch = other.result_branch
        if self.result_branch:
            self.write("pile.result-branch %s" % self.result_branch)

        self.pile_branch = other.pile_branch
        if self.pile_branch:
            self.write("pile.pile-branch %s" % self.pile_branch)

    def destroy(self):
        return self.write("--remove-section pile", check=False, stderr=nul_f, stdout=nul_f).returncode == 0

    @classmethod
    def help(cls, prefix=""):
        attr_prefix = "_Config__attr_doc_"
        attr_docs = [k for k in cls.__dict__.keys() if k.startswith(attr_prefix + prefix)]
        if not attr_docs:
            return ""

        ret = ["", "", "configuration:"]
        for attr_name in attr_docs:
            config_name = attr_name[len(attr_prefix) :].replace("_", "-")
            ret.append(f"  {config_name} {getattr(cls, attr_name)}")

        return "\n".join(ret)
