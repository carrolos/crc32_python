import timeit

msb_generator = 0x04C11DB7
lsb_generator = 0xEDB88320

def pad_next_4(x: int) -> int:
    return ((x) + (3)) & (~3)

def write_file(arr, name: str) -> None:
    print(f"writing file {name}")
    outfile = open(name, 'w')
    for elem in arr:
        outfile.write(format(elem, '#010x'))
        outfile.write("\n")
    outfile.close()

def crc32_tab_gen_msb(gen_file: bool) -> list[int]:
    arr = []
    for i in range(256):
        runner = i << 24
        for j in range(8):
            b8 = (runner >> 31) & 1
            runner = (runner << 1) & 0xFFFFFFFF
            if b8 == 1:
                runner ^= msb_generator
        arr.append(runner)
    if gen_file:
        write_file(arr, 'tab_msb.txt')
    return arr

def crc32_via_tab_msb(data: bytes, tab: list[int]) -> int:
    rem = 0xFFFFFFFF
    for i in range(len(data)):
        rem = (tab[ data[i] ^ ((rem >> 24) & 0xFF) ] ^ (rem << 8) ) & 0xFFFFFFFF
    return rem

def crc32_first_8_msb(rem: int) -> int:
    for i in range(8):
        old_msb = (rem >> 31) & 1
        rem = (rem << 1) & 0xFFFFFFFF
        if old_msb == 1:
            rem ^= msb_generator
    return rem

def crc32_bytewise_msb(data: bytes) -> int:
    rem = 0xFFFFFFFF
    for i in range(len(data)):
        rem ^= (data[i] << 24)
        rem = crc32_first_8_msb(rem)
    return rem

def crc32_bitwise_msb(data: bytes) -> int:
    rem = 0xFFFFFFFF
    for i in range(len(data)):
        cur_byte = data[i]
        # goes in reverse from bit 7 to bit 0
        for j in range(7, -1, -1):
            # places msb of byte on msb of remainder
            cur_bit = ((cur_byte >> j) & 1) << 31
            rem ^= cur_bit
            old_msb = (rem >> 31) & 1
            rem = (rem << 1) & 0xFFFFFFFF
            if old_msb == 1:
                rem ^= msb_generator
    return rem

def crc32_wordwise_msb(data: bytes) -> int:
    rem = 0xFFFFFFFF
    prev_4 = pad_next_4(len(data) - 4)
    for i in range(0, prev_4, 4):
        for j in range(4):
            rem ^= (data[i+j] << ((3 - j) * 8))
        for k in range(32):
            old_msb = (rem >> 31) & 1
            rem = (rem << 1) & 0xFFFFFFFF
            if old_msb == 1:
                rem ^= msb_generator

    next_4 = pad_next_4(len(data))
    d = 0
    for i in range(next_4 - 4, next_4):
        d = i - (next_4 - 4)
        if i < len(data):
            rem ^= (data[i] << ((3 - d) * 8))
        else:
            break

    assert(d < 4)
    for k in range(d * 8):
        old_msb = (rem >> 31) & 1
        rem = (rem << 1) & 0xFFFFFFFF
        if old_msb == 1:
            rem ^= msb_generator

    return rem

def crc32_wordwise_lsb(data: bytes) -> int:
    rem = 0xFFFFFFFF
    prev_4 = pad_next_4(len(data) - 4)
    for i in range(0, prev_4, 4):
        for j in range(4):
            rem ^= (data[i+j] << (j * 8))
        for k in range(32):
            old_lsb = rem & 1
            rem >>= 1
            if old_lsb == 1:
                rem ^= lsb_generator

    next_4 = pad_next_4(len(data))
    d = 0
    for i in range(next_4 - 4, next_4):
        d = i - (next_4 - 4)
        if i < len(data):
            rem ^= (data[i] << (d * 8))
        else:
            break

    assert(d < 4)
    for k in range(d * 8):
        old_lsb = rem & 1
        rem >>= 1
        if old_lsb == 1:
            rem ^= lsb_generator

    return rem

