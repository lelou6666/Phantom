from pyhantom.phantom_exceptions import PhantomAWSException


class ObjectFromReqInput(object):

    def __init__(self):
        self.optional_param_list_keys = {}
        self.needed_param_list_keys = {}
        self.optional_param_keys = {}
        self.needed_param_keys = {}

    def _get_value(self, name, in_val, t):
        if t == str:
            val= in_val
        elif t == int:
            val = int(in_val)
        elif t == None:
            # means to skip it (not implemented yet)
            val = None
        else:
            o = t(name)
            val = o.set_from_dict(in_val)
        return val

    def __getattr__(self, item):
        if item in self.optional_param_keys.keys():
            return None
        elif item in self.optional_param_list_keys.keys():
            return None
        raise AttributeError()

    def _do_list_param(self, params, p, type_d):
        for pl in type_d.keys():
            ndx = p.find(pl)
            if ndx == 0:
                val = self._get_value(p, params[p], type_d[pl])
                if val:
                    if pl not in self.__dict__:
                        self.__dict__[pl] = []
                    self.__dict__[pl].append(val)

    def set_from_dict(self, params):

        for p in self.needed_param_keys.keys() + self.needed_param_list_keys.keys():
            if p not in params:
                raise PhantomAWSException('MissingParameter', details="paramter %s missing" % (p))

        for p in params:
            self._do_list_param(params, p, self.needed_param_list_keys)
            self._do_list_param(params, p, self.optional_param_list_keys)

        # setup the needed ones
        for p in self.needed_param_keys:
            if p in params:
                val = self._get_value(p, params[p], self.needed_param_keys[p])
                if val:
                    self.__dict__[p] = val
        # setup the optional ones
        for p in self.optional_param_keys:
            if p in params:
                val = self._get_value(p, params[p], self.optional_param_keys[p])
                if val:
                    self.__dict__[p] = val

class BlockDeviceMappingInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self, "BlockDeviceMapping")
        self.optional_param_keys = {"DeviceName": str,  "VirtualName": str}

class LaunchConfigurationInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.optional_param_list_keys = {"BlockDeviceMappings": BlockDeviceMappingInput, "SecurityGroups": str}
        self.optional_param_keys = {"InstanceMonitoring": None,  "KernelId": str, "KeyName": str, "RamdiskId": str,  "UserData": str}
        self.needed_param_keys = {"ImageId": str, "InstanceType": str, "LaunchConfigurationName": str,}

class AutoScalingGroupInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.needed_param_list_keys = {'AvailabilityZones': str}
        self.optional_param_list_keys = {"Tags": str, "LoadBalancerNames": str}
        self.optional_param_keys = {"DefaultCooldown": None,  "DesiredCapacity": int, "HealthCheckGracePeriod": None, "HealthCheckType": None,  "PlacementGroup": None, "VPCZoneIdentifier": None}
        self.needed_param_keys = {"AutoScalingGroupName": str, "LaunchConfigurationName": str, "MaxSize": int, "MinSize": int}

class DeleteLaunchConfigurationType(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.needed_param_keys = {"LaunchConfigurationName": str}

class DescribeLaunchConfigurationsType(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.optional_param_keys = {"MaxRecords": int, "NextToken": str}
        self.optional_param_list_keys = {"LaunchConfigurationNames": str}


