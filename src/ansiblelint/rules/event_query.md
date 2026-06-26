# event-query

This rule validates `extensions/audit/event_query.yml` files used for indirect
node counting in Ansible Automation Platform 2.6+.

These files define jq queries that extract managed node identity from Ansible
module return data. Each Ansible collection that manages infrastructure (cloud
instances, network devices, virtual machines, etc.) should include an
`event_query.yml` file so AAP can accurately count the nodes being automated.

## Required file location

```
<collection_root>/extensions/audit/event_query.yml
```

## Schema

Each top-level key must be a fully qualified collection name (FQCN) for the
module whose return data the query processes. The value must contain a `query`
field with a jq expression that produces an object with these required fields:

| Field | Description |
|---|---|
| `name` | A unique string identifier for the managed node |
| `canonical_facts` | An object with at least one non-null unique identifier (e.g., GUID, MOID, ARN) |
| `facts` | An object containing `device_type` and other classification metadata |

The `device_type` field in `facts` must use a value from the normalized taxonomy:

| Category | Valid Values |
|---|---|
| **Compute** | `virtual_machine`, `bare_metal`, `container` |
| **Networking** | `switch`, `router`, `firewall`, `load_balancer`, `access_point` |
| **Cloud** | `cloud_instance`, `cloud_service`, `serverless_function` |
| **Storage** | `storage_array`, `storage_node` |
| **Management** | `controller`, `appliance`, `management_server` |
| **VMware** | `esxi_host`, `vcenter_appliance`, `cluster`, `resource_pool`, `datastore` |
| **Organizational** | `folder`, `organizational_unit` |
| **Generic** | `resource`, `endpoint`, `sensor` |

## Problematic Code

```yaml
---
# Bad FQCN — missing namespace
vmware.cluster_info: # <- Not a valid FQCN
  query: >-
    .clusters | {
      name: .moid,
      canonical_facts: { moid: .moid },
      facts: { device_type: "MyCluster" }
    }

# Missing required field
vmware.vmware.guest_info:
  query: >-
    .guests[] | {
      name: ("guest_info:" + (.moid | tostring)),
      facts: { device_type: "virtual_machine" }
    }
  # <- Missing canonical_facts in query output

# Non-standard device_type
vmware.vmware.esxi_host:
  query: >-
    .host | select(. != null) | {
      name: ("esxi_host:" + (.moid | tostring)),
      canonical_facts: { moid: .moid },
      facts: { device_type: "ESXi" }
    }
  # <- "ESXi" is not in the normalized taxonomy; use "esxi_host"
```

## Correct Code

```yaml
---
vmware.vmware.cluster_info:
  query: >-
    .clusters | select(. != null) | {
      name: ("cluster_info:" + (.moid | tostring)),
      canonical_facts: {
        module: "cluster_info",
        moid: .moid
      },
      facts: {
        device_type: "cluster",
        infra_type: "PrivateCloudVMWARE"
      }
    }

vmware.vmware.guest_info:
  query: >-
    .guests[] | {
      name: ("guest_info:" + (.moid | tostring)),
      canonical_facts: {
        module: "guest_info",
        moid: .moid
      },
      facts: {
        device_type: "virtual_machine",
        infra_type: "PrivateCloudVMWARE"
      }
    }

microsoft.ad.computer:
  query: >-
    if ($data.object_guid // null) != null
      and ($data.distinguished_name // null) != null
    then {
      name: $data.distinguished_name,
      canonical_facts: {
        object_guid: $data.object_guid,
        sid: ($data.sid // null)
      },
      facts: {
        device_type: "virtual_machine",
        platform: "microsoft_ad"
      }
    }
    else empty end
```
