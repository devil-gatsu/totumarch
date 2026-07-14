import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os

# Novo layout moderno e estruturado
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ComparadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Comparador de Segurados v2.0")
        self.geometry("750x550")
        self.resizable(False, False)
        
        # Container principal com bordas arredondadas
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="🔍 Verificador de Inconsistências", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=(20, 20))
        
        # Área de seleção de arquivos (Frame interno)
        self.frame_files = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_files.pack(pady=10, fill="x", padx=20)
        
        self.btn_atual = ctk.CTkButton(self.frame_files, text="📂 1. Planilha Atual", command=self.selecionar_atual, width=200, height=45, font=("Roboto", 14, "bold"))
        self.btn_atual.grid(row=0, column=0, padx=10, pady=15)
        self.lbl_atual = ctk.CTkLabel(self.frame_files, text="Nenhum arquivo...", text_color="gray", width=350, anchor="w", font=("Roboto", 12))
        self.lbl_atual.grid(row=0, column=1, padx=10, pady=15)
        
        self.btn_conferido = ctk.CTkButton(self.frame_files, text="📂 2. Planilha a Conferir", command=self.selecionar_conferida, width=200, height=45, font=("Roboto", 14, "bold"))
        self.btn_conferido.grid(row=1, column=0, padx=10, pady=15)
        self.lbl_conferido = ctk.CTkLabel(self.frame_files, text="Nenhum arquivo...", text_color="gray", width=350, anchor="w", font=("Roboto", 12))
        self.lbl_conferido.grid(row=1, column=1, padx=10, pady=15)

        # Barra de Progresso
        self.progress = ctk.CTkProgressBar(self.main_frame, width=550, height=15)
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        # Botão Executar
        self.btn_executar = ctk.CTkButton(self.main_frame, text="⚡ Verificar e Gerar Relatório (.txt)", command=self.iniciar_thread_verificacao, 
                                          fg_color="#006400", hover_color="#004d00", font=("Roboto", 16, "bold"), height=50)
        self.btn_executar.pack(pady=10, padx=20, fill="x")

        # Rodapé
        self.lbl_footer = ctk.CTkLabel(self, text="Criado por Matheus Carvalho", font=("Roboto", 12, "italic"), text_color="gray")
        self.lbl_footer.pack(side="bottom", pady=10)
        
        self.arquivo_atual = ""
        self.arquivo_conferido = ""

    def selecionar_atual(self):
        self.arquivo_atual = filedialog.askopenfilename(filetypes=[("Arquivos de Texto e CSV", "*.txt *.csv *.TXT")])
        if self.arquivo_atual:
            self.lbl_atual.configure(text=os.path.basename(self.arquivo_atual), text_color="white")

    def selecionar_conferida(self):
        self.arquivo_conferido = filedialog.askopenfilename(filetypes=[("Arquivos de Texto e CSV", "*.txt *.csv *.TXT")])
        if self.arquivo_conferido:
            self.lbl_conferido.configure(text=os.path.basename(self.arquivo_conferido), text_color="white")

    def ler_arquivo(self, caminho):
        try:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
        except UnicodeDecodeError:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def iniciar_thread_verificacao(self):
        if not self.arquivo_atual or not self.arquivo_conferido:
            messagebox.showwarning("Aviso", "Por favor, selecione os dois arquivos antes de continuar.")
            return
        
        self.btn_executar.configure(state="disabled", text="Processando...")
        self.progress.set(0)
        threading.Thread(target=self.processar_planilhas).start()

    def processar_planilhas(self):
        try:
            df_atual = self.ler_arquivo(self.arquivo_atual)
            df_conferida = self.ler_arquivo(self.arquivo_conferido)
            
            # Dicionário para agrupar erros da mesma pessoa
            erros_dict = {}
            total_linhas = len(df_atual)
            
            for idx, row in df_atual.iterrows():
                self.progress.set((idx + 1) / total_linhas)
                self.update_idletasks()
                
                nome = str(row.get('NOME DO SEGURADO', '')).strip()
                cpf = str(row.get('CPF', '')).strip()
                nasc = str(row.get('DATA DE NASCIMENTO', '')).strip()
                matricula = str(row.get('MATRICULA', '')).strip()
                certificado = str(row.get('CERTIFICADO', '')).strip()
                
                if not nome and not cpf:
                    continue
                
                match = df_conferida[(df_conferida['NOME DO SEGURADO'].str.strip() == nome) & 
                                     (df_conferida['CPF'].str.strip() == cpf)]
                
                if match.empty:
                    erros_dict[(nome, cpf)] = ["NÃO ENCONTRADO NA PLANILHA CONFERIDA"]
                else:
                    row_conf = match.iloc[0]
                    inconsistencias = []
                    
                    if nasc != str(row_conf.get('DATA DE NASCIMENTO', '')).strip():
                        inconsistencias.append(f"NASCIMENTO (Atual: {nasc} -> Conf: {row_conf.get('DATA DE NASCIMENTO')})")
                    
                    if matricula != str(row_conf.get('MATRICULA', '')).strip():
                        inconsistencias.append(f"MATRÍCULA (Atual: {matricula} -> Conf: {row_conf.get('MATRICULA')})")
                        
                    if certificado != str(row_conf.get('CERTIFICADO', '')).strip():
                        inconsistencias.append(f"CERTIFICADO (Atual: {certificado} -> Conf: {row_conf.get('CERTIFICADO')})")
                        
                    # Se encontrou alguma inconsistência, salva na chave da pessoa
                    if inconsistencias:
                        erros_dict[(nome, cpf)] = inconsistencias

            self.gerar_txt(erros_dict)
            
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro ao ler os arquivos:\n{str(e)}")
        finally:
            self.btn_executar.configure(state="normal", text="⚡ Verificar e Gerar Relatório (.txt)")
            self.progress.set(1)

    def gerar_txt(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhum erro encontrado! Os arquivos batem perfeitamente.")
            return

        txt_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de Texto", "*.txt")], initialfile="Inconsistencias.txt")
        if not txt_path:
            return
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Total de segurados com divergências: {len(erros_dict)}\n")
                f.write("="*100 + "\n\n")
                
                # Escreve os dados formatados em uma única linha por segurado
                for (nome, cpf), lista_erros in erros_dict.items():
                    detalhes = " | ".join(lista_erros)
                    f.write(f"{nome};{cpf};{detalhes}\n")
                    
            messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso em:\n{txt_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

if __name__ == "__main__":
    app = ComparadorApp()
    app.mainloop()
