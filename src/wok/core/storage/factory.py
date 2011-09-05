# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.storage.sfs import SfsStorage

STORAGES = {
	"sfs" : SfsStorage
}

def create_storage(name, context, conf):
	if name is None:
		name = "sfs"

	if name not in STORAGES:
		raise Exception("Unknown storage: " + name)

	return STORAGES[name](context, conf)
