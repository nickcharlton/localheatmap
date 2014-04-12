# -*- mode: ruby -*_
# vi: set ft=ruby ;

Vagrant.configure('2') do |config|
  config.vm.hostname = 'localheatmap'
  config.vm.box = 'boxes-precise64-chef'
  config.vm.box_url = 'http://boxes.nickcharlton.net/precise64-chef-virtualbox.box'

  # forward a port
  config.vm.network 'forwarded_port', guest: 5000, host: 5000, auto_correct: true

  # enable agent forwarding to allow us to use private git repos
  config.ssh.forward_agent = true

  # ensure the basic packages exist to get it all working
  config.vm.provision 'shell', inline: 'sudo apt-get -yqq install git '\
                                       'python-virtualenv ipython python-dev'
end
