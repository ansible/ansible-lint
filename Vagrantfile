Vagrant.configure("2") do |config|
  config.vm.box = ENV.fetch("FEDORA_BOX", "fedora/43-cloud-base")
  config.vm.hostname = "ansible-lint-issue-4862"
  config.vm.box_check_update = false

  config.vm.provider "virtualbox" do |vb|
    vb.cpus = 2
    vb.memory = 2048
  end

  config.vm.provision "shell", inline: <<-SHELL
    set -euo pipefail
    sudo dnf -y install ansible-lint ansible-core
    ansible-lint --version
  SHELL
end
