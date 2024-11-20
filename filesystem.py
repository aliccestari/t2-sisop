# FileSystemParam class
class FileSystemParam:
    block_size = 1024
    blocks = 2048
    fat_size = blocks * 2
    fat_blocks = fat_size // block_size
    root_block = fat_blocks
    dir_entry_size = 32
    dir_entries = block_size // dir_entry_size

# DirEntry class
class DirEntry:
    def __init__(self):
        self.filename = bytearray(25)
        self.attributes = 0
        self.first_block = 0
        self.size = 0

# FileSystem class
import os
import struct

class FileSystem:
    def __init__(self):
        self.fsparam = FileSystemParam()
        self.fat = [0] * self.fsparam.blocks
        self.data_block = bytearray(self.fsparam.block_size)
        
        # Check and create 'filesystem.dat' if it doesn't exist
        if not os.path.exists('filesystem.dat'):
            with open('filesystem.dat', 'wb') as f:
                f.write(bytearray(self.fsparam.blocks * self.fsparam.block_size))  # Initialize file with zeros

    def read_block(self, file, block):
        record = bytearray(self.fsparam.block_size)
        try:
            with open(file, 'r+b') as file_store:
                file_store.seek(block * self.fsparam.block_size)
                file_store.readinto(record)
        except IOError as e:
            print(e)
        return record

    def write_block(self, file, block, record):
        try:
            with open(file, 'r+b') as file_store:
                file_store.seek(block * self.fsparam.block_size)
                file_store.write(record[:self.fsparam.block_size])
        except IOError as e:
            print(e)

    def read_fat(self, file):
        record = [0] * self.fsparam.blocks
        try:
            with open(file, 'r+b') as file_store:
                file_store.seek(0)
                for i in range(self.fsparam.blocks):
                    record[i] = struct.unpack('h', file_store.read(2))[0]
        except IOError as e:
            print(e)
        return record

    def write_fat(self, file, fat):
        try:
            with open(file, 'r+b') as file_store:
                file_store.seek(0)
                for i in range(self.fsparam.blocks):
                    file_store.write(struct.pack('h', fat[i]))
        except IOError as e:
            print(e)

    def read_dir_entry(self, block, entry):
        bytes_block = self.read_block('filesystem.dat', block)
        offset = entry * self.fsparam.dir_entry_size
        dir_entry = DirEntry()

        dir_entry.filename = bytes_block[offset:offset + 25]
        dir_entry.attributes = bytes_block[offset + 25]
        dir_entry.first_block = struct.unpack('h', bytes_block[offset + 26:offset + 28])[0]
        dir_entry.size = struct.unpack('i', bytes_block[offset + 28:offset + 32])[0]

        return dir_entry

    def write_dir_entry(self, block, entry, dir_entry):
        bytes_block = self.read_block('filesystem.dat', block)
        offset = entry * self.fsparam.dir_entry_size

        bytes_block[offset:offset + 25] = dir_entry.filename
        bytes_block[offset + 25] = dir_entry.attributes
        bytes_block[offset + 26:offset + 28] = struct.pack('h', dir_entry.first_block)
        bytes_block[offset + 28:offset + 32] = struct.pack('i', dir_entry.size)

        self.write_block('filesystem.dat', block, bytes_block)

    def test_file_system(self):
        for i in range(self.fsparam.fat_blocks):
            self.fat[i] = 0x7ffe
        self.fat[self.fsparam.root_block] = 0x7fff
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.fat[i] = 0
        self.write_fat('filesystem.dat', self.fat)

        self.data_block = bytearray(self.fsparam.block_size)
        self.write_block('filesystem.dat', self.fsparam.root_block, self.data_block)

        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.write_block('filesystem.dat', i, self.data_block)

        dir_entry = DirEntry()
        name = "file1"
        dir_entry.filename = bytearray(name.encode('utf-8'))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 1111
        dir_entry.size = 222
        self.write_dir_entry(self.fsparam.root_block, 0, dir_entry)

        name = "file2"
        dir_entry.filename = bytearray(name.encode('utf-8'))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 2222
        dir_entry.size = 333
        self.write_dir_entry(self.fsparam.root_block, 1, dir_entry)

        name = "file3"
        dir_entry.filename = bytearray(name.encode('utf-8'))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 3333
        dir_entry.size = 444
        self.write_dir_entry(self.fsparam.root_block, 2, dir_entry)

        for i in range(self.fsparam.dir_entries):
            dir_entry = self.read_dir_entry(self.fsparam.root_block, i)
            print(f"Entry {i}, file: {dir_entry.filename.decode('utf-8').strip()} attr: {dir_entry.attributes} first: {dir_entry.first_block} size: {dir_entry.size}")

# App equivalent
if __name__ == "__main__":
    fs = FileSystem()
    fs.test_file_system()
