import os
import sys
import time

import grpc
from chirpstack_api import api
import random
from datetime import datetime

# Configuration.

# This must point to the API interface.
server = "10.1.199.203:8079"

# The DevEUI for which you want to enqueue the downlink.
dev_eui = "0000005e81fa12f4"

# The API token (retrieved using the web-interface).
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6ImQxYTZkNTM5LTQ4NDQtNDMyZC1iNzAyLTYzMDk0N2I1ZWJmZSIsInR5cCI6ImtleSJ9.iQni_csHZPhhV1WPW_FgVlcBztuztB3Ajc1KBkjQ5WI"

# Define the API key meta-data.
auth_token = [("authorization", "Bearer %s" % api_token)]

def createChannel(server):
  try:
    # Connect with TLS
    channel = grpc.insecure_channel(server)
    
    # Device-queue API client.
    client = api.MulticastGroupServiceStub(channel)
    # client = api.DeviceServiceStub(channel)
    
  except grpc.RpcError as e:
    print('error:',type(e))
    
  print("Connected to " + server)
  
  return client




def create_devices():
    
    try:
        req = api.CreateDeviceRequest()
        print('creating Device with DevEUI...')
        req.device.dev_eui           = "0000005e81fa12ff"
        req.device.name              = "to delete later"
        req.device.description       = "just an experimental setup"
        req.device.application_id    = "852523ed-05f6-4526-b27b-2b52ba44158b"
        req.device.device_profile_id = "428b6177-45b9-4df3-9578-ff2b079e5e6a"
        req.device.is_disabled       = False
        resp = client.Create(req, metadata=auth_token)
    except grpc.RpcError as e:
        print('error:',type(e))
    try:
        req = api.CreateDeviceKeysRequest()
        print('creating keys for device DevEUI...')
        req.device_keys.dev_eui = "0000005e81fa12ff"
        req.device_keys.nwk_key = "00000000000000000000000000000002"
        req.device_keys.app_key = "00000000000000000000000000000002"
        resp = client.CreateKeys(req, metadata=auth_token)
    except  grpc.RpcError as e:
        print('error:',type(e))

    return None

def create_multicast_group(client):
  req = api.CreateMulticastGroupRequest()
  req.multicast_group.name                    = "experimental group"
  req.multicast_group.application_id          = "852523ed-05f6-4526-b27b-2b52ba44158b"
  req.multicast_group.region                  = "EU868"
  req.multicast_group.mc_addr                 = "01488762"
  req.multicast_group.mc_nwk_s_key            = "bcb14c4a59696b9e31d64da8d901bc67"
  req.multicast_group.mc_app_s_key            = "a76682787466817f641d56dff9f8ba33"
  req.multicast_group.f_cnt                   = 0
  req.multicast_group.group_type              = 0
  req.multicast_group.dr                      = 0
  req.multicast_group.frequency               = 868000000
  req.multicast_group.class_c_scheduling_type = 0


  resp = client.Create(req, metadata=auth_token)
  mlt_grp_id = resp.id


  req = api.AddDeviceToMulticastGroupRequest()
  req.multicast_group_id  = mlt_grp_id
  req.dev_eui             = "0000005e81fa12f4"

  resp = client.AddDevice(req, metadata=auth_token)


  req = api.AddGatewayToMulticastGroupRequest()
  req.multicast_group_id = mlt_grp_id
  req.gateway_id         = "0016c001f1040422"

  resp = client.AddGateway(req, metadata=auth_token)


  return mlt_grp_id

if __name__ == "__main__":
  client = createChannel(server)

  # mlt_grp_id = create_multicast_group(client)

  i = 0

  data = [None] * 16

  while True:

    data = [random.randint(0x00, 0xFF) for _ in range(16)]
    data[0] = 0x01
    
    req = api.EnqueueMulticastGroupQueueItemRequest()
    req.queue_item.multicast_group_id = "b5814663-d5f1-4d8d-bad3-e7595de7e61a"
    req.queue_item.f_port             = 1
    req.queue_item.data               = bytes(data)
    req.queue_item.f_cnt              = i

    resp = client.Enqueue(req, metadata=auth_token)
    print(f"rak group {resp.f_cnt}")

    time.sleep(2)


    data = [random.randint(0x00, 0xFF) for _ in range(16)]
    data[0]=0x02

    req = api.EnqueueMulticastGroupQueueItemRequest()
    req.queue_item.multicast_group_id = "cb7eed18-8409-4825-9aa5-f120436a9901"
    req.queue_item.f_cnt              = i
    req.queue_item.f_port             = 1
    req.queue_item.data               = bytes(data)

    resp = client.Enqueue(req, metadata=auth_token)
    print(f"raspberry lab {resp.f_cnt}")   
    
    time.sleep(2)


    data = [random.randint(0x00, 0xFF) for _ in range(16)]
    data[0]=0x03

    req = api.EnqueueMulticastGroupQueueItemRequest()
    req.queue_item.multicast_group_id = "6b5a617d-d2e9-4c1d-bb5e-5a56519e4442"
    req.queue_item.f_cnt              = i
    req.queue_item.f_port             = 1
    req.queue_item.data               = bytes(data)
    
    resp = client.Enqueue(req, metadata=auth_token)
    print(f"raspberry roof {resp.f_cnt}")

    print(f"Broadcast #{i}")
    i += 1
    if i == 100:
        break

    time.sleep(65)
