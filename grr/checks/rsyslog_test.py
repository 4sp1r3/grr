#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for rsyslog state checks."""


from grr.lib import flags
from grr.lib import test_lib
from grr.lib.checks import checks_test_lib
from grr.parsers import config_file


class RsyslogCheckTests(checks_test_lib.HostCheckTest):
  """Test the rsyslog checks."""

  @classmethod
  def setUpClass(cls):
    cls.LoadCheck("rsyslog.yaml")
    cls.parser = config_file.RsyslogParser()

  def testLoggingAuthRemoteOK(self):
    chk_id = "CIS-LOGGING-AUTH-REMOTE"

    test_data = {
        "/etc/rsyslog.conf": "*.* @@tcp.example.com.:514;RSYSLOG_ForwardFormat"
    }
    host_data = self.GenFileData("LinuxRsyslogConfigs", test_data, self.parser)
    results = self.RunChecks(host_data)
    self.assertCheckUndetected(chk_id, results)

  def testLoggingAuthRemoteFail(self):
    chk_id = "CIS-LOGGING-AUTH-REMOTE"

    test_data = {"/etc/rsyslog.conf": "*.* /var/log/messages"}
    host_data = self.GenFileData("LinuxRsyslogConfigs", test_data, self.parser)
    sym = "Missing attribute: No remote destination for auth logs."
    found = ["Expected state was not found"]
    results = self.RunChecks(host_data)
    self.assertCheckDetectedAnom(chk_id, results, sym, found)

  def testLoggingFilePermissions(self):
    chk_id = "CIS-LOGGING-FILE-PERMISSIONS"

    ro = self.CreateStat("/test/ro", 0, 0, 0o0100640)
    rw = self.CreateStat("/test/rw", 0, 0, 0o0100666)

    sym = "Found: Log configurations can be modified by non-privileged users."
    found = ["/test/rw user: 0, group: 0, mode: -rw-rw-rw-"]
    results = self.GenResults(["LinuxRsyslogConfigs"], [[ro, rw]])
    self.assertCheckDetectedAnom(chk_id, results, sym, found)


def main(argv):
  test_lib.GrrTestProgram(argv=argv)


if __name__ == "__main__":
  flags.StartMain(main)
