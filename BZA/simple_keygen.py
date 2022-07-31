
def main():
    serial = input('serial: ')
    if len(serial) != 16:
        print("bad serial")
        return
    else:
        serial_len = len(serial)
        for i in range(serial_len):
            if i % 2 == 0 and i != serial_len + 1:
                if ord(serial[i]) - ord(serial[i + 1]) != -1:
                    print("bad serial")
                    return

        print("good serial")

main()
