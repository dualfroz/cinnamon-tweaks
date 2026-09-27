import unittest

from panel_tweaks import _panelsEnabledIds, _readPanelIndexedValue, _writePanelIndexedValue


class FakeSettings:
    def __init__(self, values):
        self.values = {key: list(entries) for key, entries in values.items()}

    def get_strv(self, key):
        return list(self.values.get(key, []))

    def set_strv(self, key, entries):
        self.values[key] = list(entries)


class PanelsEnabledIdsTest(unittest.TestCase):
    def testIdsInOrderWithoutDuplicates(self):
        settings = FakeSettings({"panels-enabled": ["2:0:top", "1:0:bottom", "2:1:left"]})
        self.assertEqual(_panelsEnabledIds(settings), ["2", "1"])

    def testFallsBackToFirstPanel(self):
        self.assertEqual(_panelsEnabledIds(FakeSettings({})), ["1"])


class PanelIndexedValueTest(unittest.TestCase):
    def testReadsValueOfRequestedPanel(self):
        settings = FakeSettings({"panels-height": ["1:40", "2:28"]})
        self.assertEqual(_readPanelIndexedValue(settings, "panels-height", "2", "40"), "28")

    def testReadFallsBackWhenPanelMissing(self):
        settings = FakeSettings({"panels-height": ["1:40"]})
        self.assertEqual(_readPanelIndexedValue(settings, "panels-height", "3", "40"), "40")

    def testWriteReplacesOnlyRequestedPanel(self):
        settings = FakeSettings({"panels-autohide": ["1:false", "2:false"]})
        _writePanelIndexedValue(settings, "panels-autohide", "2", "true")
        self.assertEqual(settings.get_strv("panels-autohide"), ["1:false", "2:true"])

    def testWriteAppendsMissingPanel(self):
        settings = FakeSettings({"panels-height": ["1:40"]})
        _writePanelIndexedValue(settings, "panels-height", "2", "32")
        self.assertEqual(settings.get_strv("panels-height"), ["1:40", "2:32"])


if __name__ == "__main__":
    unittest.main()
