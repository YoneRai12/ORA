import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the module under test
# We need to add the project root to sys.path or import by path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from phoenix_cli_manager import Config, PatchApplier, Logger, Redactor, acquire_lock, StateStore

class TestPhoenixSafety(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.cfg = Config(project_root=self.root)
        self.cfg.dry_run = False # Force false for tests
        # Reset defaults for tests
        self.cfg.allow_modify_globs = ("*.py",) 
        self.cfg.deny_dirs = (".git", "tests", "secrets")
        self.cfg.backups_dir = self.root / ".phoenix_cli/backups"
        self.cfg.backups_dir.mkdir(parents=True)
        self.cfg.lock_path = self.root / ".phoenix_cli/lock"
        self.redactor = Redactor(self.cfg)
        self.logger = Logger(self.cfg, self.redactor)
        self.applier = PatchApplier(self.cfg, self.logger)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_strict_allowlist_default(self):
        # Test that empty allowlist denies everything
        self.cfg.allow_modify_globs = ()
        target = self.root / "train.py"
        target.touch()
        self.assertFalse(self.applier.is_safe_target(target))

    def test_deny_tests_dir(self):
        # Test that tests dir is denied
        tests_dir = self.root / "tests"
        tests_dir.mkdir()
        target = tests_dir / "test_foo.py"
        target.touch()
        self.assertFalse(self.applier.is_safe_target(target))

    def test_deny_sensitive_dir(self):
        secrets_dir = self.root / "secrets"
        secrets_dir.mkdir()
        target = secrets_dir / "key.py"
        target.touch()
        self.assertFalse(self.applier.is_safe_target(target))

    def test_allow_normal_file(self):
        target = self.root / "train.py"
        target.touch()
        self.assertTrue(self.applier.is_safe_target(target))

    def test_redaction(self):
        text = "My API key is api_key='12345678abcdef'"
        redacted = self.redactor.redact(text)
        self.assertIn("<REDACTED>", redacted)
        self.assertNotIn("12345678abcdef", redacted)

    def test_patch_limit_files(self):
        patches = [{"file_path": f"f{i}.py", "mode": "replace_range"} for i in range(5)]
        self.cfg.max_patch_files = 3
        ok, msg = self.applier.apply_patch_set(patches)
        self.assertFalse(ok)
        self.assertIn("Too many files", msg)

    def test_lock_file_acquisition(self):
        # First acquire should succeed
        self.assertTrue(acquire_lock(self.cfg, self.logger))
        self.assertTrue(self.cfg.lock_path.exists())
        
        # Second acquire should fail (same PID, but logic checks existence)
        # Actually, if same PID, it overwrites in our simple logic? 
        # No, acquire_lock reads the file. If PID matches current PID, it might think it's held?
        # Our implementation: if lock exists, check PID. If PID alive, return False.
        # Since we are the PID, it is alive. So it should return False.
        self.assertFalse(acquire_lock(self.cfg, self.logger))

    def test_atomic_shadow_patching_success(self):
        target = self.root / "train.py"
        target.write_text("print('hello')\n", encoding="utf-8")
        
        patch = {
            "file_path": str(target),
            "mode": "replace_range",
            "start_line": 1,
            "end_line": 1,
            "code": "print('fixed')\n"
        }
        
        # Mock run_test_cmd to pass
        self.applier.run_test_cmd = MagicMock(return_value=(True, "OK"))
        
        ok, msg = self.applier.apply_patch_set([patch])
        self.assertTrue(ok, msg)
        self.assertEqual(target.read_text(encoding="utf-8"), "print('fixed')\n")
        # Check backup created
        self.assertTrue(list(self.cfg.backups_dir.glob("train.py.*.bak")))

    def test_atomic_shadow_patching_fail_test(self):
        target = self.root / "train.py"
        original_content = "print('hello')\n"
        target.write_text(original_content, encoding="utf-8")
        
        patch = {
            "file_path": str(target),
            "mode": "replace_range",
            "start_line": 1,
            "end_line": 1,
            "code": "print('broken')\n"
        }
        
        # Mock run_test_cmd to FAIL
        self.applier.run_test_cmd = MagicMock(return_value=(False, "FAIL"))
        self.cfg.require_test_pass = True
        
        ok, msg = self.applier.apply_patch_set([patch])
        self.assertFalse(ok)
        self.assertIn("Tests failed", msg)
        
        # Verify original file is RESTORED (or never changed if we did it right)
        # Our implementation applies to temp, then moves to real, then tests.
        # If test fails, it rolls back.
        self.assertEqual(target.read_text(encoding="utf-8"), original_content)

    def test_fallback_llm(self):
        # Configure fallback
        cmd = [sys.executable, str(self.root / "tests/dummy_fallback_llm.py")]
        self.cfg.fallback_llm_cmds = [cmd]
        self.cfg.fallback_llm_cmd = cmd
        
        # Create dummy fallback script
        dummy_script = self.root / "tests/dummy_fallback_llm.py"
        dummy_script.parent.mkdir(exist_ok=True)
        dummy_script.write_text("""
import sys
import json
def main():
    patch = {
        "patches": [
            {
                "file_path": "train.py",
                "mode": "replace_range",
                "start_line": 1,
                "end_line": 1,
                "code": "print('Fixed by Fallback')\\n"
            }
        ]
    }
    print(json.dumps(patch))
if __name__ == "__main__":
    main()
""", encoding="utf-8")

        # Initialize ErrorHandler
        state = StateStore(self.cfg)
        from phoenix_cli_manager import ErrorHandler
        handler = ErrorHandler(self.cfg, self.logger, state)
        
        # Mock primary LLM to fail
        handler.gemini_cli.request_fix = MagicMock(side_effect=RuntimeError("Primary Failed"))
        
        # Call LLM
        target = self.root / "train.py"
        target.touch()
        resp = handler._call_llm("prompt", target)
        
        # Verify fallback was called and returned correct data
        self.assertIn("patches", resp)
        self.assertEqual(resp["patches"][0]["code"], "print('Fixed by Fallback')\n")

if __name__ == "__main__":
    unittest.main()
