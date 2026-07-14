import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os

# Layout Minimalista
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ComparadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Comparador de Segurados v4.0")
        self.geometry("500x440")
        self.resizable(False, False)
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=15, padx=15, fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="Verificador de Inconsistências", font=("Roboto", 20, "bold"))
        self.lbl_title.pack(pady=(15, 10))
        
        # Seletor de Modo (AP ou EDUC)
        self.modo_var = ctk.StringVar(value="EDUC")
        self.seg_modo = ctk.CTkSegmentedButton(self.main_frame, values=["AP", "EDUC"], variable=self.modo_var, font=("Roboto", 12))
        self.seg_modo.pack(pady=(0, 15))

        # Botões de Arquivo
        self.btn_atual = ctk.CTkButton(self.main_frame, text="📂 1. Planilha Atual", command=self.selecionar_atual, height=35)
        self.btn_atual.pack(pady=(5, 2))
        self.lbl_atual = ctk.CTkLabel(self.main_frame, text="Nenhum arquivo", text_color="gray", font=("Roboto", 11))
        self.lbl_atual.pack(pady=(0, 10))
        
        self.btn_conferido = ctk.CTkButton(self.main_frame, text="📂 2. Planilha a Conferir", command=self.selecionar_conferida, height=35)
        self.btn_conferido.pack(pady=(5, 2))
        self.lbl_conferido = ctk.CTkLabel(self.main_frame, text="Nenhum arquivo", text_color="gray", font=("Roboto", 11))
        self.lbl_conferido.pack(pady=(0, 10))

        # Barra de Progresso
        self.progress = ctk.CTkProgressBar(self.main_frame, width=400, height=10)
        self.progress.pack(pady=15)
        self.progress.set(0)
        
        # Botão Executar
        self.btn_executar = ctk.CTkButton(self.main_frame, text="⚡ Gerar Planilha", command=self.iniciar_thread_verificacao, 
                                          fg_color="#006400", hover_color="#004d00", font=("Roboto", 14, "bold"), height=40)
        self.btn_executar.pack(pady=(0, 10), padx=30, fill="x")

        # Rodapé
        self.lbl_footer = ctk.CTkLabel(self, text="Criado por Matheus Carvalho", font=("Roboto", 10, "italic"), text_color="gray")
        self.lbl_footer.pack(side="bottom", pady=5)
        
        self.arquivo_atual = ""
        self.arquivo_conferido = ""

    def selecionar_atual(self):
        self.arquivo_atual = filedialog.askopenfilename(filetypes=[("Arquivos", "*.txt *.csv *.TXT")])
        if self.arquivo_atual:
            self.lbl_atual.configure(text=os.path.basename(self.arquivo_atual), text_color="white")

    def selecionar_conferida(self):
        self.arquivo_conferido = filedialog.askopenfilename(filetypes=[("Arquivos", "*.txt *.csv *.TXT")])
        if self.arquivo_conferido:
            self.lbl_conferido.configure(text=os.path.basename(self.arquivo_conferido), text_color="white")

    def ler_arquivo(self, caminho):
        try:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
        except UnicodeDecodeError:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def iniciar_thread_verificacao(self):
        if not self.arquivo_atual or not self.arquivo_conferido:
            messagebox.showwarning("Aviso", "Selecione os dois arquivos.")
            return
        
        self.btn_executar.configure(state="disabled", text="Processando...")
        self.progress.set(0)
        threading.Thread(target=self.processar_planilhas).start()

    def processar_planilhas(self):
        try:
            df_atual = self.ler_arquivo(self.arquivo_atual)
            df_conferida = self.ler_arquivo(self.arquivo_conferido)
            
            erros_dict = {}
            total_linhas = len(df_atual)
            modo = self.modo_var.get()
            
            for idx, row in df_atual.iterrows():
                self.progress.set((idx + 1) / total_linhas)
                self.update_idletasks()
                
                nome = str(row.get('NOME DO SEGURADO', '')).strip()
                cpf = str(row.get('CPF', '')).strip()
                nasc = str(row.get('DATA DE NASCIMENTO', '')).strip()
                matricula = str(row.get('MATRICULA', '')).strip()
                certificado = str(row.get('CERTIFICADO', '')).strip()
                
                if not nome:
                    continue
                
                # Lógica de busca de acordo com o modo selecionado
                if modo == "EDUC":
                    match = df_conferida[(df_conferida['NOME DO SEGURADO'].str.strip() == nome) & 
                                         (df_conferida['CPF'].str.strip() == cpf)]
                    cpf_relatorio = cpf
                else: # Modo AP
                    match = df_conferida[df_conferida['NOME DO SEGURADO'].str.strip() == nome]
                    cpf_relatorio = "N/A (Modo AP)"
                
                if match.empty:
                    erros_dict[(nome, cpf_relatorio)] = ["NÃO ENCONTRADO NA PLANILHA CONFERIDA"]
                else:
                    # Pega a primeira ocorrência encontrada
                    row_conf = match.iloc[0]
                    inconsistencias = []
                    
                    if nasc != str(row_conf.get('DATA DE NASCIMENTO', '')).strip():
                        inconsistencias.append(f"NASCIMENTO (Atual: {nasc} -> Conf: {row_conf.get('DATA DE NASCIMENTO')})")
                    
                    if matricula != str(row_conf.get('MATRICULA', '')).strip():
                        inconsistencias.append(f"MATRÍCULA (Atual: {matricula} -> Conf: {row_conf.get('MATRICULA')})")
                        
                    if certificado != str(row_conf.get('CERTIFICADO', '')).strip():
                        inconsistencias.append(f"CERTIFICADO (Atual: {certificado} -> Conf: {row_conf.get('CERTIFICADO')})")
                        
                    if inconsistencias:
                        erros_dict[(nome, cpf_relatorio)] = inconsistencias

            self.gerar_planilha(erros_dict)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar:\n{str(e)}")
        finally:
            self.btn_executar.configure(state="normal", text="⚡ Gerar Planilha")
            self.progress.set(1)

    def gerar_planilha(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhum erro encontrado!")
            return

        planilha_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Planilha do Excel", "*.xlsx"), ("Arquivo CSV", "*.csv")], 
            initialfile="Inconsistencias.xlsx"
        )
        
        if not planilha_path:
            return
        
        try:
            dados_planilha = []
            for (nome, cpf_relatorio), lista_erros in erros_dict.items():
                linha = {"Nome do Segurado": nome, "CPF": cpf_relatorio}
                for i, erro in enumerate(lista_erros):
                    linha[f"Erro {i+1}"] = erro
                dados_planilha.append(linha)
                
            df_relatorio = pd.DataFrame(dados_planilha)
            
            if planilha_path.endswith('.csv'):
                df_relatorio.to_csv(planilha_path, index=False, sep=';', encoding='utf-8-sig')
            else:
                df_relatorio.to_excel(planilha_path, index=False)
                
            messagebox.showinfo("Sucesso", "Planilha salva com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

if __name__ == "__main__":
    app = ComparadorApp()
    app.mainloop()
