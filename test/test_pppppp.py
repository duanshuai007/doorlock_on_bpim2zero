import re

msg = "\"http://118.31.135.88:9211/HLSLIVE/S1908170164-2020-08-20-12-00-25.ts?08F42E36-B824-4407-9822-9314D7EAD414\""
partten = r"\"[a-z][A-Z][0-9]+?\""
s = re.search(partten, msg)
print(s)

reg = r'"(http:[.*\S]*?)"'
rule = re.compile(reg)
result = re.findall(rule, msg)
print(result)
