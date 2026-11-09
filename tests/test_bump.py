"""Real bare-Git advertisement races and branch-only CLI regressions."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

from helper_support import GitFixture, cwd, source
import bump


class BumpTests(GitFixture):
    def setUp(self):
        super().setUp()
        self.hook = self.local / ".github/hooks/pre-push"
        self.original_run = bump.run

    def call(self):
        with cwd(self.local), patch.dict(os.environ, self.env, clear=True), \
                patch.object(bump, "HOOK", self.hook):
            return bump.bump_branch(self.sha, self.ref, "patch")

    def assert_unchanged(self):
        self.assertEqual(self.remote(), self.sha)
        self.assertEqual(self.git("--git-dir=" + str(self.bare), "tag", "--list"), "")

    def test_real_detached_cli_without_identity_clean_direct_child_source_only_and_no_follow_tags(self):
        self.git("tag", "-a", "unrelated-annotated", "-m", "must not follow")
        self.git("checkout", "--quiet", "--detach", self.sha)
        self.git("config", "--unset-all", "user.name")
        self.git("config", "--unset-all", "user.email")
        result = self.cli(".github/scripts/bump.py", "patch", "--sha", self.sha, "--ref", self.ref)
        self.assertEqual(result.returncode, 0, result.stderr)
        new = self.git("rev-parse", "HEAD")
        self.assertNotEqual(new, self.sha)
        self.assertEqual(self.remote(), new)
        self.assertEqual(self.git("rev-list", "--parents", "-n", "1", new), f"{new} {self.sha}")
        changed = set(self.git("diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
        self.assertEqual(changed, {str(source.PROJECT), str(source.LOCALIZED)})
        self.assertEqual((self.local / source.PLIST).read_bytes(),
                         self.git("show", self.sha + ":" + str(source.PLIST)).encode() + b"\n")
        message = self.git("log", "-1", "--format=%B")
        self.assertTrue(message.endswith(
            "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
        ), message)
        self.assertEqual(self.git("status", "--porcelain"), "")
        identity = "github-actions[bot] <github-actions[bot]@users.noreply.github.com>"
        self.assertEqual(self.git("log", "-1", "--format=%an <%ae>%n%cn <%ce>"),
                         identity + "\n" + identity)
        self.assertEqual(self.git("config", "push.followTags"), "true")
        self.assertEqual(self.git("--git-dir=" + str(self.bare), "tag", "--list"), "")
        self.assertEqual(source.read(self.local), source.read().rsplit(".", 1)[0] + "." +
                         str(int(source.read().split(".")[-1]) + 1))

    def test_no_follow_tags_negative_control_really_follows_annotated_tag(self):
        self.git("tag", "-a", "negative-control", "-m", "local fixture only")
        self.git("push", "--quiet", "origin", f"HEAD:{self.ref}")
        self.assertEqual(self.git("--git-dir=" + str(self.bare), "tag", "--list"), "negative-control")

    def test_initial_sha_ref_dirty_hidden_flag_and_guard_errors_are_zero_write(self):
        before = {path: (self.local / path).read_bytes() for path in source.SOURCE_PATHS}
        for ref in ("selected", "refs/tags/v1.0.0", "refs/heads/a..b"):
            result = self.cli(".github/scripts/bump.py", "patch", "--sha", self.sha, "--ref", ref)
            self.assertNotEqual(result.returncode, 0)
        for sha in ("a" * 39, "A" * 40, self.ancestor):
            result = self.cli(".github/scripts/bump.py", "patch", "--sha", sha, "--ref", self.ref)
            self.assertNotEqual(result.returncode, 0)
        for flag in ("--assume-unchanged", "--skip-worktree"):
            path = str(source.PLIST)
            self.git("update-index", flag, "--", path)
            (self.local / path).write_bytes(before[source.PLIST] + b" ")
            result = self.cli(".github/scripts/bump.py", "patch", "--sha", self.sha, "--ref", self.ref)
            self.assertNotEqual(result.returncode, 0)
            (self.local / path).write_bytes(before[source.PLIST])
            self.git("update-index", "--no-" + flag[2:], "--", path)
        for missing in (False, True):
            data = self.hook.read_bytes()
            if missing:
                self.hook.unlink()
            else:
                self.hook.chmod(0o644)
            result = self.cli(".github/scripts/bump.py", "patch", "--sha", self.sha, "--ref", self.ref)
            self.assertNotEqual(result.returncode, 0)
            self.hook.write_bytes(data)
            self.hook.chmod(0o755)
        self.assertEqual(before, {path: (self.local / path).read_bytes() for path in before})
        self.assertEqual(self.git("rev-parse", "HEAD"), self.sha)
        self.assert_unchanged()

    def test_initial_advance_rewind_and_delete(self):
        self.git("commit", "--quiet", "--allow-empty", "-m", "concurrent advance")
        advance = self.git("rev-parse", "HEAD")
        self.git("--git-dir=" + str(self.bare), "fetch", "--quiet", "--no-tags",
                 str(self.local), advance)
        self.git("reset", "--hard", self.sha)
        for new in (advance, self.ancestor, "0" * 40):
            self.git("--git-dir=" + str(self.bare), "update-ref", self.ref, new)
            with self.assertRaises(ValueError):
                self.call()
            self.assertEqual(self.git("rev-parse", "HEAD"), self.sha)
            self.git("--git-dir=" + str(self.bare), "update-ref", self.ref, self.sha)
        self.assert_unchanged()

    def race(self, kind):
        self.git("tag", "-a", "race-annotated", "-m", "must not follow")
        self.git("commit", "--quiet", "--allow-empty", "-m", "peer advance")
        advance = self.git("rev-parse", "HEAD")
        self.git("--git-dir=" + str(self.bare), "fetch", "--quiet", "--no-tags",
                 str(self.local), advance)
        self.git("reset", "--hard", self.sha)
        self.git("checkout", "--quiet", "--detach", self.sha)
        expected, pushes = None, 0

        def intercept(*args, **kwargs):
            nonlocal expected, pushes
            if "push" in args:
                pushes += 1
                new = self.git("rev-parse", "HEAD")
                if kind == "same-result":
                    self.git("--git-dir=" + str(self.bare), "fetch", "--quiet", "--no-tags",
                             str(self.local), new)
                    expected = new
                else:
                    expected = {"advance": advance, "rewind": self.ancestor, "delete": "0" * 40}[kind]
                self.git("--git-dir=" + str(self.bare), "update-ref", self.ref, expected)
            return self.original_run(*args, **kwargs)

        with patch.object(bump, "run", side_effect=intercept):
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                self.call()
        self.assertEqual(pushes, 1)
        if kind == "delete":
            self.assertNotEqual(self.git("--git-dir=" + str(self.bare), "rev-parse",
                                         "--verify", self.ref, check=False).returncode, 0)
        else:
            self.assertEqual(self.remote(), expected)
        self.assertEqual(self.git("--git-dir=" + str(self.bare), "tag", "--list"), "")

    def test_advertised_advance_after_final_read(self):
        self.race("advance")

    def test_advertised_rewind_after_final_read(self):
        self.race("rewind")

    def test_advertised_delete_after_final_read(self):
        self.race("delete")

    def test_advertised_same_result_zero_updates_after_final_read(self):
        self.race("same-result")

    def test_late_missing_and_nonexecutable_guard(self):
        runtime = self.root / "runtime"
        shutil.copytree(self.local / ".github", runtime)
        hook = runtime / "hooks/pre-push"
        reads = 0
        real_remote = bump.remote_ref

        def lose(ref):
            nonlocal reads
            value = real_remote(ref)
            reads += 1
            if reads == 2:
                hook.chmod(0o644)
            return value

        with patch.object(bump, "remote_ref", side_effect=lose), \
                cwd(self.local), patch.dict(os.environ, self.env, clear=True), \
                patch.object(bump, "HOOK", hook):
            with self.assertRaisesRegex(ValueError, "executable"):
                bump.bump_branch(self.sha, self.ref, "patch")
        self.assertEqual(reads, 2)
        self.assert_unchanged()
        self.git("reset", "--hard", self.sha)
        hook.chmod(0o755)
        reads = 0

        def remove(ref):
            nonlocal reads
            value = real_remote(ref)
            reads += 1
            if reads == 2:
                hook.unlink()
            return value

        with patch.object(bump, "remote_ref", side_effect=remove), \
                cwd(self.local), patch.dict(os.environ, self.env, clear=True), \
                patch.object(bump, "HOOK", hook):
            with self.assertRaisesRegex(ValueError, "executable"):
                bump.bump_branch(self.sha, self.ref, "patch")
        self.assert_unchanged()

    def prepare_child(self):
        result = self.cli(".github/scripts/source_version.py", "--bump", "patch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("add", "--", *map(str, source.SOURCE_PATHS))
        self.git("commit", "--quiet", "-m", "source child", "-m", bump.TRAILER)
        return self.git("rev-parse", "HEAD")

    def invoke_guard(self, new, rows, env=None):
        values = {**self.env, "BUMP_EXPECTED_SHA": self.sha,
                  "BUMP_EXPECTED_REF": self.ref, "BUMP_NEW_SHA": new}
        return subprocess.run([str(self.hook)], cwd=self.local, input=rows,
                              env=values if env is None else env, text=True, capture_output=True)

    def test_guard_exact_one_update_literal_head_ref_oldsha_and_missing_environment(self):
        new = self.prepare_child()
        row = f"{new} {new} {self.ref} {self.sha}\n"
        self.assertEqual(self.invoke_guard(new, row).returncode, 0)
        self.assertEqual(self.invoke_guard(new, row.replace(new + " ", "HEAD ", 1)).returncode, 0)
        for invalid in ("", row * 2, "malformed\n", row.replace(self.sha, self.ancestor),
                        row.replace(self.ref, "refs/heads/other"),
                        row.replace(new + " ", "refs/heads/selected ", 1),
                        row.replace(new, self.sha, 1)):
            self.assertNotEqual(self.invoke_guard(new, invalid).returncode, 0)
        self.assertNotEqual(self.invoke_guard(new, row, self.env).returncode, 0)
        self.assert_unchanged()

    def test_guard_revalidates_source_only_nonempty_trailer_and_direct_parent(self):
        new = self.prepare_child()
        tree = self.git("rev-parse", "HEAD^{tree}")
        selected_tree = self.git("rev-parse", self.sha + "^{tree}")
        for parents, selected, message in (
            (["-p", self.sha, "-p", self.ancestor], tree, "merge\n\n" + bump.TRAILER),
            (["-p", self.sha], selected_tree, "empty\n\n" + bump.TRAILER),
            (["-p", new], tree, "grandchild\n\n" + bump.TRAILER),
        ):
            commit = self.git("commit-tree", selected, *parents, input=message)
            self.git("reset", "--hard", commit)
            result = self.invoke_guard(commit, f"{commit} {commit} {self.ref} {self.sha}\n")
            self.assertNotEqual(result.returncode, 0, result.stderr)
        self.git("reset", "--hard", new)
        real_run = bump.run

        def missing_trailer(*args, **kwargs):
            if args[:4] == ("git", "log", "-1", "--format=%B"):
                return "simulated missing trailer"
            return real_run(*args, **kwargs)

        with cwd(self.local), patch.object(bump, "HOOK", self.hook), \
                patch.object(bump, "run", side_effect=missing_trailer):
            with self.assertRaisesRegex(ValueError, "trailer"):
                bump.commit_ready(self.sha, self.ref, new)
        (self.local / "unrelated.cpp").write_text("extra source")
        self.git("add", ".")
        tree = self.git("write-tree")
        commit = self.git("commit-tree", tree, "-p", self.sha,
                          input="extra\n\n" + bump.TRAILER + "\n")
        self.git("reset", "--hard", commit)
        self.assertNotEqual(self.invoke_guard(
            commit, f"{commit} {commit} {self.ref} {self.sha}\n").returncode, 0)
        self.assert_unchanged()

    def test_postpush_exact_remote_sha_is_verified(self):
        reads = 0
        real_remote = bump.remote_ref

        def response(ref):
            nonlocal reads
            reads += 1
            actual = real_remote(ref)
            return self.sha if reads == 3 else actual

        with patch.object(bump, "remote_ref", side_effect=response):
            with self.assertRaisesRegex(ValueError, "exact-SHA"):
                self.call()
        self.assertEqual(reads, 3)
        self.assertEqual(self.remote(), self.git("rev-parse", "HEAD"))
