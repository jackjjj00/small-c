class SystemMemory:
    def __init__(self, size=65536, start_address=1000):
        self.size=size
        self.start_address=start_address
        self.buffer=bytearray(size)
        self.next_free_address=start_address

    def allocate(self, num_bytes):
        if self.next_free_address + num_bytes >= self.start_address + self.size :
            raise RuntimeError("error: out of memory")
        allocated_address = self.next_free_address
        self.next_free_address += num_bytes
        return allocated_address
    
    def get_offset(self, address):
        if address==0:
            raise RuntimeError("error: Null pointer dereference")
        offset= address- self.start_address
        if offset < 0 or offset >= self.size :
            raise RuntimeError(f"error: Segmentation fault at address {address}")
        return offset
    
    def write_char(self, address, value):
        offset = self.get_offset(address)
        self.buffer[offset] = int(value) & 0xFF

    def write_int(self, address, value):
        offset = self.get_offset(address)
        val = int(value)
        for i in range(4):
            self.buffer[offset + i] = (val >> (8 * i)) & 0xFF

    def read_char(self, address):
        offset = self.get_offset(address)
        val = self.buffer[offset]
        # 還原 8-bit 有號整數
        if val >= 128:
            val -= 256
        return val

    def read_int(self, address):

            offset = self.get_offset(address)
            val = 0
            
            for i in range(4):
                val = val | (self.buffer[offset + i] << (8 * i))
            # 還原 32-bit 有號整數
            if val >= 0x80000000:
                val -= 0x100000000
            return val
    
    def reset(self):
        self.buffer = bytearray(self.size)
        self.next_free_address = self.start_address