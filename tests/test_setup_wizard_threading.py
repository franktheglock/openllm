"""
Test for setup wizard GUI threading fix.
Verifies that the generate_system_prompt method uses threading correctly.
"""
import ast
import unittest
from pathlib import Path


class TestSetupWizardThreading(unittest.TestCase):
    """Test suite for setup wizard GUI threading."""

    def setUp(self):
        """Load and parse the setup wizard GUI file."""
        wizard_file = Path(__file__).parent.parent / "src" / "setup_wizard_gui.py"
        with open(wizard_file, "r") as f:
            self.tree = ast.parse(f.read())

        # Find the SetupWizardGUI class
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == "SetupWizardGUI":
                self.wizard_class = node
                break
        else:
            self.fail("SetupWizardGUI class not found")

    def test_generate_system_prompt_exists(self):
        """Test that generate_system_prompt method exists."""
        methods = [
            n.name for n in self.wizard_class.body if isinstance(n, ast.FunctionDef)
        ]
        self.assertIn("generate_system_prompt", methods)

    def test_update_generated_prompt_exists(self):
        """Test that _update_generated_prompt helper method exists."""
        methods = [
            n.name for n in self.wizard_class.body if isinstance(n, ast.FunctionDef)
        ]
        self.assertIn("_update_generated_prompt", methods)

    def test_uses_threading(self):
        """Test that generate_system_prompt uses threading.Thread."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "generate_system_prompt"
            ):
                source = ast.unparse(method)
                self.assertIn(
                    "threading.Thread",
                    source,
                    "generate_system_prompt should use threading.Thread",
                )
                return
        self.fail("generate_system_prompt method not found")

    def test_uses_after_for_gui_updates(self):
        """Test that GUI updates are scheduled using self.after()."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "generate_system_prompt"
            ):
                source = ast.unparse(method)
                self.assertIn(
                    "self.after",
                    source,
                    "generate_system_prompt should use self.after for thread-safe GUI updates",
                )
                return
        self.fail("generate_system_prompt method not found")

    def test_uses_asyncio_run(self):
        """Test that async operations use asyncio.run in the background thread."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "generate_system_prompt"
            ):
                source = ast.unparse(method)
                self.assertIn(
                    "asyncio.run",
                    source,
                    "generate_system_prompt should use asyncio.run for async operations",
                )
                return
        self.fail("generate_system_prompt method not found")

    def test_daemon_thread(self):
        """Test that the thread is created as a daemon thread."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "generate_system_prompt"
            ):
                source = ast.unparse(method)
                self.assertIn(
                    "daemon=True",
                    source,
                    "Thread should be created with daemon=True",
                )
                return
        self.fail("generate_system_prompt method not found")

    def test_no_blocking_asyncio_code(self):
        """Test that the old blocking code patterns are removed."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "generate_system_prompt"
            ):
                source = ast.unparse(method)
                # The old code had ThreadPoolExecutor which was blocking
                self.assertNotIn(
                    "ThreadPoolExecutor",
                    source,
                    "Should not use ThreadPoolExecutor which can cause blocking",
                )
                # The old code had get_running_loop which was part of the problematic logic
                self.assertNotIn(
                    "get_running_loop",
                    source,
                    "Should not check for running loop (causes complexity)",
                )
                return
        self.fail("generate_system_prompt method not found")

    def test_update_method_updates_gui(self):
        """Test that _update_generated_prompt properly updates GUI elements."""
        for method in self.wizard_class.body:
            if (
                isinstance(method, ast.FunctionDef)
                and method.name == "_update_generated_prompt"
            ):
                source = ast.unparse(method)
                # Should update the text area
                self.assertIn("self.system_prompt_text", source)
                # Should update status label
                self.assertIn("self.prompt_status_label", source)
                # Should re-enable button
                self.assertIn("self.generate_prompt_btn", source)
                return
        self.fail("_update_generated_prompt method not found")


if __name__ == "__main__":
    unittest.main()
