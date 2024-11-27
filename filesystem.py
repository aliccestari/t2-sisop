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

        if not os.path.exists("filesystem.dat"):
            with open("filesystem.dat", "wb") as f:
                f.write(bytearray(self.fsparam.blocks * self.fsparam.block_size))

    def load_file_system(self):
        self.fat = self.read_fat("filesystem.dat")

    def init_file_system(self):
        for i in range(self.fsparam.fat_blocks):
            self.fat[i] = 0x7FFE
        self.fat[self.fsparam.root_block] = 0x7FFF
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.fat[i] = 0x0000
        self.write_fat("filesystem.dat", self.fat)
        self.init_root_and_data_blocks()

    def init_root_and_data_blocks(self):
        root_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.dir_entries):
            offset = i * self.fsparam.dir_entry_size
            root_block[offset : offset + self.fsparam.dir_entry_size] = bytearray(
                self.fsparam.dir_entry_size
            )
        self.write_block("filesystem.dat", self.fsparam.root_block, root_block)
        empty_block = bytearray(self.fsparam.block_size)
        for i in range(self.fsparam.root_block + 1, self.fsparam.blocks):
            self.write_block("filesystem.dat", i, empty_block)

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
        self.write_fat("filesystem.dat", self.fat)
        return block

    def free_block(self, block):
        while block != 0x7FFF:
            next_block = self.fat[block]
            self.fat[block] = 0x0000
            block = next_block
        self.write_fat("filesystem.dat", self.fat)

    def mkdir(self, path):
        try:
            if len(path.split("/")[-1]) > 25:
                print("Erro: Nome do diretório excede o limite de 25 caracteres.")
                return

            path_parts = path.strip("/").split("/")
            subdir_name = path_parts[-1]
            parent_path = "/".join(path_parts[:-1])

            parent_block = (
                self.root_block
                if not parent_path
                else self.find_directory(parent_path, self.fsparam.root_block)
            )

            if parent_block is None:
                print(f"Erro: O diretório pai '{parent_path}' não foi encontrado.")
                return

            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(parent_block, i)
                dir_name = entry.filename.decode("utf-8").strip()
                if dir_name == subdir_name and entry.attributes == 0x02:
                    print(
                        f"Erro: O diretório '{subdir_name}' já existe no diretório '{parent_path}'."
                    )
                    return

            new_block = self.allocate_block()
            if new_block == -1:
                print("Erro: Não há blocos livres disponíveis para criar o diretório.")
                return

            dir_entry = DirEntry()
            dir_entry.filename = bytearray(subdir_name.encode("utf-8")[:25])
            dir_entry.attributes = 0x02
            dir_entry.first_block = new_block
            dir_entry.size = self.fsparam.block_size

            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(parent_block, i)
                if entry.attributes == 0x00:
                    self.write_dir_entry(parent_block, i, dir_entry)
                    print(
                        f"Subdiretório '{subdir_name}' criado com sucesso no diretório '{parent_path}'!"
                    )
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
                dir_name = entry.filename.decode("utf-8").rstrip("\x00").strip()

                if dir_name == part and entry.attributes == 0x02:
                    current_block = entry.first_block
                    found = True
                    break

            if not found:
                print(
                    f"Erro: O diretório '{part}' não foi encontrado no bloco {current_block}."
                )
                return None

        return current_block

    def ls(self, block=None, indent_level=0):
        if block is None:
            block = self.root_block

        result = []  # Lista para armazenar os resultados

        try:
            for i in range(self.fsparam.dir_entries):
                entry = self.read_dir_entry(block, i)
                dir_name = entry.filename.decode("utf-8").strip()

                if entry.attributes != 0x00:  # Verifica se é uma entrada válida
                    entry_type = "DIR" if entry.attributes == 0x02 else "FILE"
                    result.append(f"{'  ' * indent_level}- {dir_name} ({entry_type})")

                    # Se for um diretório, lista recursivamente
                    if entry.attributes == 0x02:
                        result.extend(self.ls(entry.first_block, indent_level + 1))

        except Exception as e:
            result.append(f"Erro ao tentar listar o diretório: {str(e)}")

        return result

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

    def find_entry(self, filename, parent_block=None):
        if parent_block is None:
            parent_block = self.fsparam.root_block

        for i in range(self.fsparam.dir_entries):
            entry = self.read_dir_entry(parent_block, i)
            entry_name = entry.filename.decode("utf-8").rstrip("\x00").strip()

            if entry_name == filename and entry.attributes != 0x00:
                return entry, i

        return None, -1  # Se não encontrar a entrada

    def write_dir_entry(self, block, entry, dir_entry):
        bytes_block = self.read_block("filesystem.dat", block)
        offset = entry * self.fsparam.dir_entry_size

        bytes_block[offset : offset + 25] = dir_entry.filename
        bytes_block[offset + 25] = dir_entry.attributes
        bytes_block[offset + 26 : offset + 28] = struct.pack("h", dir_entry.first_block)
        bytes_block[offset + 28 : offset + 32] = struct.pack("i", dir_entry.size)

        self.write_block("filesystem.dat", block, bytes_block)

    def write_data_to_blocks(self, data, start_block):
        """Escreve os dados nos blocos encadeados da FAT."""
        block_size = self.fsparam.block_size
        current_block = start_block
        offset = 0

        while offset < len(data):
            # Divide os dados em pedaços de até 1024 bytes (tamanho do bloco)
            chunk = data[offset : offset + block_size]
            offset += block_size

            # Prepara o bloco para escrita
            data_block = bytearray(block_size)
            data_block[: len(chunk)] = chunk

            # Escreve os dados no bloco atual
            self.write_block("filesystem.dat", current_block, data_block)

            # Se ainda há dados para escrever, aloca o próximo bloco
            if offset < len(data):
                next_block = self.allocate_block(current_block)  # Aloca o próximo bloco
                current_block = next_block
            else:
                # Último bloco - marca como o final na FAT
                self.fat[current_block] = 0x7FFF

        # Atualiza a FAT no arquivo
        self.write_fat("filesystem.dat", self.fat)

    def create(self, directory, filename):
        parent_block = (
            self.fsparam.root_block
            if directory == "/"
            else self.find_directory(directory, self.fsparam.root_block)
        )

        if parent_block is None:
            raise Exception(f"Diretório '{directory}' não encontrado.")

        # Leia o diretório
        dir_block = self.read_block("filesystem.dat", parent_block)
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
                self.write_dir_entry(parent_block, i, entry)

                # Atualiza a FAT
                self.write_fat("filesystem.dat", self.fat)
                return
        raise Exception("O diretório está cheio!")

    def write(self, filepath, data):
        path_parts = filepath.strip("/").split("/")
        filename = path_parts[-1]
        parent_path = "/".join(path_parts[:-1])

        parent_block = (
            self.fsparam.root_block
            if not parent_path
            else self.find_directory(parent_path, self.fsparam.root_block)
        )

        if parent_block is None:
            raise Exception(f"Diretório '{parent_path}' não encontrado.")

        entry, entry_idx = self.find_entry(filename, parent_block)
        if not entry:
            raise Exception(
                f"Arquivo '{filename}' não encontrado no diretório '{parent_path}'."
            )

        # Libera os blocos antigos
        self.free_block(entry.first_block)

        # Divide os dados em blocos de 1024 bytes e grava
        first_block = self.allocate_block()
        entry.first_block = first_block
        entry.size = len(data)
        self.write_data_to_blocks(data, first_block)

        # Atualiza a entrada no diretório
        self.write_dir_entry(parent_block, entry_idx, entry)
        self.write_fat("filesystem.dat", self.fat)
        print(f"Dados escritos no arquivo '{filename}' com sucesso!")

    def read(self, filepath):
        path_parts = filepath.strip("/").split("/")
        filename = path_parts[-1]
        parent_path = "/".join(path_parts[:-1])

        parent_block = (
            self.fsparam.root_block
            if not parent_path
            else self.find_directory(parent_path, self.fsparam.root_block)
        )

        if parent_block is None:
            raise Exception(f"Diretório '{parent_path}' não encontrado.")

        entry, _ = self.find_entry(filename, parent_block)
        if not entry:
            raise Exception(
                f"Arquivo '{filename}' não encontrado no diretório '{parent_path}'."
            )

        # Percorra os blocos encadeados na FAT e leia os dados
        data = bytearray()
        block = entry.first_block
        while block != 0x7FFF:  # 0x7FFF indica o fim do arquivo
            data += self.read_block("filesystem.dat", block)
            block = self.fat[block]

        # Retorna apenas os dados do tamanho correto
        print(f"Conteúdo do arquivo '{filepath}': {data[:entry.size].decode('utf-8')}")
        return data[: entry.size]

    def append(self, filepath, data):
        path_parts = filepath.strip("/").split("/")
        filename = path_parts[-1]
        parent_path = "/".join(path_parts[:-1])

        parent_block = (
            self.fsparam.root_block
            if not parent_path
            else self.find_directory(parent_path, self.fsparam.root_block)
        )

        if parent_block is None:
            raise Exception(f"Diretório '{parent_path}' não encontrado.")

        entry, entry_idx = self.find_entry(filename, parent_block)
        if not entry:
            raise Exception(
                f"Arquivo '{filename}' não encontrado no diretório '{parent_path}'."
            )

        # Encontra o último bloco do arquivo
        last_block = entry.first_block
        while self.fat[last_block] != 0x7FFF:
            last_block = self.fat[last_block]

        # Verifica espaço restante no último bloco
        last_data = self.read_block("filesystem.dat", last_block)
        last_data_len = len(last_data.rstrip(b"\x00"))
        remaining_space = self.fsparam.block_size - last_data_len

        offset = 0
        if remaining_space > 0:
            # Adiciona dados ao último bloco se houver espaço
            chunk = data[:remaining_space]
            last_data[last_data_len : last_data_len + len(chunk)] = chunk
            self.write_block("filesystem.dat", last_block, last_data)
            offset += remaining_space

        # Encadeia novos blocos com os dados restantes
        block_size = self.fsparam.block_size
        while offset < len(data):
            chunk = data[offset : offset + block_size]
            offset += block_size

            # Aloca um novo bloco
            new_block = self.find_free_block()
            self.fat[last_block] = new_block
            self.fat[new_block] = 0x7FFF
            self.write_block("filesystem.dat", new_block, chunk)

            # Atualiza o último bloco
            last_block = new_block

        # Atualiza o tamanho do arquivo na entrada do diretório
        entry.size += len(data)
        self.write_dir_entry(parent_block, entry_idx, entry)
        self.write_fat("filesystem.dat", self.fat)
        print(f"Dados adicionados ao arquivo '{filename}' com sucesso!")

    def unlink(self, path):
        path_parts = path.strip("/").split("/")
        filename = path_parts[-1]
        parent_path = "/".join(path_parts[:-1])

        # Encontre o bloco do diretório pai
        parent_block = (
            self.fsparam.root_block
            if not parent_path
            else self.find_directory(parent_path, self.fsparam.root_block)
        )
        if parent_block is None:
            raise Exception(f"O diretório '{parent_path}' não foi encontrado.")

        # Procure o arquivo no diretório pai
        entry, entry_idx = self.find_entry(filename, parent_block)
        if not entry:
            raise Exception(f"Arquivo ou diretório '{filename}' não encontrado.")

        # Verifique se é um diretório e está vazio
        if entry.attributes == 0x02:  # Diretório
            for i in range(self.fsparam.dir_entries):
                sub_entry = self.read_dir_entry(entry.first_block, i)
                if sub_entry.attributes != 0x00:
                    raise Exception(
                        f"O diretório '{filename}' não está vazio. Remova o conteúdo primeiro."
                    )

        # Libere os blocos associados ao arquivo ou diretório
        self.free_block(entry.first_block)

        # Remova a entrada no diretório
        entry.attributes = 0x00  # Marca como entrada vazia
        self.write_dir_entry(parent_block, entry_idx, entry)
        self.write_fat("filesystem.dat", self.fat)
        print(f"Arquivo ou diretório '{filename}' removido com sucesso!")

    def debug_fat(self):
        """Exibe o encadeamento da FAT para depuração."""
        print("Encadeamento da FAT:")
        for i, value in enumerate(self.fat):
            if value != 0x0000:  # Mostra apenas blocos alocados
                print(f"Bloco {i}: {value}")

    def debug_entry(self, filename):
        entry, _ = self.find_entry(filename)
        if entry:
            print(
                f"Nome: {entry.filename.decode('utf-8').strip()}, Atributo: {entry.attributes}"
            )
        else:
            print(f"Entrada '{filename}' não encontrada.")

    def init(self):
        self.init_file_system()


