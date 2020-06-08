# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
from ncs.dp import Action
import ncs.maapi as maapi
import ncs.maagic as maagic

# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class SampleServiceCallback(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        vars = ncs.template.Variables()
        
        template = ncs.template.Template(service)
        #Apply vnf-info template that creates the NFVO service along with device-templates applied.
        template.apply('vnf-info', vars)
        
        vnf_info = 'TheRouter'
        dep_name = 'branch-office'
        device = service.device
        
        self.log.info("Device {}".format(device))
        vars.add("SERVICE", service.name)
        vars.add("CUSTOM-DEP", dep_name)
        vars.add("VNF-INFO", 'TheRouter')
        #Apply kicker template to redeploy the sample service when the VNF is ready reached on the plan.
        template.apply('sample-service-kicker', vars)
        
        with maapi.single_read_trans("", "system", db=ncs.OPERATIONAL) as th:
            op_root = ncs.maagic.get_root(th)  
            vnf_info_plan = op_root.nfv__nfv.cisco_nfvo__vnf_info_plan
            if vnf_info in vnf_info_plan:
                vnf_component = vnf_info_plan[vnf_info].plan.component['cisco-nfvo-nano-services:deployment', dep_name]
                for state in vnf_component.state:
                    #Check if VNF is ready reached before applying day-n config.
                    if state.name == 'ncs:ready' and state.status == 'reached':
                        self.log.info("Applying device config.. ")
                        root.ncs__devices.device['volvo-branch-office-TheRouter-CSR-esc0-1'].config.ios__interface.Loopback.create(2)
                
# ------------------------
# MIGRATION ACTION
# ------------------------
class VnfInfoMigrationAction(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):
        with maapi.single_write_trans(uinfo.username,
                                      uinfo.context,
                                      db=ncs.OPERATIONAL) as th:
            root = ncs.maagic.get_root(th)

            deployments = root.nfvo_rel2__nfvo.vnf_info.esc.vnf_deployment_result
            self.log.info("There are {} existing deployments to migrate".format(len(deployments)))

            for dep in deployments:
               self._handle_dep_res(root, th)

            th.apply()

        output.result = "Migration Complete!"

    def _handle_dep_res(self, root, th):
        old_res_list = root.nfvo_rel2__nfvo.nfvo_rel2__vnf_info.nfvo_rel2_esc__esc. \
                    nfvo_rel2_esc__vnf_deployment_result
        self.log.info("Migrating deployment result. There are {} deployments to be migrated".format(len(old_res_list)))
    
        for old_deployment in old_res_list:
            tenant = old_deployment.tenant
            dep_name = old_deployment.deployment_name
            device_name = old_deployment.esc
            device = root.ncs__devices.device[device_name]
            
            self.log.info("Migrating vnf-deployment-result {} {} {}".format(tenant, dep_name, device_name))
            
            netconf_deployment_result = root.nfv__nfv.cisco_nfvo__internal. \
                       cisco_nfvo__netconf_deployment_result.  \
                       create(dep_name)
            
            if old_deployment.status.ready is not None:
                netconf_deployment_result.status.alive = old_deployment.status.ready
            else:
                netconf_deployment_result.status.error = old_deployment.status.error

            for vdu in old_deployment.vdu:
                netconf_deployment_result.owning_service = vdu.vnf_info
                old_vm_group = vdu.vnf_info + "-" + vdu.vdu 
                
                for old_vm_device in vdu.vm_device:
                    
                    #Build vm-group:
                    vm_group = netconf_deployment_result.vm_group.create(old_vm_group)
                    vm_group.vnf_info = vdu.vnf_info
                    vm_group.vdu = vdu.vdu
                    vm_group.staged_delete = "false"
                    
                    #Build vm-device:
                    vm_device = vm_group.vm_device.create(old_vm_device.device_name)
                    vm_device.id = old_vm_device.vmid
                    vm_device.name = old_vm_device.vmname
                    vm_device.index = 1
                    vm_device.host_id = old_vm_device.hostid
                    vm_device.hostname = old_vm_device.hostname
                    #netsim_port to be updated for netsim devices only. For real devices, this is picked up from the VNFD.
                    #vm_device.netsim_port = '10023'
                        
                    if old_deployment.status.ready is not None:
                        self.log.info("Checking status for vm_device {}. Status is ready at {}".format(vm_device, old_vm_device.status.ready))
                        vm_device.status.create('alive', old_vm_device.status.ready)
                        vm_device.status.create('deployed', old_vm_device.status.ready)
                    
                    #Build Interface data:
                    for old_interface in old_vm_device.interface:
                        self.log.info("Migrating interface information for interface id: {}".format(old_interface.nic_id))
                        interface = vm_device.interface.create(old_interface.nic_id)
                        
                        if old_interface.type is not None:
                            interface.type = old_interface.type
                        
                        if old_interface.vim_interface_name is not None:
                            interface.vim_interface_name = old_interface.vim_interface_name
                        
                        if old_interface.port_id is not None:
                            interface.port_id = old_interface.port_id
                        
                        if old_interface.network is not None:
                            interface.network = old_interface.network
                        
                        if old_interface.subnet is not None:
                            interface.subnet = old_interface.subnet
                        
                        if old_interface.ip_address is not None:
                            interface.ip_address = old_interface.ip_address
                            
                        if old_interface.mac_address is not None:
                            interface.mac_address = old_interface.mac_address
                        
                        if old_interface.netmask is not None:
                            interface.netmask = old_interface.netmask
                        
                        if old_interface.gateway is not None:
                            interface.gateway = old_interface.gateway
            #Delete old NFVO oper data
            del old_res_list[tenant, dep_name, device_name]
        
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
        self.register_service('sample-service-servicepoint', SampleServiceCallback)

        ## Register actions
        self.register_action('vnf-info-migration-actionpoint', VnfInfoMigrationAction)


    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
