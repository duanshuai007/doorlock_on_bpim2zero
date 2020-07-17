


gzfile="ffffff"
salt="iotwonderful"
cmd = "dd if={} | openssl des3 -d -k {}{}{} | tar zxvf - > /dev/null".format(gzfile, "\\\"", salt, "\\\"")
print(cmd)
