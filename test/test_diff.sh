#!/bin/bash

DOWNLOADDIR="/home/swann/workgit/acs"
tar="/home/swann/test"

for var in $(diff -r ${DOWNLOADDIR} ${tar} | grep "Only in ${tar}" | awk -F"Only in ${tar}" '{print $2}' | awk -F": " '{print $1"/"$2}')
do
	echo ${var}
done
