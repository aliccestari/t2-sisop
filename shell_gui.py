import tkinter as tk
from tkinter import scrolledtext


class FileSystemShellGUI:
    def __init__(self, fs):
        self.fs = fs
        self.window = tk.Tk()
        self.window.title("Simulador de Shell - Sistema de Arquivos")

        # Configurações de estilo
        self.window.configure(bg="black")

        # Configuração do grid
        self.window.rowconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=0)
        self.window.rowconfigure(2, weight=0)
        self.window.columnconfigure(0, weight=1)

        self.output_area = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            bg="black",
            fg="white",
            font=("Courier", 12),
        )
        self.output_area.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.output_area.insert(tk.END, "Bem-vindo ao Shell do Sistema de Arquivos!\n")
        self.output_area.insert(
            tk.END, "Digite 'help' para ver os commands disponíveis.\n\n"
        )
        self.output_area.configure(state="disabled")

        self.command_entry = tk.Entry(
            self.window,
            bg="black",
            fg="white",
            insertbackground="white",
            font=("Courier", 12),
        )
        self.command_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.command_entry.bind("<Return>", self.execute_command)

    def log_output(self, message):
        """Adiciona mensagens na área de saída."""
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.see(tk.END)
        self.output_area.configure(state="disabled")

    def execute_command(self, event):
        """Executa o command inserido pelo usuário."""
        command = self.command_entry.get().strip()
        if not command:
            return

        self.log_output(f"> {command}")

        try:
            if command == "help":
                self.log_output("commands disponíveis:")
                self.log_output("init - Inicializar o sistema de arquivos")
                self.log_output("load - Carregar o sistema de arquivos")
                self.log_output("mkdir /[nome_dir] - Criar diretório")
                self.log_output("ls - Listar conteúdo do diretório raiz")
                self.log_output("create /[nome_dir][nome_arq] - Criar arquivo")
                self.log_output(
                    "write /[nome_dir]/[nome_arq] [dados] - Escrever dados em um arquivo"
                )
                self.log_output(
                    "append /[nome_dir]/[nome_arq] [dados] - Adicionar dados ao final de um arquivo"
                )
                self.log_output(
                    "read /[nome_dir]/[nome_arq] - Ler conteúdo de um arquivo"
                )
                self.log_output("unlink [caminho] - Remover um arquivo")
                self.log_output("quit - Sair do programa")
            elif command == "init":
                self.fs.init()
                self.log_output("Sistema de arquivos inicializado com sucesso!")
            elif command == "load":
                self.fs.load_file_system()
                self.log_output("Sistema de arquivos carregado com sucesso!")
            elif command.startswith("mkdir"):
                args = command.split(" ", 1)
                if len(args) > 1 and args[1].strip():
                    self.fs.mkdir(args[1].strip())
                    self.log_output(
                        f"Diretório '{args[1].strip()}' criado com sucesso!"
                    )
                else:
                    self.log_output("Erro: Nome do diretório não fornecido.")
            elif command == "ls":
                try:
                    self.log_output("Conteúdo do diretório raiz:")
                    entries = self.fs.ls()
                    for entry in entries:
                        self.log_output(entry)
                except Exception as e:
                    self.log_output(f"Erro ao listar conteúdo do diretório: {str(e)}")
            elif command.startswith("create"):
                args = command.split(" ", 2)
                if len(args) > 2 and args[1].strip() and args[2].strip():
                    directory = args[1].strip()
                    filename = args[2].strip()
                    try:
                        self.fs.create(directory, filename)
                        self.log_output(
                            f"Arquivo '{filename}' criado no diretório '{directory}' com sucesso!"
                        )
                    except Exception as e:
                        self.log_output(f"Erro ao criar arquivo: {str(e)}")
                else:
                    self.log_output(
                        "Erro: Caminho do diretório ou nome do arquivo não fornecidos."
                    )
            elif command.startswith("write"):
                args = command.split(" ", 2)
                if len(args) > 2:
                    try:
                        self.fs.write(args[1].strip(), args[2].encode("utf-8"))
                        self.log_output(
                            f"Dados escritos no arquivo '{args[1].strip()}' com sucesso!"
                        )
                    except Exception as e:
                        self.log_output(f"Erro: {str(e)}")
                else:
                    self.log_output("Erro: Caminho do arquivo ou dados não fornecidos.")

            elif command.startswith("read"):
                args = command.split(" ", 1)
                if len(args) > 1 and args[1].strip():
                    try:
                        content = self.fs.read(args[1].strip())
                        # Decodificar o conteúdo se for um bytearray
                        decoded_content = (
                            content.decode("utf-8")
                            if isinstance(content, (bytes, bytearray))
                            else content
                        )
                        self.log_output(
                            f"Conteúdo do arquivo '{args[1].strip()}': {decoded_content}"
                        )
                    except Exception as e:
                        self.log_output(f"Erro: {str(e)}")
                else:
                    self.log_output("Erro: Caminho do arquivo não fornecido.")

            elif command.startswith("append"):
                args = command.split(" ", 2)
                if len(args) > 2:
                    try:
                        self.fs.append(args[1].strip(), args[2].encode("utf-8"))
                        self.log_output(
                            f"Dados adicionados ao arquivo '{args[1].strip()}' com sucesso!"
                        )
                    except Exception as e:
                        self.log_output(f"Erro: {str(e)}")
                else:
                    self.log_output("Erro: Caminho do arquivo ou dados não fornecidos.")

            elif command.startswith("unlink"):
                args = command.split(" ", 1)
                if len(args) > 1 and args[1].strip():
                    self.fs.unlink(args[1].strip())
                    self.log_output(
                        f"Arquivo '{args[1].strip()}' removido com sucesso!"
                    )
                else:
                    self.log_output("Erro: Nome do arquivo não fornecido.")
            elif command == "debug_fat":
                fs.debug_fat()
            elif command == "quit":
                self.log_output("Saindo do programa...")
                self.window.quit()
            else:
                self.log_output(
                    "command não reconhecido. Digite 'help' para ver os commands disponíveis."
                )
        except Exception as e:
            self.log_output(f"Erro: {str(e)}")

        # Limpa o campo de entrada
        self.command_entry.delete(0, tk.END)

    def run(self):
        """Executa a interface gráfica."""
        self.window.mainloop()


if __name__ == "__main__":
    from filesystem import FileSystem

    fs = FileSystem()
    shell_gui = FileSystemShellGUI(fs)
    shell_gui.run()
