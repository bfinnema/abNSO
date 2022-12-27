# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        vars = ncs.template.Variables()
        template = ncs.template.Template(service)

        # ISIS PART
        def isis_device(device, isis_instance):
            vars.add('name', isis_instance+"-"+device)
            mgmt_ipv4_address = root.mb.mb_inventory.metroDevices.metroDevice[device].ipv4_mgmt_addr
            # self.log.info('mgmt_ipv4_address: ', mgmt_ipv4_address)
            vars.add('mgmt_ipv4_address', root.mb.mb_inventory.metroDevices.metroDevice[device].ipv4_mgmt_addr)
            vars.add('isis_interface_name', root.mb.mb_inventory.metroDevices.metroDevice[device].isis_interface_name)
            vars.add('isis_interface_number', root.mb.mb_inventory.metroDevices.metroDevice[device].isis_interface_number)
            # self.log.info('YYYEEEEHAAA ', device)
            device_type = root.mb.mb_inventory.metroDevices.metroDevice[device].device_type
            if device_type == "ER":
                template.apply('infra_isiscfs_er-template', vars)  #THIS TEMPLATE IS USED IN CASE OF INDIRECT DEPLOYMENT TO DEVICE, IE CFS - RFS CONCEPT IS APPLIED 
                # template.apply('mb_isis_er-template', vars)      #THIS TEMPLATE IS USED IN CASE OF DIRECT DEPLOYMENT TO DEVICE, IE NO CFS - RFS CONCEPT 
            else:
                template.apply('infra_isiscfs-template', vars)     #THIS TEMPLATE IS USED IN CASE OF INDIRECT DEPLOYMENT TO DEVICE, IE CFS - RFS CONCEPT IS APPLIED
                # template.apply('mb_isis-template', vars)         #THIS TEMPLATE IS USED IN CASE OF DIRECT DEPLOYMENT TO DEVICE, IE NO CFS - RFS CONCEPT 

        if service.isis_config.do_isis_config:
            isis_instance = service.isis_config.isis_instance
            vars.add('isis_instance', isis_instance)
            maxwait = root.mb.mb_inventory.ISISinstances.ISISinstance[isis_instance].maxwait
            self.log.info('maxwait: ', maxwait)
            vars.add('maxwait', root.mb.mb_inventory.ISISinstances.ISISinstance[isis_instance].maxwait)
            vars.add('max_lsp_lifetime', root.mb.mb_inventory.ISISinstances.ISISinstance[isis_instance].max_lsp_lifetime)

            if service.group == "Group":
                device_group = service.device_group_id
                devgroups = root.devices.device_group
                for device in devgroups[device_group].device_name:
                    vars.add('device', device)
                    isis_device(device, isis_instance)
            else:
                for device in service.device:
                    vars.add('device', device)
                    isis_device(device, isis_instance)

        # MPLS PART
        if service.ldp_config.do_ldp_config:
            vars.add('address_family', service.ldp_config.address_family)
            vars.add('acl_name', service.ldp_config.acl_name)
            for seq in root.mb.mb_inventory.access_lists.access_list[service.ldp_config.acl_name].sequence:
                vars.add('sequence_number', seq.sequence_number)
                vars.add('protocol', seq.protocol)
                vars.add('ipv4_addr', seq.ipv4_addr)
                vars.add('prefix_length', seq.prefix_length)
                if service.group == "Group":
                    device_group = service.device_group_id
                    devgroups = root.devices.device_group
                    for device in devgroups[device_group].device_name:
                        vars.add('device', device)
                        template.apply('infra_acl-template', vars)
                else:
                    for device in service.device:
                        vars.add('device', device)
                        template.apply('infra_acl-template', vars)
                
            for mpls_interface in service.ldp_config.mpls_interfaces.mpls_interface:
                vars.add('mpls_interface_name', mpls_interface.mpls_interface_name)
                vars.add('mpls_interface_number', mpls_interface.mpls_interface_number)
                if service.group == "Group":
                    device_group = service.device_group_id
                    devgroups = root.devices.device_group
                    for device in devgroups[device_group].device_name:
                        vars.add('device', device)
                        vars.add('router_id', root.mb.mb_inventory.metroDevices.metroDevice[device].ipv4_mgmt_addr)
                        template.apply('infra_mpls-ldp-template', vars)
                else:
                    for device in service.device:
                        vars.add('device', device)
                        vars.add('router_id', root.mb.mb_inventory.metroDevices.metroDevice[device].ipv4_mgmt_addr)
                        template.apply('infra_mpls-ldp-template', vars)

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service postmod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('mb_infra_cfs-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