if __name__ == "__main__":
    fs = FileSystem()

    while True:
        print("\nComandos disponíveis:")
        print("init - Inicializar o sistema de arquivos")
        print("load - Carregar o sistema de arquivos")
        print("mkdir [nome_dir] - Criar diretório")
        print("ls - Listar conteúdo do diretório raiz")
        print("create [nome] - Criar arquivo")
        print("write [nome] [dados] - Escrever dados em um arquivo")
        print("append [nome] [dados] - Adicionar dados ao final de um arquivo")
        print("read [nome] - Ler conteúdo de um arquivo")
        print("unlink [nome] - Remover um arquivo")
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
        elif comando.startswith("create"):
            args = comando.split(" ", 1)
            if len(args) > 1 and args[1].strip():
                fs.create(args[1].strip())
            else:
                print("Erro: Nome do arquivo não fornecido.")
        elif comando.startswith("write"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                fs.write(args[1].strip(), args[2].encode("utf-8"))
            else:
                print("Erro: Nome do arquivo ou dados não fornecidos.")
        elif comando.startswith("append"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                fs.append(args[1].strip(), args[2].encode("utf-8"))
            else:
                print("Erro: Nome do arquivo ou dados não fornecidos.")
        elif comando.startswith("read"):
            args = comando.split(" ", 1)
            if len(args) > 1 and args[1].strip():
                fs.read(args[1].strip())
            else:
                print("Erro: Nome do arquivo não fornecido.")
        elif comando.startswith("unlink"):
            args = comando.split(" ", 1)
            if len(args) > 1 and args[1].strip():
                fs.unlink(args[1].strip())
            else:
                print("Erro: Nome do arquivo não fornecido.")
        elif comando == "debug_fat":
            fs.debug_fat()
        elif comando.startswith("debug_entry"):
            args = comando.split(" ", 1)
            if len(args) > 1 and args[1].strip():
                fs.debug_entry(args[1].strip())
            else:
                print("Erro: Nome da entrada não fornecido.")
        elif comando == "quit":
            print("Saindo do programa...")
            break
        else:
            print("Comando não reconhecido. Tente novamente.")
