# ajv errors

```json
[
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'ansible.builtin.import_playbook'",
    "params": {
      "missingProperty": "ansible.builtin.import_playbook"
    },
    "schemaPath": "#/oneOf/0/required"
  },
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'import_playbook'",
    "params": {
      "missingProperty": "import_playbook"
    },
    "schemaPath": "#/oneOf/1/required"
  },
  {
    "instancePath": "/0",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "hosts"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "gather_subset"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "tasks"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0/gather_subset/0",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/gather_subset/items/anyOf/0/type"
  },
  {
    "instancePath": "/0/gather_subset/0",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "all",
        "min",
        "all_ipv4_addresses",
        "all_ipv6_addresses",
        "apparmor",
        "architecture",
        "caps",
        "chroot,cmdline",
        "date_time",
        "default_ipv4",
        "default_ipv6",
        "devices",
        "distribution",
        "distribution_major_version",
        "distribution_release",
        "distribution_version",
        "dns",
        "effective_group_ids",
        "effective_user_id",
        "env",
        "facter",
        "fips",
        "hardware",
        "interfaces",
        "is_chroot",
        "iscsi",
        "kernel",
        "local",
        "lsb",
        "machine",
        "machine_id",
        "mounts",
        "network",
        "ohai",
        "os_family",
        "pkg_mgr",
        "platform",
        "processor",
        "processor_cores",
        "processor_count",
        "python",
        "python_version",
        "real_user_id",
        "selinux",
        "service_mgr",
        "ssh_host_key_dsa_public",
        "ssh_host_key_ecdsa_public",
        "ssh_host_key_ed25519_public",
        "ssh_host_key_rsa_public",
        "ssh_host_pub_keys",
        "ssh_pub_keys",
        "system",
        "system_capabilities",
        "system_capabilities_enforced",
        "user",
        "user_dir",
        "user_gecos",
        "user_gid",
        "user_id",
        "user_shell",
        "user_uid",
        "virtual",
        "virtualization_role",
        "virtualization_type"
      ]
    },
    "schemaPath": "#/properties/gather_subset/items/anyOf/0/enum"
  },
  {
    "instancePath": "/0/gather_subset/0",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/gather_subset/items/anyOf/1/type"
  },
  {
    "instancePath": "/0/gather_subset/0",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "!all",
        "!min",
        "!all_ipv4_addresses",
        "!all_ipv6_addresses",
        "!apparmor",
        "!architecture",
        "!caps",
        "!chroot,cmdline",
        "!date_time",
        "!default_ipv4",
        "!default_ipv6",
        "!devices",
        "!distribution",
        "!distribution_major_version",
        "!distribution_release",
        "!distribution_version",
        "!dns",
        "!effective_group_ids",
        "!effective_user_id",
        "!env",
        "!facter",
        "!fips",
        "!hardware",
        "!interfaces",
        "!is_chroot",
        "!iscsi",
        "!kernel",
        "!local",
        "!lsb",
        "!machine",
        "!machine_id",
        "!mounts",
        "!network",
        "!ohai",
        "!os_family",
        "!pkg_mgr",
        "!platform",
        "!processor",
        "!processor_cores",
        "!processor_count",
        "!python",
        "!python_version",
        "!real_user_id",
        "!selinux",
        "!service_mgr",
        "!ssh_host_key_dsa_public",
        "!ssh_host_key_ecdsa_public",
        "!ssh_host_key_ed25519_public",
        "!ssh_host_key_rsa_public",
        "!ssh_host_pub_keys",
        "!ssh_pub_keys",
        "!system",
        "!system_capabilities",
        "!system_capabilities_enforced",
        "!user",
        "!user_dir",
        "!user_gecos",
        "!user_gid",
        "!user_id",
        "!user_shell",
        "!user_uid",
        "!virtual",
        "!virtualization_role",
        "!virtualization_type"
      ]
    },
    "schemaPath": "#/properties/gather_subset/items/anyOf/1/enum"
  },
  {
    "instancePath": "/0/gather_subset/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/properties/gather_subset/items/anyOf"
  },
  {
    "instancePath": "/0",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/items/oneOf"
  }
]
```

# check-jsonschema

stdout:

