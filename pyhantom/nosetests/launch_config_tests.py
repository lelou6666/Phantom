import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import logging
import boto.ec2.autoscale
import unittest
import time
import uuid
import pyhantom
from pyhantom.main_router import MainRouter

# this test has a new server ever time to make sure there is a fresh env
from pyhantom.nosetests.server import RunPwFileServer
from pyhantom.system.tester import _TESTONLY_clear_registry

class BasicLaunchConfigTests(unittest.TestCase):

    def _get_good_con(self):
        region = RegionInfo(endpoint=self.hostname)
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=self.username, aws_secret_access_key=self.password, is_secure=False, port=self.port, debug=3, region=region)
        return con

    def setUp(self):
        self.tst_server = RunPwFileServer()
        self.tst_server.start()
        time.sleep(2.0)
        (self.username, self.password, self.hostname, self.port) = self.tst_server.get_boto_values()
        self.con = self._get_good_con()

    def tearDown(self):
        _TESTONLY_clear_registry()
        try:
            self.tst_server.end()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)


    def tests_list_empty_groups(self):
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x), "Should have gotten no rows back %s | %s" % (len(x), str(x)))

    def test_create_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = self.con.create_launch_configuration(lc)
        self.assertTrue(x.request_id)

    def test_create_delete_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.delete_launch_configuration(name)
        self.assertTrue(x.request_id)

    def test_create_delete_list_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))

    def test_create_delete_list_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].name, name)
        self.con.delete_launch_configuration(name)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x))

    def test_delete_failure(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.delete_launch_configuration(name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_same_twice_error(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = self.con.create_launch_configuration(lc)
        try:
            x = self.con.create_launch_configuration(lc)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_delete_not_there(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.delete_launch_configuration(name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_list_not_there(self):
        name = str(uuid.uuid4()).split('-')[0]
        x = self.con.get_all_launch_configurations(names=[name])
        self.assertEqual(len(x), 0)

    def test_create_list_multiple(self):
        name1 = str(uuid.uuid4()).split('-')[0]
        name2 = str(uuid.uuid4()).split('-')[0]
        lc1 = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name1, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        lc2 = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name2, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc1)
        self.con.create_launch_configuration(lc2)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(2, len(x))
        for rc in x:
            self.assertTrue(rc.name in [name1, name2])

        self.con.delete_launch_configuration(name1)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].name, name2)
        
    def test_list_no_contig(self):
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
            self.con.create_launch_configuration(lc)

        nl = [names[1], names[4]]
        x = self.con.get_all_launch_configurations(names=nl)
        for rc in x:
            self.assertTrue(rc.name in nl)

        for n in names:
            self.con.delete_launch_configuration(n)

    def test_create_list_more_params(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default', 'more'], user_data="XXXUSERDATAYYY", instance_type='m1.small', kernel_id='XEN', ramdisk_id='RAMXXX')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))

    def test_set_security_groups(self):
        sec_groups = ['default', 'more']
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=sec_groups, user_data="XXXUSERDATAYYY", instance_type='m1.small', kernel_id='XEN', ramdisk_id='RAMXXX')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations(names=[name,])
        self.assertEqual(1, len(x))
        for s in sec_groups:
            self.assertTrue(s in x[0].security_groups)
        self.assertEqual(len(sec_groups), len(x[0].security_groups))

    def test_bad_login(self):
        region = RegionInfo(endpoint=self.hostname)
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id="XXX", aws_secret_access_key=self.password, is_secure=False, port=self.port, debug=3, region=region)
        try:
            x = con.get_all_launch_configurations()
            self.assertTrue(False, "login should have failed")
        except BotoServerError, ex:
            pass


    def test_bad_pw(self):
        region = RegionInfo(endpoint=self.hostname)
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=self.username, aws_secret_access_key="XXX", is_secure=False, port=self.port, debug=3, region=region)
        try:
            x = con.get_all_launch_configurations()
            self.assertTrue(False, "login should have failed")
        except BotoServerError, ex:
            pass

    def test_set_userdata(self):
        userdata = "XXXUSERDATAYYY"
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data=userdata, instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].user_data, userdata)
