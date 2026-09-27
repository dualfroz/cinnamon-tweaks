import contextlib
import io
import unittest

from tests import schemaCompiled, testSchemaId

import keybindings
from keybindings import Shortcut, matchConflicts, normalizeAccelerator, systemBindings


class NormalizeAcceleratorTest(unittest.TestCase):
    def testControlSpellingsAreEqual(self):
        expected = normalizeAccelerator("<Control>t")
        self.assertEqual(normalizeAccelerator("<Primary>t"), expected)
        self.assertEqual(normalizeAccelerator("<Ctrl>t"), expected)

    def testModifierOrderDoesNotMatter(self):
        self.assertEqual(normalizeAccelerator("<Super><Shift>t"), normalizeAccelerator("<Shift><Super>t"))
        self.assertEqual(normalizeAccelerator("<Primary><Alt>Delete"), normalizeAccelerator("<Alt><Control>Delete"))

    def testKeyNameCaseDoesNotMatter(self):
        self.assertEqual(normalizeAccelerator("<Super>T"), normalizeAccelerator("<Super>t"))

    def testDifferentCombinationsDiffer(self):
        self.assertNotEqual(normalizeAccelerator("<Super>t"), normalizeAccelerator("<Super><Shift>t"))
        self.assertNotEqual(normalizeAccelerator("<Alt>t"), normalizeAccelerator("<Alt>y"))

    def testEmptyOrModifierOnlyIsNone(self):
        self.assertIsNone(normalizeAccelerator(""))
        self.assertIsNone(normalizeAccelerator(None))
        self.assertIsNone(normalizeAccelerator("<Control>"))


class MatchConflictsTest(unittest.TestCase):
    def setUp(self):
        self.customShortcuts = [
            Shortcut("custom0", "Terminal", "gnome-terminal", "<Primary><Alt>t"),
            Shortcut("custom1", "Files", "nemo", "<Super>e"),
        ]

    def testCustomConflictWithDifferentSpelling(self):
        conflicts = matchConflicts("<Alt><Control>t", self.customShortcuts, [])
        self.assertEqual(conflicts, ["custom shortcut \"Terminal\""])

    def testEditedShortcutIsExcluded(self):
        conflicts = matchConflicts("<Control><Alt>t", self.customShortcuts, [], excludeCustomId="custom0")
        self.assertEqual(conflicts, [])

    def testSystemConflictListedOnce(self):
        systemShortcuts = [
            ("org.example.wm", "terminal", "<Primary><Alt>t"),
            ("org.example.wm", "terminal", "<Control><Alt>T"),
            ("org.example.wm", "close", "<Alt>F4"),
        ]
        conflicts = matchConflicts("<Control><Alt>t", [], systemShortcuts)
        self.assertEqual(conflicts, ["system shortcut \"terminal\" (org.example.wm)"])

    def testNoConflict(self):
        self.assertEqual(matchConflicts("<Super>z", self.customShortcuts, [("s", "k", "<Super>x")]), [])

    def testUnparseableBindingHasNoConflicts(self):
        self.assertEqual(matchConflicts("<Control>", self.customShortcuts, []), [])


@unittest.skipUnless(schemaCompiled, "glib-compile-schemas is not available")
class SystemBindingsTest(unittest.TestCase):
    def setUp(self):
        keybindings.missingSchemasReported.clear()

    def testReadsStringListKeysAndSkipsMissingSchema(self):
        warnings = io.StringIO()
        with contextlib.redirect_stderr(warnings):
            bindings = systemBindings([testSchemaId, "org.example.missing"])
        self.assertEqual(set(bindings), {
            (testSchemaId, "terminal", "<Primary><Alt>t"),
            (testSchemaId, "lock", "<Super>l"),
            (testSchemaId, "lock", "<Control><Alt>l"),
        })
        self.assertIn("org.example.missing", warnings.getvalue())

    def testMissingSchemaIsReportedOnce(self):
        warnings = io.StringIO()
        with contextlib.redirect_stderr(warnings):
            systemBindings(["org.example.missing"])
            systemBindings(["org.example.missing"])
        self.assertEqual(warnings.getvalue().count("org.example.missing"), 1)


if __name__ == "__main__":
    unittest.main()
