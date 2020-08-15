import uuid
import sys

if __name__ == "__main__":
	print(len(sys.argv))
	if len(sys.argv)< 2:
		print("error")
		exit
	sn = uuid.UUID(int = uuid.getnode())
	print(sn)
