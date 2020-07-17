#!/usr/nbin/env python3
#-*- coding:utf-8 -*-

BOARDCAST_ADDR = "ffffffffffff"
OPENDOOR_TOPIC = "/door_ctrl"
OPENDOOR_RESP_TOPIC = "/door_response"
QR_TOPIC = "/qr_ctrl"
QR_RESP_TOPIC = "/qr_response"
DEVICE_STATUS_TOPIC = "/status"
UPDATE_TOPIC = "/update"
UPDATE_RESP_TOPIC = "/update_resp"
OPENSSH_TOPIC = "/ssh_enable"
OPENSSH_RESP_TOPIC = "/ssh_enable_resp"

DEVICE_INFO_TOPIC = "/test/device_info"
DEVICE_INFO_RESP_TOPIC = "/test/device_info_resp"

DOORSTONE="iotwonderful"

OPENDOOR_MSG = {
	"device_sn" : "",
	"stime" : 0,
	"action" : 0,
	"identify" : 0,
}

OPENDOOR_RESP_MSG = {
	"device_sn" : "",
	"rtime" : 0,
	"result" : 0,
	"identify" : 0,
}

QR_GETWX2VCODE = {
	"device_sn" : "",
	"stime" : 0,
	"type" : 0,
	"identify" : 0,
	"message" : {
		"page" : "",
		"scene" : "",
	},
}

QR_DOWN2VCODE = {
	"device_sn" : "",
	"stime" : 0,
	"type" : 0,
	"identify" : 0,
	"message" : {
		"download" : "",
	},
}

QR_GENERATE2VCODE = {
	"device_sn" : "",
	"stime" : 0,
	"type" : 0,
	"identify" : 0,
	"message" : {
		"data" : "",
	},
}

QR_RESPONSE = {
	"device_sn" : "",
	"rtime" : 0,
	"type" : 0,
	"identify" : 0,
	"status" : "",
}

DEVICE_STATUS = {
	"device_sn" : "",
	"rtime" : 0,
	"status" : 0,
}

UPDATE_INFO = {
	"device_sn" : "",
	"stime" : "",
	"firmware" : {
		"url" : "",
		"version" : "",
		"packetsize" : 0,
		"enable" : "",
		"md5" : "",
	}
}

UPDATE_RESP_INFO = {
	"device_sn" : "",
	"rtime" : "",
	"firmware" : {
		"version" : "",
		"status" : "",
	}
}

OPENSSH_INFO = {
	"device_sn" : "",
	"stime" : "",
	"enable" : 0,
	"opentime" : 0,
}

OPENSSH_RESP_INFO = {
	"device_sn" : "",
	"rtime" : "",
	"status" : 0,
}

DEVICE_INFO = {
	"device_sn" : "",
	"stime" : 0,
	# 0  = get doorlock time
	# !0 = set doorlock time
	"doorlock" : 0,
	"ip" : "",
	"current" : "",
	"thread status" : ""
}
