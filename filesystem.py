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

        # Check and create 'filesystem.dat' if it doesn't exist
<<<<<<< HEAD
        if not os.path.exists("filesystem.dat"):
            with open("filesystem.dat", "wb") as f:
                f.write(
                    bytearray(self.fsparam.blocks * self.fsparam.block_size)
                )  # Initialize file with zeros
=======
        if not os.path.exists('filesystem.dat'):
            with open('filesystem.dat', 'wb') as f:
                f.write(bytearray(self.fsparam.blocks * self.fsparam.block_size))  # Initialize file with zeros
                
    def init_file_system(self):
        # Reservar blocos para FAT
        for i in range(self.fsparam.fat_blocks):
            self.fat[i] = 0x7FFE  # Blocos reservados para FAT

        # Reservar bloco para diretório raiz
        self.fat[self.fsparam.root_block] = 0x7FFF  # Diretório raiz

        # Marcar blocos de dados como livres
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.fat[i] = 0x0000  # Livre

        # Persistir a FAT no arquivo 'filesystem.dat'
        self.write_fat('filesystem.dat', self.fat)

        print("FAT inicializada com sucesso!")
        
        # Configurar diretório raiz e zerar blocos de dados
        self.init_root_and_data_blocks()
        
    def init_root_and_data_blocks(self):
        # Inicializar o bloco do diretório raiz
        root_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.dir_entries):
            offset = i * self.fsparam.dir_entry_size
            root_block[offset:offset + self.fsparam.dir_entry_size] = bytearray(self.fsparam.dir_entry_size)
        self.write_block('filesystem.dat', self.fsparam.root_block, root_block)

        print("Diretório raiz inicializado com sucesso!")

        # Zerar todos os blocos de dados
        empty_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.write_block('filesystem.dat', i, empty_block)

        print("Blocos de dados zerados com sucesso!")
