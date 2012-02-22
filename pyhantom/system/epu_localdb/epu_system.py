import logging
from pyhantom.out_data_types import InstanceType, AWSListType
from pyhantom.system.local_db.system import SystemLocalDB
from pyhantom.phantom_exceptions import PhantomAWSException
from ceiclient.connection import DashiCeiConnection
from ceiclient.client import EPUMClient

g_add_template = {'general' :
                    {'engine_class': 'epu.decisionengine.impls.phantom.PhantomEngine'},
                  'health':
                    {'monitor_health': False},
                  'engine_conf':
                    {'preserve_n': None,
                     'epuworker_type': 'sleeper',
                     'epuworker_image_id': None,
                     'iaas_site': None,
                     'iaas_allocation': None,
                     'deployable_type': 'sleeper'}
                  }



def convert_epu_description_to_asg_out(desc, asg):
    inst_list = desc['instances']
    name = desc['name']
    config = desc['config']

    asg.DesiredCapacity = config['engine_conf']['preserve_n']
    asg.Instances = AWSListType('Instances')

    for inst in inst_list:
        out_t = InstanceType('Instance')

        out_t.AutoScalingGroupName = name
        out_t.InstanceId = inst['iaas_id']
        out_t.HealthStatus = inst['state']
        out_t.LifecycleState = inst['state']
        out_t.AvailabilityZone = inst['site']
        out_t.LaunchConfigurationName = asg.LaunchConfigurationName

        asg.Instances.type_list.append(out_t)
        
    return asg

class EPUSystemWithLocalDB(SystemLocalDB):

    def __init__(self, cfg, log=logging):
        SystemLocalDB.__init__(self, cfg, log)

        self._broker = cfg.phantom.system.broker
        self._rabbitpw = cfg.phantom.system.rabbit_pw
        self._rabbituser = cfg.phantom.system.rabbit_user
        self._rabbitexchange = cfg.phantom.system.rabbit_exchange
        self._dashi_conn = DashiCeiConnection(self._broker, self._rabbituser, self._rabbitpw, exchange=self._rabbitexchange)
        self._epum_client = EPUMClient(self._dashi_conn)


    def create_autoscale_group(self, user_obj, asg):
        # call the parent class
        (db_asg, db_lc) = self._create_autoscale_group(user_obj, asg)

        global g_add_template
        conf = g_add_template.copy()
        conf['engine_conf']['preserve_n'] = asg.DesiredCapacity
        conf['engine_conf']['epuworker_image_id'] = db_lc.ImageId
        conf['engine_conf']['iaas_site'] = 'ec2-east' # db_asg.AvailabilityZones
        conf['engine_conf']['iaas_allocation'] = db_lc.InstanceType

        try:
            self._epum_client.add_epu(asg.AutoScalingGroupName, conf)
        except Exception, ex:
            raise

        # add to the db if everything else works out
        self._db.db_obj_add(db_asg)
        self._db.db_commit()


    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (asg.AutoScalingGroupName))

        conf = {'engine_conf':
                    {'preserve_n': None},
                  }
        try:
            self._epum_client.reconfigure_epu(name, conf)
        except Exception, ex:
            raise

        asg.DesiredCapacity = desired_capacity
        self._db.db_commit()


    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        try:
            (asg_list_type, next_token) = SystemLocalDB.get_autoscale_groups(self, user_obj, names, max, startToken)
            epu_list = self._epum_client.list_epus()

            # verify that the names are in thelist
            my_list = []
            for grp in asg_list_type.type_list:
                if grp.AutoScalingGroupName not in epu_list:
                    # perhaps all we should do here is log the error and remove the item from the DB
                    # for now make it very obvious that this happened
                    raise PhantomAWSException('InternalFailure', "%s is in the DB but the epu does not know about it" % (grp.AutoScalingGroupName))

                epu_desc = self._epum_client.describe_epu(grp.AutoScalingGroupName)
                convert_epu_description_to_asg_out(epu_desc, grp)
        except Exception, ex:
            raise
        except:
            raise

        return (asg_list_type, next_token)


    def delete_autoscale_group(self, user_obj, name, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        try:
            self._epum_client.remove_epu(name)
        except Exception, ex:
            raise

        self._db.delete_asg(asg)
        self._db.db_commit()
