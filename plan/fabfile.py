from fabric.api import env, run

env.user = 'root'

def update():
    print("Executing on %(host)s as %(user)s" % env)
    run('/opt/rerun-chef-basenode.sh')
    run('/opt/rerun-chef-dtrs.sh')
<<<<<<< HEAD
    run('/opt/rerun-chef-provisioner-start.sh')
    run('/opt/rerun-chef-epum.sh')
    run('/opt/rerun-chef-phantom.sh')
    run('/opt/rerun-chef-phantomweb.sh')
=======
    run('/opt/rerun-chef-provisioner.sh')
    run('/opt/rerun-chef-epum.sh')
    run('/opt/rerun-chef-phantom.sh')
    run('/opt/rerun-chef-phantomweb.sh')
    run('/opt/rerun-chef-opentsdbproxy.sh')
>>>>>>> refs/remotes/nimbusproject/master
