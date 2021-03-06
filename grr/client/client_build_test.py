#!/usr/bin/env python
"""Tests for grr.client.client_build."""

import multiprocessing
import os
import platform
import tempfile
import unittest

import mock

from grr.lib import builders
from grr.lib import flags
from grr.lib import test_lib


class ClientBuildTests(test_lib.GRRBaseTest):

  def setUp(self):
    super(ClientBuildTests, self).setUp()
    # Delay import until we can mock out the parser, otherwise the parser
    # declarations in client_build mess up our test argument parsing
    self.parser_patcher = mock.patch.object(flags, "PARSER")
    self.parser_patcher.start()
    # pylint: disable=g-import-not-at-top
    from grr.client import client_build
    # pylint: enable=g-import-not-at-top
    self.client_build = client_build

  def tearDown(self):
    super(ClientBuildTests, self).tearDown()
    self.parser_patcher.stop()


class ClientBuildTest(ClientBuildTests):

  @unittest.skipUnless(platform.system() == "Linux",
                       "Just test linux to avoid lots of patching")
  def testBuildingContext(self):
    with mock.patch.object(builders, "LinuxClientBuilder") as mock_builder:
      self.client_build.TemplateBuilder().BuildTemplate()
      self.assertEqual(mock_builder.call_count, 1)


class MultiRepackTest(ClientBuildTests):

  def setUp(self):
    super(MultiRepackTest, self).setUp()
    self.pool_obj = mock.MagicMock()
    self.pool_patcher = mock.patch.object(
        multiprocessing, "Pool", return_value=self.pool_obj)
    self.mock_pool = self.pool_patcher.start()

    config_dir = tempfile.mkdtemp()
    self.label1_config = os.path.join(config_dir, "label1.yaml")
    self.label2_config = os.path.join(config_dir, "label2.yaml")
    open(self.label1_config, mode="w").write("Client.labels: [label1]")
    open(self.label2_config, mode="w").write("Client.labels: [label2]")
    self.template_dir = tempfile.mkdtemp()
    self.deb_template = os.path.join(self.template_dir,
                                     "grr_3.1.0.2_amd64.deb.zip")
    self.exe_template = os.path.join(self.template_dir,
                                     "GRR_3.1.0.2_i386.exe.zip")
    self.xar_template = os.path.join(self.template_dir,
                                     "grr_3.1.0.2_amd64.xar.zip")
    open(self.deb_template, mode="w").write("linux")
    open(self.exe_template, mode="w").write("windows")
    open(self.xar_template, mode="w").write("darwin")

    self.output_dir = tempfile.mkdtemp()

  def tearDown(self):
    super(MultiRepackTest, self).tearDown()
    self.pool_patcher.stop()

  def testMultipleRepackingNoSigning(self):
    self.client_build.MultiTemplateRepacker().RepackTemplates(
        [self.label1_config, self.label2_config],
        [self.deb_template, self.exe_template, self.xar_template],
        self.output_dir)

    # 3 templates x 2 labels = 6 repacks
    self.assertEqual(self.pool_obj.apply_async.call_count, 6)


def main(argv):
  test_lib.main(argv)


if __name__ == "__main__":
  flags.StartMain(main)
