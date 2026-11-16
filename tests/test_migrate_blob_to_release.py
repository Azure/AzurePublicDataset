"""Exercise the migration workflow's Bash without network or release operations."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "migrate-blob-to-release.yml"
)

STUBS = r"""
export TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR"
: > calls.log

python3() {
  printf 'asset-check\n' >> calls.log
  [[ "$TEST_MODE" == "skip" ]]
}

gh() {
  if [[ "$1" != "release" || "$2" != "upload" ]]; then
    echo "Unexpected gh command: $*" >&2
    return 99
  fi
  printf 'upload\n' >> calls.log
  if [[ "$TEST_MODE" == "upload_fail" ]] ||
     [[ "$TEST_MODE" == "first_upload_fail" && "${4##*/}" == "first.csv" ]]; then
    return 1
  fi
}

curl() {
  printf 'curl\n' >> calls.log
  local output=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o)
        output="$2"
        shift 2
        ;;
      -w|--connect-timeout|--max-time|--retry|--retry-delay)
        shift 2
        ;;
      -fsSL|https://*)
        shift
        ;;
      *)
        echo "Unexpected curl argument: $1" >&2
        return 99
        ;;
    esac
  done
  if [[ -z "$output" ]]; then
    echo "Missing curl output path" >&2
    return 99
  fi
  local attempt
  attempt=$(grep -c '^curl$' calls.log)
  if [[ "$TEST_MODE" == "download_fail" ]] ||
     [[ "$TEST_MODE" == "download_once" && "$attempt" -eq 1 ]]; then
    echo "Simulated download error" >&2
    printf '503'
    return 22
  fi
  printf 'trace data\n' > "$output"
  printf '200'
}

sleep() {
  return 0
}

timeout() {
  shift
  "$@"
}
"""


class MigrationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bash = os.environ.get("BASH_PATH") or shutil.which("bash")
        if bash is None:
            raise RuntimeError("Bash is required; set BASH_PATH if it is not on PATH")
        cls.bash = bash
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["migrate"]["steps"]
        release = next(
            step for step in steps if step.get("name") == "Create or get release"
        )
        upload = next(step for step in steps if step.get("name") == "Upload assets")
        cls.release_condition = release.get("if")
        script = upload["run"]
        if not isinstance(script, str):
            raise TypeError("The upload step must contain an inline Bash script")
        cls.upload_script = script

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def run_upload(
        self,
        mode: str = "success",
        dry_run: bool = False,
        files: tuple[str, ...] = ("file.csv",),
    ) -> subprocess.CompletedProcess[str]:
        urls = [
            f"https://example.blob.core.windows.net/container/{name}" for name in files
        ]
        (self.root / "urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
        script = self.upload_script
        inputs = {
            "release_tag": "test-release",
            "dry_run": "true" if dry_run else "false",
            "url_file": "urls.txt",
        }
        for key, value in inputs.items():
            script = script.replace("${{ inputs." + key + " }}", value)
        self.assertNotIn("${{", script)
        return subprocess.run(
            [self.bash, "--noprofile", "--norc", "-e", "-c", STUBS + script],
            cwd=self.root,
            env={**os.environ, "TEST_MODE": mode},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )

    def calls(self) -> list[str]:
        return (self.root / "calls.log").read_text(encoding="utf-8").splitlines()

    def assert_no_temporary_uploads(self) -> None:
        self.assertEqual(list((self.root / "tmp").iterdir()), [])

    def test_dry_run_skips_release_creation(self) -> None:
        self.assertEqual(self.release_condition, "inputs.dry_run != 'true'")

    def test_dry_run_only_lists_assets(self) -> None:
        result = self.run_upload(dry_run=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[DRY RUN] Would upload: file.csv", result.stdout)
        self.assertEqual(self.calls(), [])
        self.assert_no_temporary_uploads()

    def test_successful_upload(self) -> None:
        result = self.run_upload()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls().count("curl"), 1)
        self.assertEqual(self.calls().count("upload"), 1)
        self.assertIn("Uploaded : 1", result.stdout)
        self.assertIn("Failed   : 0", result.stdout)
        self.assert_no_temporary_uploads()

    def test_existing_asset_is_skipped(self) -> None:
        result = self.run_upload(mode="skip")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls(), ["asset-check"])
        self.assertIn("Skipped  : 1", result.stdout)
        self.assert_no_temporary_uploads()

    def test_transient_download_error_is_retried(self) -> None:
        result = self.run_upload(mode="download_once")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls().count("curl"), 2)
        self.assertEqual(self.calls().count("upload"), 1)
        self.assertIn("Uploaded : 1", result.stdout)
        self.assert_no_temporary_uploads()

    def test_exhausted_downloads_fail(self) -> None:
        result = self.run_upload(mode="download_fail")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls().count("curl"), 3)
        self.assertNotIn("upload", self.calls())
        self.assertIn("Failed   : 1", result.stdout)
        self.assertIn("::error::", result.stdout)
        self.assert_no_temporary_uploads()

    def test_exhausted_uploads_fail(self) -> None:
        result = self.run_upload(mode="upload_fail")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls().count("curl"), 3)
        self.assertEqual(self.calls().count("upload"), 3)
        self.assertIn("Failed   : 1", result.stdout)
        self.assertIn("::error::", result.stdout)
        self.assert_no_temporary_uploads()

    def test_later_files_are_processed_after_failure(self) -> None:
        result = self.run_upload(
            mode="first_upload_fail", files=("first.csv", "second.csv")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls().count("upload"), 4)
        self.assertIn("PASS: second.csv", result.stdout)
        self.assertIn("Uploaded : 1", result.stdout)
        self.assertIn("Failed   : 1", result.stdout)
        self.assert_no_temporary_uploads()


if __name__ == "__main__":
    unittest.main()
