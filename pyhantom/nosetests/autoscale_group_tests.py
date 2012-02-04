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
from pyhantom.nosetests import RunTestPwFileServer

# this test has a new server ever time to make sure there is a fresh env
from pyhantom.system.tester import _TESTONLY_clear_registry

class BasicAutoScaleGroupTests(unittest.TestCase):

    tst_server = RunTestPwFileServer(MainRouter())

    @classmethod
    def setupClass(cls):
        print "setUpModule"
        try:
            cls.tst_server.start()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)
        time.sleep(0.5)

    @classmethod
    def teardownClass(cls):
        try:
            cls.tst_server.end()
            cls.tst_server.join()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)

    def _get_good_con(self):
        region = RegionInfo('localhost')
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=self.username, aws_secret_access_key=self.password, is_secure=False, port=self.port, debug=3, region=region)
        con.host = 'localhost'
        return con

    def setUp(self):
        (self.username, self.password, self.port) = BasicAutoScaleGroupTests.tst_server.get_boto_values()
        self.con = self._get_good_con()

    def tearDown(self):
        _TESTONLY_clear_registry()

    def test_create_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)

    def test_create_delete_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        self.con.delete_auto_scaling_group(group_name)

    def test_delete_nonexistant_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        try:
            self.con.delete_auto_scaling_group(group_name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_group_twice(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        try:
            self.con.create_auto_scaling_group(asg)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_delete_group_twice(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        self.con.delete_auto_scaling_group(group_name)
        try:
            self.con.delete_auto_scaling_group(group_name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_list_delete_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        l = self.con.get_all_groups()
        self.assertEqual(l[0].name, group_name)
        self.con.delete_auto_scaling_group(group_name)

    def test_list_empty(self):
        l = self.con.get_all_groups()
        self.assertEqual(len(l), 0)

    def test_list_not_there(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.get_all_groups(names=[name])
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_list_no_contig(self):
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        nl = [names[1], names[4]]
        x = self.con.get_all_groups(names=nl)
        for rc in x:
            self.assertTrue(rc.name in nl)

        for n in names:
            self.con.delete_auto_scaling_group(n)


    def test_list_many_asgs(self):
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        x = self.con.get_all_groups()
        self.assertEqual(len(x), len(names))
        for rc in x:
            self.assertTrue(rc.name in names)

        for n in names:
            self.con.delete_auto_scaling_group(n)

    def test_list_many_asgs_many_times(self):
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        for i in range(0, 8):
            x = self.con.get_all_groups()
            self.assertEqual(len(x), len(names))
        for rc in x:
            self.assertTrue(rc.name in names)

        for n in names:
            self.con.delete_auto_scaling_group(n)


    def test_set_desired_capacity(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        l = self.con.get_all_groups(names=[group_name])

        c = 10
        asg.set_capacity(c)

        l = self.con.get_all_groups(names=[group_name])
        self.assertEqual(c, l[0].desired_capacity)

        self.assertEqual(l[0].name, group_name)
        self.con.delete_auto_scaling_group(group_name)