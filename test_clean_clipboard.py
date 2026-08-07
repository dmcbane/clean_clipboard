"""Tests for clean_clipboard: text cleaning and platform clipboard dispatch."""

import unittest
from unittest import mock

import clean_clipboard as cc


class CleanNewlineTests(unittest.TestCase):
    def test_newline_is_preserved(self):
        self.assertEqual(cc.clean("line one\nline two"), "line one\nline two")

    def test_crlf_is_normalized_to_lf(self):
        self.assertEqual(cc.clean("line one\r\nline two"), "line one\nline two")

    def test_lone_cr_is_normalized_to_lf(self):
        self.assertEqual(cc.clean("line one\rline two"), "line one\nline two")

    def test_crlf_does_not_double_line_breaks(self):
        self.assertEqual(cc.clean("a\r\n\r\nb"), "a\n\nb")


class CleanExistingBehaviorTests(unittest.TestCase):
    def test_tab_becomes_two_spaces(self):
        self.assertEqual(cc.clean("a\tb"), "a  b")

    def test_smart_double_quotes(self):
        self.assertEqual(cc.clean("“hi”"), '"hi"')

    def test_smart_single_quotes(self):
        self.assertEqual(cc.clean("it’s"), "it's")

    def test_em_dash(self):
        self.assertEqual(cc.clean("a—b"), "a-b")

    def test_ellipsis(self):
        self.assertEqual(cc.clean("wait…"), "wait...")

    def test_nbsp_becomes_space(self):
        self.assertEqual(cc.clean("a\u00a0b"), "a b")

    def test_zero_width_dropped(self):
        self.assertEqual(cc.clean("a\u200bb"), "ab")

    def test_disallowed_chars_stripped(self):
        self.assertEqual(cc.clean("a☺b€c"), "abc")


class ClipboardBackendTests(unittest.TestCase):
    """Platform dispatch is pure (platform + env in, commands out), so it is
    testable without touching a real clipboard."""

    def _backend(self, platform_name, release="6.8.0-generic", env=None):
        with mock.patch.object(cc.sys, "platform", platform_name), \
             mock.patch.object(cc.platform, "uname") as uname, \
             mock.patch.dict(cc.os.environ, env or {}, clear=True):
            uname.return_value = mock.Mock(release=release)
            return cc._clipboard_backend()

    def test_windows_uses_powershell(self):
        b = self._backend("win32")
        self.assertEqual(b.read_cmd[0], "powershell")
        self.assertEqual(b.write_cmd[0], "powershell")
        self.assertTrue(b.strips_trailing_crlf)

    def test_macos_uses_pbpaste_pbcopy(self):
        b = self._backend("darwin")
        self.assertEqual(b.read_cmd, ["pbpaste"])
        self.assertEqual(b.write_cmd, ["pbcopy"])
        self.assertFalse(b.strips_trailing_crlf)

    def test_wsl_uses_windows_powershell(self):
        b = self._backend(
            "linux", release="6.18.33.2-microsoft-standard-WSL2"
        )
        self.assertEqual(b.read_cmd[0], "powershell.exe")
        self.assertEqual(b.write_cmd[0], "powershell.exe")
        self.assertTrue(b.strips_trailing_crlf)

    def test_wayland_uses_wl_clipboard(self):
        b = self._backend("linux", env={"WAYLAND_DISPLAY": "wayland-0"})
        self.assertEqual(b.read_cmd, ["wl-paste", "-n"])
        self.assertEqual(b.write_cmd, ["wl-copy"])
        self.assertFalse(b.strips_trailing_crlf)

    def test_x11_falls_back_to_xclip(self):
        b = self._backend("linux", env={"DISPLAY": ":0"})
        self.assertEqual(b.read_cmd, ["xclip", "-selection", "clipboard", "-o"])
        self.assertEqual(b.write_cmd, ["xclip", "-selection", "clipboard"])
        self.assertFalse(b.strips_trailing_crlf)

    def test_wayland_checked_before_x11(self):
        # Wayland sessions also set DISPLAY (XWayland); wl-clipboard must win.
        b = self._backend(
            "linux", env={"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}
        )
        self.assertEqual(b.write_cmd, ["wl-copy"])


class GetClipboardTests(unittest.TestCase):
    def _run_with_stdout(self, stdout, strips):
        backend = cc.ClipboardBackend(["fake"], ["fake"], strips)
        with mock.patch.object(cc, "_clipboard_backend", return_value=backend), \
             mock.patch.object(cc.subprocess, "run") as run:
            run.return_value = mock.Mock(stdout=stdout)
            return cc.get_clipboard()

    def test_powershell_trailing_crlf_removed(self):
        self.assertEqual(self._run_with_stdout("text\r\n", strips=True), "text")

    def test_only_one_trailing_crlf_removed(self):
        # A real newline at the end of the clipboard text must survive.
        self.assertEqual(
            self._run_with_stdout("text\n\r\n", strips=True), "text\n"
        )

    def test_non_powershell_output_untouched(self):
        self.assertEqual(
            self._run_with_stdout("text\n", strips=False), "text\n"
        )


class MainErrorHandlingTests(unittest.TestCase):
    def test_missing_clipboard_tool_exits_nonzero_with_hint(self):
        err = FileNotFoundError(2, "No such file or directory", "xclip")
        with mock.patch.object(cc, "get_clipboard", side_effect=err), \
             mock.patch.object(cc.sys, "stderr") as stderr:
            self.assertEqual(cc.main(), 1)
        written = "".join(
            c.args[0] for c in stderr.write.call_args_list if c.args
        )
        self.assertIn("xclip", written)

    def test_empty_clipboard_exits_nonzero(self):
        with mock.patch.object(cc, "get_clipboard", return_value=""), \
             mock.patch.object(cc.sys, "stderr"):
            self.assertEqual(cc.main(), 1)


if __name__ == "__main__":
    unittest.main()
