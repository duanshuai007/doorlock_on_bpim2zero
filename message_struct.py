#!/usr/nbin/env python3
#-*- coding:utf-8 -*-


OPENDOOR_TOPIC = "/door_ctrl"
OPENDOOR_RESP_TOPIC = "/door_response"
QR_TOPIC = "/qr_ctrl"
QR_RESP_TOPIC = "/qr_response"

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