>>>>>>> 56c5b1bf42591b39aefb714a0913768c932fcb73

    def read_block(self, file, block):
        record = bytearray(self.fsparam.block_size)
        try:
            with open(file, "r+b") as file_store:
                file_store.seek(block * self.fsparam.block_size)
                file_store.readinto(record)
        except IOError as e:
            print(e)
        return record

    def write_block(self, file, block, record):
        try:
            with open(file, "r+b") as file_store:
                file_store.seek(block * self.fsparam.block_size)
                file_store.write(record[: self.fsparam.block_size])
        except IOError as e:
            print(e)

    def read_fat(self, file):
        record = [0] * self.fsparam.blocks
        try:
            with open(file, "r+b") as file_store:
                file_store.seek(0)
                for i in range(self.fsparam.blocks):
                    record[i] = struct.unpack("h", file_store.read(2))[0]
        except IOError as e:
            print(e)
        return record

    def write_fat(self, file, fat):
        try:
            with open(file, "r+b") as file_store:
                file_store.seek(0)
                for i in range(self.fsparam.blocks):
                    file_store.write(struct.pack("h", fat[i]))
        except IOError as e:
            print(e)

    def read_dir_entry(self, block, entry):
        bytes_block = self.read_block("filesystem.dat", block)
        offset = entry * self.fsparam.dir_entry_size
        dir_entry = DirEntry()

        dir_entry.filename = bytes_block[offset : offset + 25]
        dir_entry.attributes = bytes_block[offset + 25]
        dir_entry.first_block = struct.unpack(
            "h", bytes_block[offset + 26 : offset + 28]
        )[0]
        dir_entry.size = struct.unpack("i", bytes_block[offset + 28 : offset + 32])[0]

        return dir_entry

    def write_dir_entry(self, block, entry, dir_entry):
        bytes_block = self.read_block("filesystem.dat", block)
        offset = entry * self.fsparam.dir_entry_size

        bytes_block[offset : offset + 25] = dir_entry.filename
        bytes_block[offset + 25] = dir_entry.attributes
        bytes_block[offset + 26 : offset + 28] = struct.pack("h", dir_entry.first_block)
        bytes_block[offset + 28 : offset + 32] = struct.pack("i", dir_entry.size)

        self.write_block("filesystem.dat", block, bytes_block)

    def test_file_system(self):
        for i in range(self.fsparam.fat_blocks):
            self.fat[i] = 0x7FFE
        self.fat[self.fsparam.root_block] = 0x7FFF
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.fat[i] = 0
        self.write_fat("filesystem.dat", self.fat)

        self.data_block = bytearray(self.fsparam.block_size)
        self.write_block("filesystem.dat", self.fsparam.root_block, self.data_block)

        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.write_block("filesystem.dat", i, self.data_block)

        dir_entry = DirEntry()
        name = "file1"
        dir_entry.filename = bytearray(name.encode("utf-8"))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 1111
        dir_entry.size = 222
        self.write_dir_entry(self.fsparam.root_block, 0, dir_entry)

        name = "file2"
        dir_entry.filename = bytearray(name.encode("utf-8"))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 2222
        dir_entry.size = 333
        self.write_dir_entry(self.fsparam.root_block, 1, dir_entry)

        name = "file3"
        dir_entry.filename = bytearray(name.encode("utf-8"))
        dir_entry.attributes = 0x01
        dir_entry.first_block = 3333
        dir_entry.size = 444
        self.write_dir_entry(self.fsparam.root_block, 2, dir_entry)

        for i in range(self.fsparam.dir_entries):
            dir_entry = self.read_dir_entry(self.fsparam.root_block, i)
            print(
                f"Entry {i}, file: {dir_entry.filename.decode('utf-8').strip()} attr: {dir_entry.attributes} first: {dir_entry.first_block} size: {dir_entry.size}"
            )

    def create(self, filename):
        # Leia o diretório raiz
        dir_block = self.read_block("filesystem.dat", self.fsparam.root_block)
        for i in range(self.fsparam.dir_entries):
            offset = i * self.fsparam.dir_entry_size
            if dir_block[offset + 25] == 0x00:  # Entrada vazia
                # Aloca o primeiro bloco para o arquivo
                first_block = self.allocate_block()

                # Cria a nova entrada no diretório
                entry = DirEntry()
                entry.filename = bytearray(filename.ljust(25).encode("utf-8"))
                entry.attributes = 0x01  # Arquivo regular
                entry.first_block = first_block
                entry.size = 0

                # Escreve a entrada no diretório
                self.write_dir_entry(self.fsparam.root_block, i, entry)

                # Salva a FAT atualizada
                self.save_fat()
                return
        raise Exception("O diretório está cheio!")

    def write(self, filename, data):
        entry, entry_idx = self.find_entry(filename)
        if not entry:
            raise Exception(f"Arquivo {filename} não encontrado.")

        # Libera os blocos antigos
        self.release_block(entry.first_block)

        # Divide os dados em blocos de 1024 bytes e grava
        first_block = self.allocate_block()
        entry.first_block = first_block
        entry.size = len(data)
        self.write_data_to_blocks(data, first_block)

        # Atualiza a entrada no diretório
        self.write_dir_entry(self.fsparam.root_block, entry_idx, entry)
        self.save_fat()

    def append(self, filename, data):
        entry, entry_idx = self.find_entry(filename)
        if not entry:
            raise Exception(f"Arquivo {filename} não encontrado.")

        # Encontra o último bloco do arquivo
        last_block = entry.first_block
        while self.fat[last_block] != 0x7FFF:
            last_block = self.fat[last_block]

        # Escreve os dados nos blocos, encadeando na FAT
        self.write_data_to_blocks(data, last_block, append=True)
        entry.size += len(data)

        # Atualiza a entrada no diretório
        self.write_dir_entry(self.fsparam.root_block, entry_idx, entry)
        self.save_fat()

    def read(self, filename):
        entry, _ = self.find_entry(filename)
        if not entry:
            raise Exception(f"Arquivo {filename} não encontrado.")

        # Percorre os blocos na FAT e lê os dados
        data = bytearray()
        block = entry.first_block
        while block != 0x7FFF:
            data += self.read_block("filesystem.dat", block)
            block = self.fat[block]
        return data[: entry.size]

    def unlink(self, filename):
        entry, entry_idx = self.find_entry(filename)
        if not entry:
            raise Exception(f"Arquivo {filename} não encontrado.")

        # Libera os blocos na FAT
        self.release_block(entry.first_block)

        # Remove a entrada no diretório
        entry.attributes = 0x00  # Marca como entrada vazia
        self.write_dir_entry(self.fsparam.root_block, entry_idx, entry)
        self.save_fat()


    def init(self):
        """
        Comando para inicializar o sistema de arquivos.
        """
        print("Inicializando o sistema de arquivos...")
        self.init_file_system()
        print("Sistema de arquivos foi formatado e está pronto para uso.")

# App equivalent
if __name__ == "__main__":
    fs = FileSystem()

    # fs.init_file_system()
    
    while True:
        print("\nComandos disponíveis:")
        print("init - Inicializar o sistema de arquivos")
        print("quit - Sair do programa")

        comando = input("Digite o comando: ").strip().lower()

        if comando == "init":
            fs.init()
        elif comando == "quit":
            print("Saindo do programa...")
            break
        else:
            print("Comando não reconhecido. Tente novamente.")
    

    # Teste criar arquivo
    fs.create("arquivo1")

    # Teste escrever dados
    fs.write("arquivo1", b"Dados para o arquivo 1")

    # Teste ler os dados
    dados = fs.read("arquivo1")
    print("Dados lidos:", dados.decode("utf-8"))

    # Teste adicionar mais dados (append)
    fs.append("arquivo1", b" mais dados")
    dados = fs.read("arquivo1")
    print("Dados após append:", dados.decode("utf-8"))

    # Teste remover o arquivo
    fs.unlink("arquivo1")