```json
{
  "status": "fail",
  "successes": [],
  "errors": [
    {
      "filename": "negative_test/playbooks/gather_subset3.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'gather_subset': [1], 'tasks': [{'ansible.builtin.debug': {'msg': 'foo'}}]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'gather_subset', 'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].gather_subset[0]",
        "message": "1 is not one of ['all', 'min', 'all_ipv4_addresses', 'all_ipv6_addresses', 'apparmor', 'architecture', 'caps', 'chroot,cmdline', 'date_time', 'default_ipv4', 'default_ipv6', 'devices', 'distribution', 'distribution_major_version', 'distribution_release', 'distribution_version', 'dns', 'effective_group_ids', 'effective_user_id', 'env', 'facter', 'fips', 'hardware', 'interfaces', 'is_chroot', 'iscsi', 'kernel', 'local', 'lsb', 'machine', 'machine_id', 'mounts', 'network', 'ohai', 'os_family', 'pkg_mgr', 'platform', 'processor', 'processor_cores', 'processor_count', 'python', 'python_version', 'real_user_id', 'selinux', 'service_mgr', 'ssh_host_key_dsa_public', 'ssh_host_key_ecdsa_public', 'ssh_host_key_ed25519_public', 'ssh_host_key_rsa_public', 'ssh_host_pub_keys', 'ssh_pub_keys', 'system', 'system_capabilities', 'system_capabilities_enforced', 'user', 'user_dir', 'user_gecos', 'user_gid', 'user_id', 'user_shell', 'user_uid', 'virtual', 'virtualization_role', 'virtualization_type']"
      },
      "num_sub_errors": 8,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'gather_subset', 'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'gather_subset': [1], 'tasks': [{'ansible.builtin.debug': {'msg': 'foo'}}]} is not valid under any of the given schemas"
        },
        {
          "path": "$[0]",
          "message": "'ansible.builtin.import_playbook' is a required property"
        },
        {
          "path": "$[0]",
          "message": "'import_playbook' is a required property"
        },
        {
          "path": "$[0].gather_subset[0]",
          "message": "1 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].gather_subset[0]",
          "message": "1 is not one of ['all', 'min', 'all_ipv4_addresses', 'all_ipv6_addresses', 'apparmor', 'architecture', 'caps', 'chroot,cmdline', 'date_time', 'default_ipv4', 'default_ipv6', 'devices', 'distribution', 'distribution_major_version', 'distribution_release', 'distribution_version', 'dns', 'effective_group_ids', 'effective_user_id', 'env', 'facter', 'fips', 'hardware', 'interfaces', 'is_chroot', 'iscsi', 'kernel', 'local', 'lsb', 'machine', 'machine_id', 'mounts', 'network', 'ohai', 'os_family', 'pkg_mgr', 'platform', 'processor', 'processor_cores', 'processor_count', 'python', 'python_version', 'real_user_id', 'selinux', 'service_mgr', 'ssh_host_key_dsa_public', 'ssh_host_key_ecdsa_public', 'ssh_host_key_ed25519_public', 'ssh_host_key_rsa_public', 'ssh_host_pub_keys', 'ssh_pub_keys', 'system', 'system_capabilities', 'system_capabilities_enforced', 'user', 'user_dir', 'user_gecos', 'user_gid', 'user_id', 'user_shell', 'user_uid', 'virtual', 'virtualization_role', 'virtualization_type']"
        },
        {
          "path": "$[0].gather_subset[0]",
          "message": "1 is not of type 'string'"
        },
        {
          "path": "$[0].gather_subset[0]",
          "message": "1 is not one of ['!all', '!min', '!all_ipv4_addresses', '!all_ipv6_addresses', '!apparmor', '!architecture', '!caps', '!chroot,cmdline', '!date_time', '!default_ipv4', '!default_ipv6', '!devices', '!distribution', '!distribution_major_version', '!distribution_release', '!distribution_version', '!dns', '!effective_group_ids', '!effective_user_id', '!env', '!facter', '!fips', '!hardware', '!interfaces', '!is_chroot', '!iscsi', '!kernel', '!local', '!lsb', '!machine', '!machine_id', '!mounts', '!network', '!ohai', '!os_family', '!pkg_mgr', '!platform', '!processor', '!processor_cores', '!processor_count', '!python', '!python_version', '!real_user_id', '!selinux', '!service_mgr', '!ssh_host_key_dsa_public', '!ssh_host_key_ecdsa_public', '!ssh_host_key_ed25519_public', '!ssh_host_key_rsa_public', '!ssh_host_pub_keys', '!ssh_pub_keys', '!system', '!system_capabilities', '!system_capabilities_enforced', '!user', '!user_dir', '!user_gecos', '!user_gid', '!user_id', '!user_shell', '!user_uid', '!virtual', '!virtualization_role', '!virtualization_type']"
        },
        {
          "path": "$[0].gather_subset[0]",
          "message": "1 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
