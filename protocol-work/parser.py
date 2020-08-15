import struct

def main():
    with open('raw-steerer-data.txt', 'r') as f:
        datas = f.read().splitlines()
    
    for data in datas:
        # Little Endian
        out = struct.unpack("<I", bytes.fromhex(data))
        print(out)


if __name__ == "__main__":
    main()