def crc32_tab_gen_lsb(gen_file: bool) -> list[int]:
    arr = []
    for i in range(256):
        runner = i
        for j in range(8):
            old_lsb = runner & 1
            runner >>= 1
            if (old_lsb == 1):
                runner ^= lsb_generator
        arr.append(runner)
    if gen_file:
        write_file(arr, 'tab_lsb.txt')
    return arr

def crc32_via_tab_lsb(data: bytes, tab: list[int]) -> int:
    rem = 0xFFFFFFFF
    for i in range(len(data)):
        rem = (tab[ (rem ^ data[i]) & 0xFF ] ^ (rem >> 8)) & 0xFFFFFFFF
    return rem

def crc32_last_8_lsb(rem: int) -> int:
	for i in range(8):
		old_lsb = rem & 1
		rem >>= 1
		if old_lsb == 1:
			rem ^= lsb_generator
	return rem

def crc32_bytewise_lsb(data: bytes) -> int:
    rem = 0xFFFFFFFF # initialization of all ones
    for i in range(len(data)):
        rem ^= data[i]
        rem = crc32_last_8_lsb(rem)
    return rem

def crc32_bitwise_lsb(data: bytes) -> int:
    rem = 0xFFFFFFFF
    for i in range(len(data)):
        cur_byte = data[i]
        for j in range(8):
            cur_bit = (cur_byte >> j) & 1
            rem ^= cur_bit
            old_lsb = rem & 1
            rem >>= 1
            if old_lsb == 1:
                rem ^= lsb_generator
    return rem

def print_outcome(left_val: int, left_desc: str, right_val: int, right_desc: str, reflect: bool) -> None:
    outcome = "true" if left_val == right_val else "false"
    order = "lsb" if reflect else "msb"
    print(f"crc32 {order} {left_desc} = <{hex(left_val)}> ?= <{hex(right_val)}> = {right_desc}? {outcome}")

def main():
    message = "hello, world!".encode("utf-8")

    lsb_arr = crc32_tab_gen_lsb(False)
    assert(len(lsb_arr) == 256)
    bytewise_lsb = crc32_bytewise_lsb(message)
    via_tab_lsb = crc32_via_tab_lsb(message, lsb_arr)

#    print_outcome(bytewise_lsb, "bytewise", via_tab_lsb, "tab", True)

    msb_arr = crc32_tab_gen_msb(False)
    bytewise_msb = crc32_bytewise_msb(message)
    via_tab_msb = crc32_via_tab_msb(message, msb_arr)

#    print_outcome(bytewise_msb, "bytewise", via_tab_msb, "tab", False)

    lsb_bitwise = crc32_bitwise_lsb(message)
#    print_outcome(bytewise_lsb, "bytewise", lsb_bitwise, "bitwise", True)
    msb_bitwise = crc32_bitwise_msb(message)
    print_outcome(bytewise_msb, "bytewise", msb_bitwise, "bitwise", False)

    lsb_wordwise = crc32_wordwise_lsb(message)
#    print_outcome(bytewise_lsb, "bytewise", lsb_wordwise, "wordwise", True)

    msb_wordwise = crc32_wordwise_msb(message)
#    print_outcome(bytewise_msb, "bytewise", msb_wordwise, "wordwise", False)

    print("Running benchmarks. First up, msb versions")
    print(f"\ttimeit results for bitwise: {timeit.timeit(lambda: crc32_bitwise_msb(message))}")
    print(f"\ttimeit results for bytewise: {timeit.timeit(lambda: crc32_bytewise_msb(message))}")
    print(f"\ttimeit results for table: {timeit.timeit(lambda: crc32_via_tab_msb(message, msb_arr))}")
    print(f"\ttimeit results for wordwise: {timeit.timeit(lambda: crc32_wordwise_msb(message))}")
    print("Now running lsb versions")
    print(f"\ttimeit results for bitwise: {timeit.timeit(lambda: crc32_bitwise_lsb(message))}")
    print(f"\ttimeit results for bytewise: {timeit.timeit(lambda: crc32_bytewise_lsb(message))}")
    print(f"\ttimeit results for table: {timeit.timeit(lambda: crc32_via_tab_lsb(message, lsb_arr))}")
    print(f"\ttimeit results for wordwise: {timeit.timeit(lambda: crc32_wordwise_lsb(message))}")

    
if __name__ == "__main__":
    main()
