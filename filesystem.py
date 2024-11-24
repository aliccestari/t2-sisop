import os
import struct

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
class FileSystem:
    def __init__(self):
        self.fsparam = FileSystemParam()
        self.fat = [0] * self.fsparam.blocks
        self.data_block = bytearray(self.fsparam.block_size)
        self.root_block = self.fsparam.root_block

        if not os.path.exists('filesystem.dat'):
            with open('filesystem.dat', 'wb') as f:
                f.write(bytearray(self.fsparam.blocks * self.fsparam.block_size))

    def load_file_system(self):
        self.fat = self.read_fat('filesystem.dat')

    def init_file_system(self):
        for i in range(self.fsparam.fat_blocks):
            self.fat[i] = 0x7FFE
        self.fat[self.fsparam.root_block] = 0x7FFF
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.fat[i] = 0x0000
        self.write_fat('filesystem.dat', self.fat)
        self.init_root_and_data_blocks()

    def init_root_and_data_blocks(self):
        root_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.dir_entries):
            offset = i * self.fsparam.dir_entry_size
            root_block[offset:offset + self.fsparam.dir_entry_size] = bytearray(self.fsparam.dir_entry_size)
        self.write_block('filesystem.dat', self.fsparam.root_block, root_block)
        empty_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.write_block('filesystem.dat', i, empty_block)

    def find_free_block(self):
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            if self.fat[i] == 0x0000:
                return i
        raise Exception("Erro: Não há blocos livres disponíveis.")

    def allocate_block(self, previous_block=None):
        block = self.find_free_block()
        if previous_block is not None:
            self.fat[previous_block] = block
        self.fat[block] = 0x7FFF
        self.write_fat('filesystem.dat', self.fat)
        return block

    def free_block(self, block):
        while block != 0x7FFF:
            next_block = self.fat[block]
            self.fat[block] = 0x0000
            block = next_block
        self.write_fat('filesystem.dat', self.fat)

    def mkdir(self, path):
        try:
            if len(path.split("/")[-1]) > 25:
                print("Erro: Nome do diretório excede o limite de 25 caracteres.")
                return

            path_parts = path.strip("/").split("/")
            subdir_name = path_parts[-1]
            parent_path = "/".join(path_parts[:-1])

            parent_block = self.root_block if not parent_path else self.find_directory(parent_path, self.fsparam.root_block)

            if parent_block is None:
                print(f"Erro: O diretório pai '{parent_path}' não foi encontrado.")
                return

            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(parent_block, i)
                dir_name = entry.filename.decode('utf-8').strip()
                if dir_name == subdir_name and entry.attributes == 0x02:
                    print(f"Erro: O diretório '{subdir_name}' já existe no diretório '{parent_path}'.")
                    return

            new_block = self.allocate_block()
            if new_block == -1:
                print("Erro: Não há blocos livres disponíveis para criar o diretório.")
                return

            dir_entry = DirEntry()
            dir_entry.filename = bytearray(subdir_name.encode('utf-8')[:25])
            dir_entry.attributes = 0x02
            dir_entry.first_block = new_block
            dir_entry.size = self.fsparam.block_size

            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(parent_block, i)
                if entry.attributes == 0x00:
                    self.write_dir_entry(parent_block, i, dir_entry)
                    print(f"Subdiretório '{subdir_name}' criado com sucesso no diretório '{parent_path}'!")
                    return

            print("Erro: O diretório pai está cheio.")

        except Exception as e:
            print(f"Erro ao tentar criar o diretório: {str(e)}")

    def find_directory(self, path, parent_block):
        path_parts = path.strip("/").split("/")
        current_block = parent_block

        for part in path_parts:
            found = False
            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(current_block, i)
                dir_name = entry.filename.decode('utf-8').rstrip('\x00').strip()

                if dir_name == part and entry.attributes == 0x02:
                    current_block = entry.first_block
                    found = True
                    break

            if not found:
                print(f"Erro: O diretório '{part}' não foi encontrado no bloco {current_block}.")
                return None

        return current_block

    def ls(self, block=None, indent_level=0):
        if block is None:
            block = self.root_block

        try:
            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(block, i)
                dir_name = entry.filename.decode('utf-8').strip()

                if entry.attributes != 0x00:
                    entry_type = "DIR" if entry.attributes == 0x02 else "FILE"
                    print(f"{'  ' * indent_level}- {dir_name}")

                    if entry.attributes == 0x02:
                        self.ls(entry.first_block, indent_level + 1)

        except Exception as e:
            print(f"Erro ao tentar listar o diretório: {str(e)}")

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

    def init(self):
        self.init_file_system()

if __name__ == "__main__":
    fs = FileSystem()
    
    while True:
        print("\nComandos disponíveis:")
        print("init - Inicializar o sistema de arquivos")
        print("load - Carregar o sistema de arquivos")
        print("mkdir [nome] - Criar diretório")
        print("ls - Listar conteúdo do diretório raiz")
        print("quit - Sair do programa")

        comando = input("Digite o comando: ").strip().lower()

        if comando == "init":
            fs.init()
        elif comando == "load":
            fs.load_file_system()
        elif comando.startswith("mkdir"):
            args = comando.split(" ", 1)
            if len(args) > 1 and args[1].strip():
                fs.mkdir(args[1].strip())
            else:
                print("Erro: Nome do diretório não fornecido.")
        elif comando == "ls":
            fs.ls()
        elif comando == "quit":
            print("Saindo do programa...")
            break
        else:
            print("Comando não reconhecido. Tente novamente.")
