import contextlib
import io
import unittest
from unittest.mock import patch

from stockstudy.windows import main


class WindowsLauncherTests(unittest.TestCase):
    def test_double_click_opens_menu_until_exit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("builtins.input", return_value="0"), patch("stockstudy.windows.cli_main") as run:
            self.assertEqual(main([]), 0)
        self.assertIn("股票日线筛选", output.getvalue())
        run.assert_not_called()

    def test_scan_and_failure_return_to_menu(self):
        for choice, strategy, status in (("1", "pattern", 0), ("2", "pattern-drop", 1)):
            with self.subTest(choice=choice):
                output = io.StringIO()
                with contextlib.redirect_stdout(output), patch("builtins.input", side_effect=[choice, "", "0"]), patch("stockstudy.windows.cli_main", return_value=status) as run:
                    self.assertEqual(main([]), 0)
                arguments = run.call_args.args[0]
                self.assertEqual(arguments[:3], ["scan", "--strategy", strategy])
                self.assertEqual(output.getvalue().count("股票日线筛选"), 2)

    def test_explicit_arguments_preserve_cli_behavior(self):
        with patch("stockstudy.windows.cli_main", return_value=2) as run:
            self.assertEqual(main(["scan", "--lookback", "10"]), 2)
        run.assert_called_once_with(["scan", "--lookback", "10"])

    def test_closed_input_does_not_raise(self):
        with contextlib.redirect_stdout(io.StringIO()), patch("builtins.input", side_effect=EOFError):
            self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
